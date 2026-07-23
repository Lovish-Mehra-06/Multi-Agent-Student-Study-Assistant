from pathlib import Path
import streamlit as st
from app import create_controller

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Multi-Agent Student Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Custom Professional CSS Styling (Forced High-Contrast Theme)
# --------------------------------------------------
st.markdown(
    """
    <style>
    /* Global Container Background and Standard Text */
    .stApp {
        background-color: #FFFFFF;
        color: #111827;
    }
    .main-header {
        font-size: 2.25rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    
    /* Force high-contrast text color for chat messages, markdown blocks, and expanders */
    .stChatMessage, .stChatMessage p, .stChatMessage span, .stChatMessage div,
    .stMarkdown, div[data-testid="stMarkdownContainer"], 
    div[data-testid="stExpanderDetails"] p, div[data-testid="stExpanderDetails"] span {
        color: #111827 !important;
    }

    /* Style Chat Containers for clear distinction */
    div[data-testid="stChatMessage"] {
        background-color: #F3F4F6;
        border: 1px solid #E5E7EB;
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Style Expanders */
    div[data-testid="stExpander"] {
        border: 1px solid #D1D5DB;
        border-radius: 0.5rem;
        background-color: #F9FAFB;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    div[data-testid="stExpander"] summary p {
        color: #1F2937 !important;
        font-weight: 600;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Cached Resource Controller Initialization
# --------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_controller():
    return create_controller()


# --------------------------------------------------
# Sidebar Configuration & App Info
# --------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=64)
    st.markdown("### Study Assistant Panel")
    st.write(
        "Powered by a collaborative multi-agent architecture to retrieve, synthesize, audit, and structure learning materials."
    )

    st.markdown("---")
    st.markdown("#### Capabilities")
    st.markdown("- 📖 **Contextual QA & Answers**")
    st.markdown("- 📝 **Automated Study Notes**")
    st.markdown("- 🃏 **Flashcards Generation (CSV)**")
    st.markdown("- 🔍 **Exam & PYQ Analysis**")

    st.markdown("---")
    if st.button(
        "Clear Conversation History", type="secondary", use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()

# --------------------------------------------------
# Main Header Section
# --------------------------------------------------
st.markdown(
    '<p class="main-header">🎓 Multi-Agent Student Study Assistant</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-header">Ask questions, request study notes, build flashcards, or study exam trends naturally.</p>',
    unsafe_allow_html=True,
)

# Initialize Controller with a clean status box
if "controller" not in st.session_state:
    with st.status("Initializing AI Agents & Vector Store...", expanded=True) as status:
        st.write("Loading vector database indices...")
        st.session_state.controller = load_controller()
        status.update(label="System Ready!", state="complete", expanded=False)

controller = st.session_state.controller

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your Multi-Agent Study Assistant. How can I help you learn today? You can ask me to explain a concept, generate notes, make flashcards, or look up exam questions.",
            "result": None,
        }
    ]


def render_result_payload(result):
    """Helper function to render structured agent outputs safely and provide file downloads."""
    res_type = result.get("type")

    if res_type == "answer":
        st.write(result.get("answer"))

    elif res_type in ["notes", "flashcards"]:
        if "notes" in result:
            st.markdown(result["notes"])

        # Handle Notes File Download & Display
        notes_file = result.get("notes_file")
        if notes_file and Path(notes_file).exists():
            st.caption(f"💾 Saved locally to: `{notes_file}`")
            with open(notes_file, "r", encoding="utf-8") as f:
                notes_data = f.read()
            st.download_button(
                label="📥 Download Generated Notes",
                data=notes_data,
                file_name=Path(notes_file).name,
                mime="text/markdown",
            )

        # Handle Flashcards CSV File Download & Display
        flashcards_file = result.get("flashcards_file")
        if flashcards_file and Path(flashcards_file).exists():
            st.caption(f"💾 Flashcards CSV saved to: `{flashcards_file}`")
            with open(flashcards_file, "r", encoding="utf-8") as f:
                csv_data = f.read()
            st.download_button(
                label="📥 Download Flashcards CSV",
                data=csv_data,
                file_name=Path(flashcards_file).name,
                mime="text/csv",
            )

    elif res_type == "exam_analysis":
        if "report" in result:
            st.markdown(result["report"])
        sources = result.get("sources", [])
        if sources:
            st.markdown("#### 📋 Analyzed Previous Year Questions")
            for idx, q in enumerate(sources, start=1):
                with st.expander(
                    f"Q{idx} ({q.get('year', 'N/A')}) — Chapter: {q.get('chapter', 'N/A')}"
                ):
                    st.markdown(f"**Concept:** {q.get('concept', 'Unknown')}")
                    st.markdown(f"**Question:**\n{q['question']}")
                    if q.get("answer"):
                        st.markdown(f"**Answer:**\n{q['answer']}")

    # Audit Report Expander
    if result.get("audit"):
        with st.expander("🔍 Quality Auditor Review"):
            st.write(result["audit"])

    # Source References Expander
    sources = result.get("sources", [])
    if sources and res_type != "exam_analysis":
        with st.expander("📖 Source References"):
            for idx, doc in enumerate(sources, start=1):
                meta = doc.metadata
                st.markdown(
                    f"**{idx}. {meta.get('source', 'Unknown')}** "
                    f"(Chapter: {meta.get('chapter_number', 'Unknown')}, "
                    f"Subject: {meta.get('subject', 'Unknown')})"
                )


# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        res = message.get("result")
        if res:
            render_result_payload(res)

# --------------------------------------------------
# Chat Input & Core Execution Loop
# --------------------------------------------------
if prompt := st.chat_input("Type your study query or command here..."):
    # Append user message
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "result": None}
    )
    with st.chat_message("user"):
        st.markdown(prompt)

    # Execute Agent workflow
    with st.chat_message("assistant"):
        with st.spinner("Multi-agent team processing your query..."):
            try:
                result = controller.run(prompt)
                response_text = "Here is what our agents generated for your request:"

                st.markdown(response_text)
                render_result_payload(result)

                # Save assistant response state
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                        "result": result,
                    }
                )
            except Exception as e:
                error_msg = f"An error occurred while executing the request: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg, "result": None}
                )
