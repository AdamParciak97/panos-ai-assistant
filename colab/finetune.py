# =============================================================================
# PAN-OS AI Assistant — Fine-tuning Notebook (uruchom w Google Colab)
# =============================================================================
# Instrukcja:
# 1. Otwórz Google Colab: https://colab.research.google.com
# 2. Zmień runtime na GPU: Runtime → Change runtime type → T4 GPU
# 3. Wklej ten kod do komórek i uruchom po kolei
# =============================================================================

# ── KOMÓRKA 1: Instalacja ────────────────────────────────────────────────────
CELL_1 = """
!pip install transformers datasets peft accelerate bitsandbytes -q
!pip install torch torchvision torchaudio -q
"""

# ── KOMÓRKA 2: Dane treningowe ───────────────────────────────────────────────
CELL_2 = """
import json

# Syntetyczne dane Q&A o PAN-OS
training_data = [
    {"question": "Jak skonfigurowac Security Policy w PAN-OS?",
     "answer": "Security Policy konfiguruje sie w Policies > Security. Kliknij Add, uzupelnij: Name, From/To (strefy), Source/Destination (IP), Application (App-ID), Service (porty), Action (allow/deny). Wazna kolejnosc regul — PAN-OS przetwarza od gory."},

    {"question": "Co to jest App-ID w Palo Alto?",
     "answer": "App-ID to technologia identyfikacji aplikacji niezalezna od portu i protokolu. Uzywa sygnatur, dekodowania protokolow i heurystyk. Dziala w warstwie 7. Baza jest aktualizowana przez content updates co tydzien."},

    {"question": "Jak dziala WildFire?",
     "answer": "WildFire to cloudowy sandboxing. Nieznane pliki sa wysylane do chmury Palo Alto, analizowane w izolowanym srodowisku (Windows/Linux/Android). Werdykt (benign/malicious/grayware) jest udostepniany wszystkim subskrybentom w ciagu 5 minut."},

    {"question": "Jak skonfigurowac NAT w PAN-OS?",
     "answer": "NAT konfiguruje sie w Policies > NAT. Source NAT (SNAT): maskarada IP wychodzacego. Destination NAT (DNAT): przekierowanie do wewnetrznego serwera. NAT jest przetwarzany PRZED Security Policy. Typ translacji: Dynamic IP and Port (wielu uzytkownicy > 1 IP), Static IP (1:1)."},

    {"question": "Czym roznia sie strefy Layer 2 i Layer 3?",
     "answer": "Layer 3 zone: interfejs ma IP, routing jest aktywny, PAN-OS jest bramka. Layer 2 zone: PAN-OS pracuje jako switch, brak routingu miedzy VLAN. Virtual Wire zone: transparent mode, PAN-OS niewidoczny w topologii, brak IP na interfejsach."},

    {"question": "Jak wlaczyc SSL Inspection?",
     "answer": "SSL Inspection wymaga: 1) Certyfikatu CA (wlasnego lub zakupionego) wgranego w Device > Certificate Management. 2) SSL/TLS Service Profile w Objects. 3) Decryption Policy w Policies > Decryption: from/to strefy, action=decrypt, SSL Forward Proxy dla ruchu wychodzacego."},

    {"question": "Jak sprawdzic logi na Palo Alto?",
     "answer": "Logi dostepne w Monitor > Logs: Traffic (ruch), Threat (zagrozenia), URL Filtering, WildFire, System, Configuration. Filtrowanie przez query builder lub recznie: (addr.src in 192.168.1.0/24) and (port.dst eq 443). Eksport do CSV lub forwarding do Syslog/Panorama."},

    {"question": "Co to jest Panorama?",
     "answer": "Panorama to centralne narzedzie zarzadzania wieloma firewallami Palo Alto. Funkcje: zarzadzanie politykami (Device Groups), konfiguracja urzadzen (Templates), zbieranie i przeszukiwanie logow (Log Collectors), generowanie raportow. Licencja wymagana oddzielnie."},

    {"question": "Jak skonfigurowac HA (High Availability)?",
     "answer": "HA konfiguruje sie w Device > High Availability. Tryby: Active/Passive (jeden aktywny, jeden standby), Active/Active (oba aktywne, load balancing). Wymaga: HA1 link (heartbeat/config sync), HA2 link (session sync), HA3 (packet forwarding w A/A). Oba urzadzenia musza miec te sama wersje PAN-OS."},

    {"question": "Jak uzywac API PAN-OS?",
     "answer": "PAN-OS XML API: GET https://firewall/api/?type=keygen&user=admin&password=xxx > zwraca API key. Komendy: type=config (konfiguracja), type=op (operational), type=log (logi), type=commit (commit). Przyklad: GET /api/?type=op&cmd=<show><system><info></info></system></show>&key=APIKEY. Odpowiedz w XML."},

    {"question": "Czym jest Threat Prevention w PAN-OS?",
     "answer": "Threat Prevention to modul IPS/IDS zawierajacy: Vulnerability Protection Profile (blokuje exploity, CVE), Anti-Spyware Profile (wykrywa C2, DNS sinkhole), Antivirus Profile (sygnatury malware). Profile przypisuje sie do Security Policy. Wymagana licencja Threat Prevention."},

    {"question": "Jak skonfigurowac GlobalProtect VPN?",
     "answer": "GlobalProtect wymaga: 1) Portal — urzadzenie do autentykacji uzytkownikow (Device > GlobalProtect > Portals). 2) Gateway — punkt koncentracji VPN (Device > GlobalProtect > Gateways). 3) Tunele IPsec lub SSL. 4) Klient GlobalProtect na stacji roboczej. Autentykacja: LDAP/AD, certyfikaty, MFA."},

    {"question": "Jak zrobic backup konfiguracji?",
     "answer": "Backup przez GUI: Device > Setup > Operations > Export Named Configuration Snapshot. Backup przez API: GET /api/?type=export&category=configuration&key=APIKEY. Automatyczny backup: Panorama > Scheduled Config Export. Wersje konfiguracji widoczne w Device > Setup > Operations > Saved Configurations."},

    {"question": "Co to jest Security Profile i jak go uzyc?",
     "answer": "Security Profile to zbior ustawien inspekcji: Antivirus, Anti-Spyware, Vulnerability Protection, URL Filtering, File Blocking, WildFire Analysis, DoS Protection. Profile tworzy sie w Objects > Security Profiles. Nastepnie przypisuje do reguly w Security Policy w zakladce Actions > Profile Setting."},

    {"question": "Jak skonfigurowac routing dynamiczny OSPF?",
     "answer": "OSPF konfiguruje sie w Network > Virtual Routers > OSPF. Kroki: 1) Wlacz OSPF, podaj Router ID. 2) Dodaj Area (type: backbone=0.0.0.0, stub, NSSA). 3) Dodaj interfejsy do Area z odpowiednim typem (p2p, broadcast). 4) Ustaw redistribution jesli potrzeba. 5) Commit. Weryfikacja: show routing protocol ospf neighbor."},
]

# Zapisz dane treningowe
with open('panos_training_data.jsonl', 'w', encoding='utf-8') as f:
    for item in training_data:
        f.write(json.dumps({
            "text": f"### Question: {item['question']}\\n### Answer: {item['answer']}"
        }, ensure_ascii=False) + "\\n")

print(f"Zapisano {len(training_data)} przykladow treningowych")
"""

