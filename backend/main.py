from dotenv import load_dotenv
load_dotenv()

import os
import json
import shutil


from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import rag_answer, add_pdf_to_vectorstore
from finetuned import finetuned_answer
from database import save_conversation, update_rating, get_history
from datetime import datetime



app = FastAPI(title="PAN-OS AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QuestionRequest(BaseModel):
    question: str


class RatingRequest(BaseModel):
    conv_id: int
    mode: str   # "rag" lub "ft"
    rating: int  # 1 lub -1


@app.get("/")
def root():
    return {"status": "ok", "message": "PAN-OS AI Assistant API"}


@app.post("/ask")
def ask_question(req: QuestionRequest):
    """Pyta oba modele jednocześnie i zwraca porównanie odpowiedzi"""
    try:
        question = req.question.strip()
        if not question:
            raise HTTPException(400, detail="Pytanie nie moze byc puste")

        # Pobierz odpowiedzi z obu modeli
        rag_resp, sources = rag_answer(question)
        ft_resp = finetuned_answer(question)

        # Zapisz do historii
        conv_id = save_conversation(
            question=question,
            rag_answer=rag_resp,
            ft_answer=ft_resp,
            sources=json.dumps(sources)
        )

        return {
            "id": conv_id,
            "question": question,
            "rag": {
                "answer": rag_resp,
                "sources": sources,
                "mode": "RAG (dokumenty)"
            },
            "finetuned": {
                "answer": ft_resp,
                "mode": "Fine-tuned model"
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(500, detail=str(e))


@app.post("/rate")
def rate_answer(req: RatingRequest):
    """Ocena odpowiedzi thumbs up/down"""
    try:
        update_rating(req.conv_id, req.mode, req.rating)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDFa i dodanie do bazy wektorowej"""
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(400, detail="Tylko pliki PDF sa akceptowane")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        chunks = add_pdf_to_vectorstore(file_path)

        return {
            "status": "ok",
            "filename": file.filename,
            "chunks": chunks,
            "message": f"Dodano {chunks} fragmentow do bazy wiedzy"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/history")
def get_chat_history(limit: int = Query(50)):
    """Historia rozmów"""
    try:
        records = get_history(limit=limit)
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "question": r.question,
                "rag_answer": r.rag_answer,
                "ft_answer": r.ft_answer,
                "rag_rating": r.rag_rating,
                "ft_rating": r.ft_rating,
                "sources": json.loads(r.sources) if r.sources else []
            }
            for r in records
        ]
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/stats")
def get_stats():
    """Statystyki ocen modeli"""
    try:
        records = get_history(limit=1000)
        rag_up   = sum(1 for r in records if r.rag_rating == 1)
        rag_down = sum(1 for r in records if r.rag_rating == -1)
        ft_up    = sum(1 for r in records if r.ft_rating == 1)
        ft_down  = sum(1 for r in records if r.ft_rating == -1)

        return {
            "total_conversations": len(records),
            "rag": {"thumbs_up": rag_up, "thumbs_down": rag_down},
            "finetuned": {"thumbs_up": ft_up, "thumbs_down": ft_down}
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))
