"""
modules/exam_data.py

Purpose:
    Process CBSE sample papers and marking schemes.

Flow:
    Question Paper PDF
            |
            ↓
    Extract Questions
            |
            ↓
    Marking Scheme PDF
            |
            ↓
    Extract Answers
            |
            ↓
    Chapter Mapping
            |
            ↓
    exam_database.json

Used by:
    agents/exam_analysis_agent.py
"""

import os
import re
import json
import fitz

from modules.llm_client import LLMClient

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

EXAM_DATABASE_PATH = os.path.join(BASE_DIR, "data", "exam_database.json")


# =====================================================
# PDF TEXT EXTRACTION
# =====================================================


def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF
    """

    document = fitz.open(pdf_path)

    pages_text = []

    for page in document:
        pages_text.append(page.get_text("text"))

    document.close()

    return "\n".join(pages_text)


# =====================================================
# QUESTION PAPER PARSER
# =====================================================
def extract_questions(text: str):

    lines = text.splitlines()

    questions = []

    current_number = None
    current_text = []

    expected_number = 1

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Detect possible question number
        match = re.match(r"^(\d{1,2})\s*(.*)", line)

        if match:

            number = int(match.group(1))
            remaining = match.group(2).strip()

            # Valid question start:
            # Must match expected sequence
            if number == expected_number and number <= 39:

                # save previous
                if current_number is not None:

                    questions.append(
                        {
                            "question_no": current_number,
                            "question": clean_text(" ".join(current_text)),
                        }
                    )

                current_number = number

                current_text = []

                if remaining:
                    current_text.append(remaining)

                expected_number += 1

                continue

        # normal line
        if current_number is not None:

            current_text.append(line)

    # save last question

    if current_number is not None:

        questions.append(
            {
                "question_no": current_number,
                "question": clean_text(" ".join(current_text)),
            }
        )

    return questions


# =====================================================
# MARKING SCHEME PARSER
# =====================================================
def extract_answers(text: str):

    lines = text.splitlines()

    answers = {}

    current_number = None
    current_text = []

    expected = 1

    for line in lines:

        line = line.strip()

        if not line:
            continue

        match = re.match(r"^(\d{1,2})\.\s*(.*)", line)

        if match:

            number = int(match.group(1))
            remaining = match.group(2)

            if number == expected:

                if current_number is not None:

                    answers[current_number] = clean_text(" ".join(current_text))

                current_number = number
                current_text = [remaining]

                expected += 1

                continue

        if current_number is not None:

            current_text.append(line)

    if current_number:

        answers[current_number] = clean_text(" ".join(current_text))

    return answers


# =====================================================
# TEXT CLEANING
# =====================================================


def clean_text(text):

    text = text.replace("\n", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =====================================================
# CHAPTER CLASSIFIER
# =====================================================
# =====================================================
# CHAPTER CLASSIFIER
# =====================================================

CHAPTER_KEYWORDS = {
    "chemical reactions and equations": [
        "reaction",
        "chemical",
        "oxidation",
        "reduction",
        "redox",
        "combination",
        "decomposition",
        "displacement",
        "double displacement",
        "precipitate",
        "equation",
        "corrosion",
        "rusting",
        "balanced equation",
    ],
    "acids bases and salts": [
        "acid",
        "base",
        "salt",
        "ph",
        "indicator",
        "litmus",
        "neutralisation",
        "neutralization",
        "h+",
        "oh-",
        "lime water",
        "calcium hydroxide",
    ],
    "metals and non-metals": [
        "metal",
        "non-metal",
        "copper",
        "iron",
        "zinc",
        "silver",
        "gold",
        "ferrous",
        "aluminium",
        "magnesium",
        "reactivity",
        "alloy",
        "galvanization",
        "ore",
        "mineral",
    ],
    "carbon and its compounds": [
        "carbon",
        "ethanol",
        "ethene",
        "ethyne",
        "ester",
        "soap",
        "detergent",
        "covalent",
        "ethanoic",
        "hydrocarbon",
        "homologous",
        "saturated",
        "unsaturated",
    ],
    "life processes": [
        "respiration",
        "photosynthesis",
        "kidney",
        "heart",
        "blood",
        "digestion",
        "bile",
        "gallbladder",
        "nutrition",
        "stomata",
        "transpiration",
        "xylem",
        "phloem",
        "urine",
        "nephron",
        "lymph",
    ],
    "control and coordination": [
        "hormone",
        "brain",
        "reflex",
        "neuron",
        "nervous",
        "coordination",
        "auxin",
        "tropic",
        "phototropism",
        "geotropism",
    ],
    "how do organisms reproduce": [
        "reproduction",
        "fertilization",
        "zygote",
        "placenta",
        "embryo",
        "menstruation",
        "puberty",
        "testis",
        "ovary",
        "uterus",
    ],
    "heredity": [
        "gene",
        "trait",
        "dominant",
        "recessive",
        "inheritance",
        "pea",
        "genotype",
        "phenotype",
        "variation",
        "offspring",
        "chromosome",
        "dna",
    ],
    "light reflection and refraction": [
        "mirror",
        "lens",
        "image",
        "object",
        "reflection",
        "refraction",
        "focal",
        "focus",
        "concave",
        "convex",
        "magnification",
        "ray diagram",
    ],
    "human eye and colourful world": [
        "human eye",
        "retina",
        "myopia",
        "hypermetropia",
        "cataract",
        "dispersion",
        "spectrum",
        "rainbow",
        "prism",
        "scattering",
        "atmosphere",
    ],
    "electricity": [
        "current",
        "voltage",
        "resistance",
        "ohm",
        "ammeter",
        "voltmeter",
        "power",
        "circuit",
        "wire",
        "series",
        "parallel",
        "fuse",
    ],
    "magnetic effects of electric current": [
        "magnet",
        "magnetic",
        "solenoid",
        "compass",
        "electromagnet",
        "field lines",
        "right hand",
        "fleming",
        "motor",
        "generator",
    ],
    "our environment": [
        "ecosystem",
        "food chain",
        "biodegradable",
        "non biodegradable",
        "ozone",
        "waste",
        "pollution",
        "environment",
    ],
    "sustainable management of natural resources": [
        "forest",
        "water harvesting",
        "coal",
        "petroleum",
        "resource",
        "wildlife",
        "conservation",
        "dam",
        "sustainable",
    ],
}


def classify_chapter(question: str):

    q = question.lower()

    scores = {}

    for chapter, keywords in CHAPTER_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in q:
                score += len(keyword)

        scores[chapter] = score

    best = max(scores, key=lambda chapter: scores[chapter])

    if scores[best] == 0:
        return "Unknown", 0

    return best, scores[best]


# =====================================================
# LLM CHAPTER CLASSIFIER
# =====================================================

_llm = None


def llm_classify(question: str, answer: str = "") -> tuple[str, str]:
    """
    Returns:
        (chapter, concept)
    """

    global _llm

    if _llm is None:
        _llm = LLMClient(temperature=0)

    prompt = f"""
