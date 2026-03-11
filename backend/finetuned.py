import os
import json
from anthropic import Anthropic

client = Anthropic(timeout=120.0)

FINETUNED_MODEL_PATH = os.getenv("FINETUNED_MODEL_PATH", "./models/panos-finetuned")

# System prompt symulujący fine-tuned model
# Po prawdziwym fine-tuningu podmień na lokalny model
PANOS_SYSTEM_PROMPT = """Jestes asystentem AI wytrenowanym wylacznie na dokumentacji Palo Alto Networks PAN-OS.
Specjalizujesz sie w:
- Konfiguracji Security Policy, NAT, Routing
- Diagnostyce i troubleshootingu
- Best practices bezpieczenstwa
- Integracji z Panorama
- API PAN-OS i automatyzacji

Odpowiadasz zwiezle, technicznie i zawsze podajesz konkretne przyklady konfiguracji.
Jezeli pytanie nie dotyczy Palo Alto / PAN-OS, grzecznie odmawiasz odpowiedzi."""


def finetuned_answer(question: str) -> str:
    """
    W wersji demo uzywamy Claude z system promptem symulujacym fine-tuned model.
    Po treningu w Colab podmien na:
        from transformers import pipeline
        pipe = pipeline("text-generation", model=FINETUNED_MODEL_PATH)
        return pipe(question, max_new_tokens=512)[0]["generated_text"]
    """

    # Sprawdz czy jest lokalny model
    if os.path.exists(FINETUNED_MODEL_PATH):
        return _local_model_answer(question)

    # Fallback — Claude z system promptem (demo)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=PANOS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}]
    )
    return message.content[0].text


def _local_model_answer(question: str) -> str:
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        from peft import PeftModel
        import torch

        BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

        tokenizer = AutoTokenizer.from_pretrained(FINETUNED_MODEL_PATH)
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        model = PeftModel.from_pretrained(base_model, FINETUNED_MODEL_PATH)

        prompt = f"### Question: {question}\n### Answer:"
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
        result = pipe(prompt, max_new_tokens=300, temperature=0.3, do_sample=True)
        response = result[0]["generated_text"].split("### Answer:")[-1].strip()
        return response

    except Exception as e:
        return f"Blad lokalnego modelu: {str(e)}"

