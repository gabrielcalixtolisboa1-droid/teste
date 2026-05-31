import os
import uuid
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import pdfplumber
import ollama

app = FastAPI(title="Estudo IA Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
DB_DIR = Path("chroma_db")
DB_DIR.mkdir(exist_ok=True)

chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
collection = chroma_client.get_or_create_collection(
    name="estudos",
    metadata={"hnsw:space": "cosine"},
)

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 < chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > chunk_size:
                words = para.split()
                sub = ""
                for word in words:
                    if len(sub) + len(word) + 1 < chunk_size:
                        sub = (sub + " " + word).strip()
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = word
                current = sub
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Apenas arquivos PDF são suportados")

    safe_name = Path(file.filename).name
    file_path = UPLOAD_DIR / safe_name
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
    except Exception as e:
        raise HTTPException(400, f"Erro ao ler PDF: {e}")

    if not text.strip():
        raise HTTPException(
            400,
            "Não foi possível extrair texto deste PDF. O arquivo pode conter apenas imagens.",
        )

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(400, "Não foi possível dividir o texto em trechos")

    doc_id = str(uuid.uuid4())
    embeddings = embedder.encode(chunks).tolist()

    collection.add(
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[
            {
                "filename": safe_name,
                "doc_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ],
    )

    return {
        "message": f"'{safe_name}' indexado com sucesso",
        "doc_id": doc_id,
        "chunks": len(chunks),
        "characters": len(text),
    }


@app.get("/documents")
async def list_documents():
    try:
        results = collection.get(include=["metadatas"])
    except Exception:
        return []

    docs: dict = {}
    for meta in results["metadatas"]:
        doc_id = meta["doc_id"]
        if doc_id not in docs:
            docs[doc_id] = {
                "doc_id": doc_id,
                "filename": meta["filename"],
                "chunks": meta["total_chunks"],
            }

    return list(docs.values())


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    results = collection.get(where={"doc_id": doc_id})
    if not results["ids"]:
        raise HTTPException(404, "Documento não encontrado")
    collection.delete(ids=results["ids"])
    return {"message": "Documento removido com sucesso"}


class ChatRequest(BaseModel):
    question: str
    model: str = "llama3.2"


@app.post("/chat")
async def chat(request: ChatRequest):
    if collection.count() == 0:
        raise HTTPException(
            400, "Nenhum documento indexado. Faça upload de um PDF primeiro."
        )

    query_embedding = embedder.encode([request.question]).tolist()[0]
    n_results = min(5, collection.count())

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas"],
    )

    chunks = results["documents"][0]
    sources = list(set(m["filename"] for m in results["metadatas"][0]))
    context = "\n\n---\n\n".join(chunks)

    system_prompt = (
        "Você é um assistente de estudos especializado. "
        "Responda APENAS com base no contexto fornecido abaixo. "
        "Se a resposta não estiver no contexto, diga: "
        '"Não encontrei informação sobre isso nos seus documentos." '
        "Seja claro, didático e organize sua resposta com bullet points quando necessário. "
        "Responda em português."
    )

    user_prompt = f"Contexto dos documentos de estudo:\n{context}\n\nPergunta: {request.question}"

    def generate():
        try:
            stream = ollama.chat(
                model=request.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
            )
            for chunk in stream:
                if hasattr(chunk, "message"):
                    token = chunk.message.content or ""
                else:
                    token = chunk.get("message", {}).get("content", "")
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'sources': sources, 'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/models")
async def list_models():
    try:
        models_data = ollama.list()
        model_list = (
            models_data.models
            if hasattr(models_data, "models")
            else models_data.get("models", [])
        )
        names = []
        for m in model_list:
            if hasattr(m, "model"):
                names.append(m.model)
            elif isinstance(m, dict):
                names.append(m.get("model") or m.get("name", ""))
        return {"models": [n for n in names if n] or ["llama3.2"]}
    except Exception:
        return {"models": ["llama3.2"]}


@app.get("/health")
async def health():
    ollama_ok = False
    try:
        ollama.list()
        ollama_ok = True
    except Exception:
        pass
    return {"status": "ok", "ollama": ollama_ok, "documents": collection.count()}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
