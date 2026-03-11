"""
Skrypt do automatycznego generowania danych treningowych Q&A z PDFów dokumentacji PAN-OS.

Użycie:
    1. Wrzuć PDFy do folderu: data/pdfs/
    2. Uruchom: python generate_qa.py
    3. Wynik zapisze się do: data/panos_training_data.jsonl
    4. Wgraj ten plik do Colab i trenuj od nowa

Wymagania:
    pip install anthropic pypdf langchain-text-splitters
"""

import os
import json
import time
from pathlib import Path
from anthropic import Anthropic
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── KONFIGURACJA ──────────────────────────────────────────────────────────────
PDF_DIR         = "./data/pdfs"          # folder z PDFami
OUTPUT_FILE     = "./data/panos_training_data.jsonl"
QA_PER_CHUNK    = 1                      # ile Q&A generować z każdego fragmentu
MAX_CHUNKS      = 20                    # limit chunków (None = bez limitu)
CHUNK_SIZE      = 800                    # rozmiar fragmentu tekstu
CHUNK_OVERLAP   = 100

from dotenv import load_dotenv
load_dotenv()
load_dotenv("./backend/.env")

client = Anthropic()


def extract_text_from_pdf(pdf_path: str) -> str:
    """Wyciąga tekst z PDFa"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def generate_qa_from_chunk(chunk: str, source: str) -> list[dict]:
    """Generuje Q&A z fragmentu tekstu przez Claude API"""
    prompt = f"""Na podstawie poniższego fragmentu dokumentacji Palo Alto Networks PAN-OS wygeneruj {QA_PER_CHUNK} par pytanie-odpowiedź.

Zasady:
- Pytania muszą być konkretne i techniczne
- Odpowiedzi muszą być wyczerpujące i zawierać przykłady konfiguracji jeśli to możliwe
- Pytania i odpowiedzi pisz po polsku
- Format odpowiedzi: TYLKO czysty JSON, bez żadnego tekstu przed/po
- Nie używaj znaków specjalnych które psują JSON

Fragment dokumentacji (źródło: {source}):
{chunk}

Zwróć TYLKO tablicę JSON w tym formacie:
[
  {{"question": "Pytanie 1?", "answer": "Odpowiedź 1"}},
  {{"question": "Pytanie 2?", "answer": "Odpowiedź 2"}},
  {{"question": "Pytanie 3?", "answer": "Odpowiedź 3"}}
]"""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        response = message.content[0].text.strip()

        # Wyczyść response z markdown jeśli jest
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        qa_list = json.loads(response)
        return qa_list

    except json.JSONDecodeError as e:
        print(f"  ⚠️  Błąd parsowania JSON: {e}")
        return []
    except Exception as e:
        print(f"  ⚠️  Błąd API: {e}")
        return []


def process_pdfs():
    """Główna funkcja — przetwarza wszystkie PDFy i generuje dane treningowe"""

    # Sprawdź czy folder istnieje
    pdf_dir = Path(PDF_DIR)
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)
        print(f"✅ Stworzono folder: {PDF_DIR}")
        print(f"📁 Wrzuć PDFy do folderu {PDF_DIR}/ i uruchom skrypt ponownie")
        return

    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"❌ Brak plików PDF w folderze {PDF_DIR}/")
        print(f"📁 Wrzuć PDFy z dokumentacji PAN-OS do: {PDF_DIR}/")
        return

    print(f"📄 Znaleziono {len(pdfs)} plików PDF:")
    for p in pdfs:
        print(f"   - {p.name}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    all_qa = []
    total_chunks = 0

    # Załaduj istniejące dane jeśli plik już istnieje
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
        print(f"\n📊 Istniejące dane treningowe: {len(existing)} przykładów")
        all_qa = existing
    else:
        all_qa = []

    print(f"\n🚀 Generuję nowe dane treningowe...\n")

    for pdf_path in pdfs:
        print(f"📖 Przetwarzam: {pdf_path.name}")

        text = extract_text_from_pdf(str(pdf_path))
        if not text.strip():
            print(f"  ⚠️  Pusty tekst — pomijam")
            continue

        chunks = splitter.split_text(text)
        print(f"  📝 Fragmentów: {len(chunks)}")

        # Ogranicz liczbę chunków jeśli ustawiono limit
        if MAX_CHUNKS:
            chunks = chunks[:MAX_CHUNKS]
            print(f"  🔢 Używam pierwszych {len(chunks)} fragmentów")

        for i, chunk in enumerate(chunks):
            # Pomiń zbyt krótkie fragmenty
            if len(chunk.strip()) < 100:
                continue

            print(f"  ⚙️  Chunk {i+1}/{len(chunks)} — generuję Q&A...", end="", flush=True)
            qa_list = generate_qa_from_chunk(chunk, pdf_path.name)

            if qa_list:
                # Konwertuj do formatu treningowego
                for qa in qa_list:
                    if "question" in qa and "answer" in qa:
                        all_qa.append({
                            "text": f"### Question: {qa['question']}\n### Answer: {qa['answer']}",
                            "source": pdf_path.name
                        })
                print(f" ✅ {len(qa_list)} Q&A")
            else:
                print(f" ❌ Brak")

            total_chunks += 1

            # Pauza żeby nie przekroczyć rate limit API
            time.sleep(1)

        print(f"  ✅ Zakończono: {pdf_path.name}\n")

    # Zapisz wyniki
    with open(output_path, "w", encoding="utf-8") as f:
        for item in all_qa:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    new_count = len(all_qa)
    print(f"{'='*60}")
    print(f"✅ GOTOWE!")
    print(f"📊 Łącznie danych treningowych: {new_count}")
    print(f"💾 Zapisano do: {OUTPUT_FILE}")
    print(f"{'='*60}")
    print(f"\n📋 NASTĘPNY KROK:")
    print(f"1. Wgraj plik {OUTPUT_FILE} do Google Colab")
    print(f"2. W Colab zmień nazwę pliku na: panos_training_data.jsonl")
    print(f"3. Uruchom komórki 3, 4, 5 od nowa (pomiń 1 i 2)")


if __name__ == "__main__":
    process_pdfs()
