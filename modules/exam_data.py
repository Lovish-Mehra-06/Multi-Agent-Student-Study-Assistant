"""
modules/exam_data.py

Purpose:
    Process CBSE sample papers and marking schemes into a structured,
    evidence-accurate exam_database.json.

Design goals (rewrite):
    - 100% deterministic / rule-based. No LLM calls anywhere in this file.
    - Layout-aware PDF parsing: CBSE papers use a fixed 3-column table
      (Q.No | Question/Answer | Marks). Reading plain concatenated text
      (as the old implementation did) interleaves the Marks column into
      the question/answer body and is the root cause of misaligned and
      corrupted extractions. Here we use word bounding boxes to keep the
      three columns separate.
    - Questions and answers are matched by question_no via a dict merge,
      not by list position/zip, so a missing/extra item on either side
      can't silently shift every subsequent answer.

Flow:
    Question Paper PDF ---layout-aware parse---> {question_no: {...}}
    Marking Scheme PDF ---layout-aware parse---> {question_no: {...}}
                              |
                              v
                    dict merge on question_no
                              |
                              v
              rule-based section / type / marks /
              subpart / chapter / concept tagging
                              |
                              v
                    exam_database.json

Used by:
    agents/exam_analysis_agent.py
"""

import os
import re
import json
from collections import defaultdict

import fitz  # PyMuPDF

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXAM_DATABASE_PATH = os.path.join(BASE_DIR, "data", "exam_database.json")


# =====================================================
# LOW-LEVEL LAYOUT EXTRACTION
# =====================================================
#
# fitz.Page.get_text("words") returns (x0, y0, x1, y1, word, block_no,
# line_no, word_no). Grouping by (block_no, line_no) reconstructs the
# PDF's own visual lines (as laid out), which is far more reliable than
# re-splitting a flattened text blob. Each visual line also carries an
# x0 (left edge), which tells us which of the paper's three columns
# (Q.No / Content / Marks) it belongs to.


def _extract_raw_lines(pdf_path: str):
    """
    Returns an ordered list of line dicts: {page, x0, y0, text, ntok}.

    Uses get_text("dict") and preserves PyMuPDF's own block/line paint
    order (the same order "words"/"text" mode agree on for these
    documents). Critically, we do NOT re-sort lines by raw y0 -- doing so
    breaks logical reading order whenever line baselines are close
    together (e.g. a Marks-column entry and the next Q.No-column entry
    sitting at nearly the same height), which was found to occasionally
    swap a question's trailing content with the next question's opening
    line.
    """

    document = fitz.open(pdf_path)
    all_lines = []

    for page_no, page in enumerate(document):

        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if not text:
                    continue
                x0 = line["bbox"][0]
                y0 = line["bbox"][1]
                ntok = len(text.split())
                all_lines.append(
                    {
                        "page": page_no + 1,
                        "x0": x0,
                        "y0": y0,
                        "text": text,
                        "ntok": ntok,
                    }
                )

    document.close()
    return all_lines


_NUM_LINE_RE = re.compile(r"^(\d{1,2})\.?$")


def _find_marks_column_threshold(lines):
    """
    Every CBSE Q.No/Marks column entry is a *lone* number on its own
    visual line. The Q.No column sits near the left margin, the Marks
    column sits near the right margin -- these two clusters of x0
    values are always separated by a large gap (empirically 300-450pt
    on a 612pt-wide page). Finding that gap gives us a deterministic,
    layout-derived threshold without hardcoding pixel coordinates,
    so this also adapts to slightly different CBSE templates/years.
    """

    xs = sorted(
        {
            round(line["x0"], 1)
            for line in lines
            if line["ntok"] == 1 and _NUM_LINE_RE.match(line["text"])
        }
    )

    if len(xs) < 2:
        return None

    gaps = [(xs[i + 1] - xs[i], xs[i], xs[i + 1]) for i in range(len(xs) - 1)]
    gaps.sort(reverse=True)
    biggest_gap, lo, hi = gaps[0]

    if biggest_gap < 100:
        # No clean bimodal split found; caller should fall back.
        return None

    return (lo + hi) / 2


