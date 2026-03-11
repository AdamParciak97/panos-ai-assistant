# 🧠 PAN-OS AI Assistant

Aplikacja do porównania dwóch technik AI — **RAG** i **Fine-tuning** — na dokumentacji Palo Alto Networks PAN-OS. Projekt stworzony jako część portfolio z zakresu AI/ML i cyberbezpieczeństwa.

---

## 📸 Demo
### Screnshoots
<img width="1886" height="890" alt="image" src="https://github.com/user-attachments/assets/80239900-e33c-44ce-86bf-562d913ba8bd" />

Aplikacja pokazuje odpowiedzi obu modeli obok siebie na to samo pytanie:

- **RAG** — przeszukuje dokumenty w czasie rzeczywistym i cytuje źródła
- **Fine-tuned** — odpowiada z wiedzy wbudowanej podczas treningu (TinyLlama + LoRA)

---

## ✨ Funkcjonalności

- 💬 **Chat interface** — zadawaj pytania o PAN-OS w języku polskim
- 🔍 **Porównanie RAG vs Fine-tune** — odpowiedzi obok siebie
- 📄 **Upload PDFów** — wgrywaj własną dokumentację do bazy RAG
- 👍👎 **Ocena odpowiedzi** — głosuj który model odpowiada lepiej
- 📊 **Statystyki** — który model wygrywa na podstawie ocen
- 📁 **Historia rozmów** — wszystkie poprzednie pytania i odpowiedzi

---

## 🛠️ Stack technologiczny

| Warstwa | Technologia |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, SQLite |
| RAG | LangChain, FAISS, sentence-transformers |
| Fine-tuning | Hugging Face Transformers, PEFT (LoRA) |
| Model bazowy | TinyLlama-1.1B-Chat |
| AI API | Anthropic Claude (RAG + generowanie Q&A) |
| Frontend | React, Vite |
| Trening | Google Colab (T4 GPU) |

---

## 📁 Struktura projektu

```
panos-ai-assistant/
├── backend/
│   ├── main.py               # FastAPI endpoints
│   ├── rag.py                # RAG pipeline (LangChain + FAISS)
│   ├── finetuned.py          # Lokalny fine-tuned model (LoRA)
│   ├── database.py           # Historia rozmów i oceny (SQLite)
│   ├── .env.example          # Szablon konfiguracji
│   ├── requirements.txt
│   └── models/               # Folder na wytrenowany model (nie w repo)
├── frontend/
│   └── src/
│       └── App.jsx           # React UI
├── colab/
│   └── finetune.py           # Notebook do trenowania w Google Colab
├── data/
│   ├── pdfs/                 # PDFy do RAG (nie w repo)
│   └── panos_training_data.jsonl  # Dane treningowe (nie w repo)
├── generate_qa.py            # Skrypt generowania Q&A z PDFów
└── README.md
```

---

## ⚙️ Instalacja i uruchomienie

### Wymagania
- Python 3.10+
- Node.js 18+
- Klucz API Anthropic (https://console.anthropic.com)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

Stwórz plik `backend/.env` na podstawie `.env.example`:

```env
ANTHROPIC_API_KEY=sk-ant-...
FINETUNED_MODEL_PATH=./models/panos-finetuned
```

Uruchom:

```bash
python -m uvicorn main:app --reload
```

API dostępne na: **http://localhost:8000/docs**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplikacja dostępna na: **http://localhost:5173**

---

## 🤖 Fine-tuning — jak wytrenować własny model

### 1. Wygeneruj dane treningowe z PDFów

```bash
# Wrzuć PDFy do data/pdfs/
# Ustaw w generate_qa.py: QA_PER_CHUNK=1, MAX_CHUNKS=20
python generate_qa.py
```

### 2. Trenuj w Google Colab

1. Otwórz https://colab.research.google.com
2. Zmień runtime: **Runtime → Change runtime type → T4 GPU**
3. Wgraj `data/panos_training_data.jsonl` do `/content/`
4. Uruchom komórki z `colab/finetune.py` po kolei
5. Pobierz `panos-finetuned.zip`

### 3. Wgraj model do projektu

```bash
# Rozpakuj ZIP do backend/models/
Expand-Archive panos-finetuned.zip -DestinationPath backend\models\panos-finetuned
```

Zrestartuj backend — Fine-tuned model działa lokalnie bez API.

---

## 🔌 Endpointy API

| Endpoint | Metoda | Opis |
|---|---|---|
| `/ask` | POST | Pytanie do obu modeli jednocześnie |
| `/rate` | POST | Ocena odpowiedzi (👍👎) |
| `/upload-pdf` | POST | Dodaj PDF do bazy RAG |
| `/history` | GET | Historia rozmów |
| `/stats` | GET | Statystyki ocen modeli |

---

## 💡 Czym różni się RAG od Fine-tuningu?

| | RAG | Fine-tuning |
|---|---|---|
| Jak działa | Przeszukuje dokumenty w locie | Wiedza wbudowana podczas treningu |
| Aktualizacja wiedzy | Dodaj nowy PDF — gotowe | Trzeba trenować od nowa |
| Cytowanie źródeł | Tak | Nie |
| Szybkość | Wolniejszy (szukanie) | Szybszy (z pamięci) |
| Najlepszy dla | Aktualnych, zmieniających się danych | Stabilnej, specjalistycznej wiedzy |

---

## 👤 Autor

**Adam Parciak** — [github.com/AdamParciak97](https://github.com/AdamParciak97)