Classify the following CBSE Class 10 Science question.

Question:
{question}

Answer:
{answer}

Choose ONLY one chapter from this list:

1. Chemical Reactions and Equations
2. Acids, Bases and Salts
3. Metals and Non-metals
4. Carbon and Its Compounds
5. Life Processes
6. Control and Coordination
7. How do Organisms Reproduce
8. Heredity
9. Light - Reflection and Refraction
10. Human Eye and Colourful World
11. Electricity
12. Magnetic Effects of Electric Current
13. Our Environment
14. Sustainable Management of Natural Resources

Also identify the main concept.

Return ONLY this JSON.

{{
    "chapter":"...",
    "concept":"..."
}}
"""

    response = _llm.generate(prompt)

    try:
        import json

        data = json.loads(response)

        return (
            data.get("chapter", "Unknown"),
            data.get("concept", "Unknown"),
        )

    except Exception:

        return ("Unknown", "Unknown")


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

    print("Extracting Question Paper...")
    question_text = extract_pdf_text(question_pdf)

    print("Extracting Marking Scheme...")
    marking_text = extract_pdf_text(marking_pdf)

    questions = extract_questions(question_text)
    answers = extract_answers(marking_text)

    records = []

    for item in questions:

        q_no = item["question_no"]

        # ---------- Chapter Classification ----------
        chapter, concept = llm_classify(item["question"], answers.get(q_no, ""))
        records.append(
            {
                "year": year,
                "class": class_name,
                "subject": subject,
                "question_no": q_no,
                "question": item["question"],
                "answer": answers.get(q_no, ""),
                "chapter": chapter,
                "concept": concept,
            }
        )

    save_database(records)

    print(f"Saved {len(records)} questions")

    return records


# =====================================================
# SAVE DATABASE
# =====================================================


def save_database(records):

    os.makedirs(os.path.dirname(EXAM_DATABASE_PATH), exist_ok=True)

    old_data = []

    if os.path.exists(EXAM_DATABASE_PATH):

        with open(EXAM_DATABASE_PATH, "r", encoding="utf-8") as file:

            old_data = json.load(file)

    old_data.extend(records)

    with open(EXAM_DATABASE_PATH, "w", encoding="utf-8") as file:

        json.dump(old_data, file, indent=4, ensure_ascii=False)


# =====================================================
# LOAD DATABASE
# =====================================================


def load_database():

    if not os.path.exists(EXAM_DATABASE_PATH):

        return []

    with open(EXAM_DATABASE_PATH, "r", encoding="utf-8") as file:

        return json.load(file)


# =====================================================
# ANALYSIS FUNCTIONS
# =====================================================


def chapter_weightage():

    data = load_database()

    result = {}

    for item in data:

        chapter = item["chapter"]

        if chapter not in result:

            result[chapter] = {"questions": 0}

        result[chapter]["questions"] += 1

    return result


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    sample_paper_dir = os.path.join(BASE_DIR, "data", "sample_papers")

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
