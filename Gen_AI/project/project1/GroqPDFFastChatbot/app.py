import os
import PyPDF2
import chainlit as cl
from dotenv import load_dotenv

from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# ==================================================
# ENV
# ==================================================
load_dotenv()
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

# ==================================================
# PDF PATHS
# ==================================================
PDFS = {
    "paper1.pdf": "data/paper1.pdf",
    "paper2.pdf": "data/paper2.pdf",
}

CHROMA_DIR = "./chroma_db"

# ==================================================
# LLM
# ==================================================
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0.2,
)

# ==================================================
# PROMPTS (STRONG SYSTEM CONTROL)
# ==================================================
SHORT_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a technical assistant. "
        "Answer briefly and directly. "
        "Limit the answer to 4–5 sentences."
    ),
    (
        "human",
        "Context:\n{context}\n\nQuestion:\n{question}"
    ),
])

DETAILED_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert robotics researcher writing a thesis-level explanation. "
        "You MUST answer using the provided context, even if it is partial. "
        "Do NOT say phrases like 'not enough information' or 'insufficient data'. "
        "Instead, infer and elaborate rigorously from the context. "
        "Be detailed, structured, and technical. "
        "Mention PDF names and page numbers explicitly."
    ),
    (
        "human",
        "Context:\n{context}\n\nQuestion:\n{question}"
    ),
])

# ==================================================
# LOAD + INDEX PDFs (PERSISTENT)
# ==================================================
def load_and_index_pdfs():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    if os.path.exists(CHROMA_DIR):
        return Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
        )

    texts = []
    metadatas = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
    )

    for pdf_name, pdf_path in PDFS.items():
        pdf = PyPDF2.PdfReader(pdf_path)
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if not page_text:
                continue

            chunks = splitter.split_text(page_text)
            for chunk in chunks:
                texts.append(chunk)
                metadatas.append({
                    "pdf": pdf_name,
                    "page": page_num
                })

    return Chroma.from_texts(
        texts,
        embeddings,
        metadatas=metadatas,
        persist_directory=CHROMA_DIR,
    )

# ==================================================
# CHAT START
# ==================================================
@cl.on_chat_start
async def on_chat_start():

    await cl.Message(
        content="📄 Loading PDFs and vector database...",
        elements=[cl.Image(path="pic.jpg", display="inline")],
    ).send()

    vectordb = load_and_index_pdfs()

    cl.user_session.set("mode", "short")

    # --------------------------------------------------
    # PDF-AWARE RETRIEVAL (KEY FIX)
    # --------------------------------------------------
    async def retrieve_docs(input):
        # Extract query string safely
        if isinstance(input, dict):
            query = input.get("question", "")
        else:
            query = input

        query_lower = query.lower()

        # Metadata filtering based on query intent
        if "paper1" in query_lower:
            docs = vectordb.similarity_search(
                query=query,
                k=6,
                filter={"pdf": "paper1.pdf"}
            )
        elif "paper2" in query_lower:
            docs = vectordb.similarity_search(
                query=query,
                k=6,
                filter={"pdf": "paper2.pdf"}
            )
        else:
            docs = vectordb.similarity_search(
                query=query,
                k=6
            )

        context = ""
        for d in docs:
            context += (
                f"Source: {d.metadata['pdf']} (page {d.metadata['page']})\n"
                f"{d.page_content.strip()}\n\n"
            )

        return context

    # --------------------------------------------------
    # RAG CHAIN
    # --------------------------------------------------
    chain = (
        {
            "context": RunnableLambda(retrieve_docs),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(
            lambda x: (
                SHORT_PROMPT
                if cl.user_session.get("mode") == "short"
                else DETAILED_PROMPT
            ).invoke(x)
        )
        | llm
    )

    cl.user_session.set(
        "chain",
        RunnableWithMessageHistory(
            chain,
            lambda _: ChatMessageHistory(),
            input_messages_key="question",
            history_messages_key="history",
        ),
    )

    await cl.Message(
        content=(
            "✅ PDFs loaded successfully.\n\n"
            "Ask questions normally.\n"
            "Use **/short** or **/detailed** anywhere in your message.\n\n"
            "Examples:\n"
            "• explain paper1 /detailed\n"
            "• compare paper1 and paper2\n"
        )
    ).send()

# ==================================================
# MESSAGE HANDLER (COMMANDS ANYWHERE)
# ==================================================
@cl.on_message
async def main(message: cl.Message):

    content = message.content.strip()
    content_lower = content.lower()

    # Mode detection anywhere in message
    if "/detailed" in content_lower:
        cl.user_session.set("mode", "detailed")
        content = content.replace("/detailed", "").strip()

    if "/short" in content_lower:
        cl.user_session.set("mode", "short")
        content = content.replace("/short", "").strip()

    if not content:
        await cl.Message("Mode updated. Please ask your question.").send()
        return

    chain = cl.user_session.get("chain")

    result = await chain.ainvoke(
        {"question": content},
        config={"configurable": {"session_id": "default"}},
    )

    await cl.Message(content=result.content).send()