# ── KOMÓRKA 3: Fine-tuning z LoRA ────────────────────────────────────────────
CELL_3 = """
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
import torch

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Maly model, dziala na Colab T4
OUTPUT_DIR = "./panos-finetuned"

print("Ladowanie tokenizera i modelu...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Konfiguracja LoRA (Parameter-Efficient Fine-Tuning)
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,                    # Rank — im wyzszy tym wiecej parametrow
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Zaladuj dane
dataset = load_dataset("text", data_files={"train": "panos_training_data.jsonl"})

def tokenize(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=512,
        padding="max_length"
    )

tokenized = dataset["train"].map(tokenize, batched=True)
tokenized = tokenized.remove_columns(["text"])
tokenized = tokenized.rename_column("input_ids", "input_ids")

print("Dataset gotowy:", tokenized)
"""

# ── KOMÓRKA 4: Trening ───────────────────────────────────────────────────────
CELL_4 = """
from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    warmup_steps=10,
    logging_steps=10,
    save_steps=50,
    learning_rate=2e-4,
    fp16=True,
    optim="adamw_torch",
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

print("Rozpoczynam trening...")
trainer.train()
print("Trening zakonczony!")
"""

# ── KOMÓRKA 5: Zapisz i pobierz model ────────────────────────────────────────
CELL_5 = """
# Zapisz model
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Model zapisany w {OUTPUT_DIR}")

# Spakuj do ZIP i pobierz
import shutil
shutil.make_archive('panos-finetuned', 'zip', OUTPUT_DIR)
from google.colab import files
files.download('panos-finetuned.zip')
print("Pobieranie modelu...")
"""

# ── KOMÓRKA 6: Test modelu ───────────────────────────────────────────────────
CELL_6 = """
from transformers import pipeline

pipe = pipeline("text-generation", model=OUTPUT_DIR, tokenizer=OUTPUT_DIR,
                device_map="auto", torch_dtype=torch.float16)

test_questions = [
    "Jak skonfigurowac Security Policy w PAN-OS?",
    "Co to jest App-ID?",
    "Jak wlaczyc WildFire?",
]

for q in test_questions:
    prompt = f"### Question: {q}\\n### Answer:"
    result = pipe(prompt, max_new_tokens=200, temperature=0.3, do_sample=True)
    answer = result[0]["generated_text"].split("### Answer:")[-1].strip()
    print(f"Q: {q}")
    print(f"A: {answer}")
    print("-" * 60)
"""

# Wyswietl instrukcje
print("=" * 70)
print("INSTRUKCJA URUCHOMIENIA W GOOGLE COLAB")
print("=" * 70)
print()
print("1. Otworz: https://colab.research.google.com")
print("2. File > New Notebook")
print("3. Runtime > Change runtime type > GPU (T4)")
print("4. Skopiuj i uruchom kazda CELL po kolei:")
print()
for i, cell in enumerate([CELL_1, CELL_2, CELL_3, CELL_4, CELL_5, CELL_6], 1):
    print(f"{'='*60}")
    print(f"CELL {i}:")
    print(cell)
print()
print("5. Po zakonczeniu pobierz plik: panos-finetuned.zip")
print("6. Rozpakuj do: backend/models/panos-finetuned/")
print("7. Ustaw w .env: FINETUNED_MODEL_PATH=./models/panos-finetuned")