SECTION_HEADER_RE = re.compile(r"^SECTION\s*[-–—]\s*([A-E])\b", re.IGNORECASE)


def _parse_columned_pdf(pdf_path: str, is_marking_scheme: bool, max_question_no: int = 60):
    """
    Shared parser for both the Question Paper and the Marking Scheme,
    since both use the same Q.No | Content | Marks table layout.

    Returns:
        items: {question_no: {"text": str, "marks": int|None,
                               "section": "A".."E"|None}}
        max_question_no: int
    """

    lines = _extract_raw_lines(pdf_path)
    marks_threshold = _find_marks_column_threshold(lines)

    items = {}
    current_no = None
    current_lines = []
    current_section = None
    expected_no = 1
    max_seen = 0

    def flush():
        nonlocal current_no, current_lines
        if current_no is not None:
            text = _clean_text(" ".join(current_lines))
            items[current_no]["text"] = text
        current_lines = []

    for line in lines:

        text = line["text"]
        if not text:
            continue

        # ---- Section headers (deterministic section boundary markers) ----
        section_match = SECTION_HEADER_RE.match(text)
        if section_match:
            current_section = section_match.group(1).upper()
            continue

        # ---- Table header row noise ("Q. No", "Questions", "Marks") ----
        if text in ("Q. No", "Q.No", "Questions", "Marks", "Answer", "Answers"):
            continue

        is_lone_number = line["ntok"] == 1 and _NUM_LINE_RE.match(text)

        # ---- Marks column (right-hand side lone numbers) ----
        if (
            is_lone_number
            and marks_threshold is not None
            and line["x0"] > marks_threshold
        ):
            if current_no is not None:
                try:
                    items[current_no]["marks"] = int(text.rstrip("."))
                except ValueError:
                    pass
            continue

        # ---- Question/Answer number column (left-hand side) ----
        if is_lone_number and (
            marks_threshold is None or line["x0"] <= marks_threshold
        ):
            number = int(text.rstrip("."))

            # Normally requires an exact sequential match. A small forward
            # tolerance (allow skipping up to a few numbers) keeps one
            # missed/garbled entry from permanently desyncing every
            # question after it, while still rejecting numbers that are
            # far off (which are almost certainly not a real Q.No cell).
            in_tolerance = expected_no <= number <= expected_no + 4

            if in_tolerance and number <= max_question_no and number not in items:
                flush()
                current_no = number
                current_lines = []
                items[current_no] = {
                    "text": "",
                    "marks": None,
                    "section": current_section,
                }
                expected_no = number + 1
                max_seen = max(max_seen, number)
                continue
            # A lone number that doesn't match the expected sequence is
            # very unlikely to be a real question/answer index (it may be
            # a stray figure label etc.) -- treat as ordinary content.

        # ---- Ordinary content line ----
        if current_no is not None:
            current_lines.append(text)

    flush()

    return items, max_seen


def _clean_text(text: str) -> str:
    text = text.replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =====================================================
# QUESTION PAPER / MARKING SCHEME PARSERS (public wrappers)
# =====================================================


def extract_questions(pdf_path: str):
    """Returns {question_no: {"question": str, "marks": int|None, "section": str|None}}"""
    raw, _ = _parse_columned_pdf(pdf_path, is_marking_scheme=False)
    return {
        no: {"question": v["text"], "marks": v["marks"], "section": v["section"]}
        for no, v in raw.items()
    }


def extract_answers(pdf_path: str):
    """Returns {question_no: {"answer": str, "marks": int|None, "section": str|None}}"""
    raw, _ = _parse_columned_pdf(pdf_path, is_marking_scheme=True)
    return {
        no: {"answer": v["text"], "marks": v["marks"], "section": v["section"]}
        for no, v in raw.items()
    }


# =====================================================
# RULE-BASED QUESTION TYPE / SUBPART / SECTION TAGGING
# =====================================================

ASSERTION_REASON_RE = re.compile(r"\bAssertion\s*:.*\bReason\s*:", re.IGNORECASE | re.DOTALL)
SUBPART_RE = re.compile(r"\(([a-e]|i{1,3}|iv|v|vi{0,3})\)", re.IGNORECASE)
OR_CHOICE_RE = re.compile(r"(?:^|\s)OR(?:\s|$)")

# Section -> default (question_type, expected_marks). Used as a fallback
# whenever the section itself couldn't be determined for a question.
SECTION_DEFAULTS = {
    "A": ("MCQ", 1),
    "B": ("Very Short Answer", 2),
    "C": ("Short Answer", 3),
    "D": ("Long Answer", 5),
    "E": ("Case-Based/Source-Based", 4),
}


def classify_question_type(question_text: str, section: str):

    if ASSERTION_REASON_RE.search(question_text):
        return "Assertion-Reason"

    if section and section in SECTION_DEFAULTS:
        return SECTION_DEFAULTS[section][0]

    return "Unknown"


def extract_subparts(text: str):
    labels = []
    for match in SUBPART_RE.finditer(text):
        label = match.group(1).lower()
        if label not in labels:
            labels.append(label)
    return labels


def has_internal_choice(text: str) -> bool:
    return bool(OR_CHOICE_RE.search(text))


# =====================================================
# CHAPTER / CONCEPT CLASSIFICATION (rule-based, keyword scoring)
# =====================================================
#
# Two-level deterministic classifier:
#   1. Chapter-level keywords (broad).
#   2. Concept-level keywords nested under each chapter (fine-grained).
# The concept with the highest cumulative keyword-length score wins;
# its parent chapter is used as the chapter label. Falls back to
# chapter-only keywords if no concept-level match is found, and to
# "Unknown" if nothing matches at all.

CHAPTER_CONCEPTS = {
    "Chemical Reactions and Equations": {
        "Types of chemical reactions": [
            "combination reaction", "decomposition reaction",
            "displacement", "double displacement", "precipitate",
            "precipitation",
        ],
        "Oxidation and reduction": [
            "oxidation", "reduction", "redox", "oxidized", "reduced",
        ],
        "Corrosion and rancidity": [
            "corrosion", "rusting", "rancidity", "galvanization",
            "galvanisation", "alloying",
        ],
        "Balancing chemical equations": [
            "balanced equation", "balanced chemical equation", "chemical equation",
        ],
    },
    "Acids, Bases and Salts": {
        "pH and indicators": [
            "ph", "indicator", "litmus", "universal indicator",
        ],
        "Reactions of acids and bases": [
            "acid", "base", "neutralisation", "neutralization",
            "lime water", "calcium hydroxide", "hydrochloric acid",
        ],
        "Common salts": [
            "salt", "baking soda", "washing soda", "bleaching powder",
            "plaster of paris", "chlor alkali", "chlor-alkali",
        ],
    },
    "Metals and Non-metals": {
        "Reactivity and displacement": [
            "reactivity series", "reactivity", "displacement reaction",
            "ferrous sulphate", "copper coin",
        ],
        "Properties and uses of metals": [
            "metal", "non-metal", "malleable", "ductile", "alloy",
            "ore", "mineral",
        ],
        "Extraction and corrosion of metals": [
            "extraction of metal", "corrosion", "rusting", "galvanization",
        ],
    },
    "Carbon and its Compounds": {
        "Hydrocarbons": [
            "hydrocarbon", "saturated", "unsaturated", "ethene", "ethyne",
            "homologous series",
        ],
        "Ethanol and ethanoic acid": [
            "ethanol", "ethanoic acid", "esterification", "ester",
            "vinegar", "acetic acid",
        ],
        "Soaps and detergents": [
            "soap", "detergent", "micelle",
        ],
        "Covalent bonding": [
            "covalent bond", "covalent", "carbon compound",
        ],
    },
    "Life Processes": {
        "Nutrition and digestion": [
            "digestion", "bile", "gallbladder", "nutrition", "villi",
        ],
        "Respiration": [
            "respiration", "photosynthesis", "stomata",
        ],
        "Transportation": [
            "blood", "heart", "xylem", "phloem", "transpiration", "lymph",
        ],
        "Excretion": [
            "kidney", "urine", "nephron", "excretion", "reabsorbed",
        ],
    },
    "Control and Coordination": {
        "Nervous system": [
            "reflex", "neuron", "nervous", "brain", "spinal cord",
        ],
        "Hormones and plant coordination": [
            "hormone", "auxin", "tropic", "phototropism", "geotropism",
        ],
    },
    "How do Organisms Reproduce": {
        "Human reproduction": [
            "puberty", "menstruation", "uterus", "placenta", "embryo",
            "testis", "ovary", "fertilization", "fertilisation",
        ],
        "Modes of reproduction": [
            "reproduction", "zygote", "vegetative propagation",
        ],
    },
    "Heredity": {
        "Mendelian genetics": [
            "dominant", "recessive", "pea plant", "genotype", "phenotype",
            "cross", "f1", "f2", "monohybrid",
        ],
        "Variation and evolution": [
            "variation", "chromosome", "dna", "gene", "trait", "offspring",
            "inheritance",
        ],
    },
    "Light - Reflection and Refraction": {
        "Mirrors": [
            "mirror", "concave mirror", "convex mirror", "focal length",
            "ray diagram",
        ],
        "Lenses": [
            "lens", "convex lens", "concave lens", "magnification",
            "image distance", "object distance", "lens formula",
        ],
    },
    "Human Eye and Colourful World": {
        "Human eye defects": [
            "human eye", "retina", "myopia", "hypermetropia", "cataract",
        ],
        "Dispersion and scattering": [
            "dispersion", "prism", "spectrum", "scattering", "rainbow",
        ],
    },
    "Electricity": {
        "Ohm's law and resistance": [
            "resistance", "ohm", "resistivity", "temperature of the wire",
        ],
        "Circuits": [
            "circuit", "series", "parallel", "ammeter", "voltmeter", "fuse",
        ],
        "Power": [
            "electric power", "power rating", "kwh",
        ],
    },
    "Magnetic Effects of Electric Current": {
        "Magnetic field and field lines": [
            "magnetic field", "field lines", "bar magnet", "iron filings",
            "magnet", "poles of a magnet",
        ],
        "Electromagnetism": [
            "solenoid", "compass", "electromagnet", "right hand", "motor",
            "generator", "current carrying", "force on the wire",
            "fleming", "left hand rule", "current in the wire",
        ],
    },
    "Our Environment": {
        "Ecosystem and waste": [
            "ecosystem", "food chain", "biodegradable", "non biodegradable",
            "waste",
        ],
        "Ozone layer": [
            "ozone", "cfc", "chlorofluorocarbon", "uv radiation",
        ],
    },
    "Sustainable Management of Natural Resources": {
        "Conservation": [
            "water harvesting", "conservation", "sustainable", "forest",
            "wildlife",
        ],
        "Resources": [
            "coal", "petroleum", "fossil fuel", "dam", "resource",
        ],
    },
}


def classify_chapter_and_concept(question_text: str, answer_text: str = ""):
    """
    Deterministic keyword scoring across question + answer text.
    Returns (chapter, concept). Falls back to ("Unknown", "Unknown")
    when nothing matches.
    """

    haystack = f"{question_text} {answer_text}".lower()

    best_chapter = None
    best_concept = None
    best_score = 0

    chapter_scores = defaultdict(int)

    for chapter, concepts in CHAPTER_CONCEPTS.items():
        for concept, keywords in concepts.items():
            score = 0
            for keyword in keywords:
                if keyword in haystack:
                    score += len(keyword)
            chapter_scores[chapter] += score
            if score > best_score:
                best_score = score
                best_chapter = chapter
                best_concept = concept

    if best_chapter is not None:
        return best_chapter, best_concept

    if chapter_scores and max(chapter_scores.values()) > 0:
        chapter = max(chapter_scores, key=lambda c: chapter_scores[c])
        return chapter, "Unknown"

    return "Unknown", "Unknown"


# =====================================================
# BUILD DATABASE
# =====================================================


def build_exam_database(
    question_pdf,
    marking_pdf,
    year="2022-23",
    subject="Science",
    class_name="X",
):

    print(f"[{year}] Parsing question paper: {question_pdf}")
    questions = extract_questions(question_pdf)

    print(f"[{year}] Parsing marking scheme: {marking_pdf}")
    answers = extract_answers(marking_pdf)

    all_numbers = sorted(set(questions) | set(answers))

    records = []
    missing_questions = []
    missing_answers = []

    for q_no in all_numbers:

        q_item = questions.get(q_no)
        a_item = answers.get(q_no)

        if q_item is None:
            missing_questions.append(q_no)
            question_text = ""
        else:
            question_text = q_item["question"]

        if a_item is None:
            missing_answers.append(q_no)
            answer_text = ""
        else:
            answer_text = a_item["answer"]

        section = (q_item or {}).get("section") or (a_item or {}).get("section")

        marks = (q_item or {}).get("marks")
        if marks is None:
            marks = (a_item or {}).get("marks")
        if marks is None and section in SECTION_DEFAULTS:
            marks = SECTION_DEFAULTS[section][1]

        question_type = classify_question_type(question_text, section)
        subparts = extract_subparts(question_text)
        internal_choice = has_internal_choice(question_text)

        chapter, concept = classify_chapter_and_concept(question_text, answer_text)

        records.append(
            {
                "year": year,
                "class": class_name,
                "subject": subject,
                "question_no": q_no,
                "section": section,
                "question_type": question_type,
                "marks": marks,
                "subparts": subparts,
                "has_internal_choice": internal_choice,
                "question": question_text,
                "answer": answer_text,
                "chapter": chapter,
                "concept": concept,
            }
        )

    if missing_questions:
        print(f"  WARNING: no question text found for #: {missing_questions}")
    if missing_answers:
        print(f"  WARNING: no answer text found for #: {missing_answers}")

    save_database(records)
    print(f"  Saved {len(records)} questions ({len(missing_answers)} missing answers)")

    return records


# =====================================================
# SAVE / LOAD DATABASE
# =====================================================


def save_database(records, overwrite=False):

    os.makedirs(os.path.dirname(EXAM_DATABASE_PATH), exist_ok=True)

    old_data = []
    if not overwrite and os.path.exists(EXAM_DATABASE_PATH):
        with open(EXAM_DATABASE_PATH, "r", encoding="utf-8") as file:
            old_data = json.load(file)

    old_data.extend(records)

    with open(EXAM_DATABASE_PATH, "w", encoding="utf-8") as file:
        json.dump(old_data, file, indent=4, ensure_ascii=False)


def load_database():
    if not os.path.exists(EXAM_DATABASE_PATH):
        return []
    with open(EXAM_DATABASE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


# =====================================================
# LIGHTWEIGHT ANALYSIS HELPERS (unchanged public API)
# =====================================================


def chapter_weightage():
    data = load_database()
    result = {}
    for item in data:
        chapter = item["chapter"]
        result.setdefault(chapter, {"questions": 0})
        result[chapter]["questions"] += 1
    return result


# =====================================================
# CLI / BATCH BUILD
# =====================================================

if __name__ == "__main__":

    sample_paper_dir = os.path.join(BASE_DIR, "data", "sample_papers")

    if not os.path.isdir(sample_paper_dir):
        print(f"No sample_papers directory found at {sample_paper_dir}")
        raise SystemExit(0)

    folders = sorted(os.listdir(sample_paper_dir))

    for folder in folders:

        folder_path = os.path.join(sample_paper_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        print(f"\nProcessing {folder}")

        question_pdf = None
        marking_pdf = None

        for file in os.listdir(folder_path):
            lower = file.lower()
            if "sqp" in lower:
                question_pdf = os.path.join(folder_path, file)
            elif "ms" in lower:
                marking_pdf = os.path.join(folder_path, file)

        if question_pdf is None or marking_pdf is None:
            print("Missing PDFs")
            continue

        year = folder.replace("X Science ", "")

        build_exam_database(
            question_pdf=question_pdf,
            marking_pdf=marking_pdf,
            year=year,
            subject="Science",
            class_name="X",
        )

    print("\nFinished building database.")
