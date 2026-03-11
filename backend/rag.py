import os
import json
from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from anthropic import Anthropic

client = Anthropic(timeout=120.0)

EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DB_PATH = "./vectordb"

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
vectorstore = None


def load_vectorstore():
    global vectorstore
    if os.path.exists(VECTOR_DB_PATH):
        vectorstore = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
        print(f"Zaladowano vectorstore z {VECTOR_DB_PATH}")
    else:
        _create_default_vectorstore()


def _create_default_vectorstore():
    global vectorstore
    # Syntetyczne dane o PAN-OS gdy brak PDFów
    default_docs = [
        "Palo Alto Networks PAN-OS to system operacyjny Next-Generation Firewall. Obsługuje App-ID do identyfikacji aplikacji, User-ID do mapowania użytkowników, Content-ID do inspekcji treści.",
        "Security Policy w PAN-OS definiuje reguły ruchu sieciowego. Każda reguła zawiera: from/to (strefy), source/destination (adresy IP), application (App-ID), service (porty), action (allow/deny/drop).",
        "Zones w PAN-OS dzielą sieć na segmenty bezpieczeństwa. Typy stref: Layer 3, Layer 2, Virtual Wire, TAP, Tunnel. Ruch między strefami jest kontrolowany przez Security Policy.",
        "App-ID w PAN-OS identyfikuje aplikacje niezależnie od portu i protokołu. Używa sygnatur, dekodowania protokołów i heurystyk. Baza App-ID jest aktualizowana przez content updates.",
        "NAT Policy w PAN-OS konfiguruje translację adresów. Typy NAT: Source NAT (SNAT), Destination NAT (DNAT), Static NAT. NAT jest przetwarzany przed Security Policy.",
        "Threat Prevention w PAN-OS to moduł IPS/IDS. Zawiera: Vulnerability Protection (ochrona przed exploitami), Anti-Spyware (wykrywanie C2), Antivirus (sygnatury złośliwego oprogramowania).",
        "WildFire to sandboxing service Palo Alto Networks. Analizuje nieznane pliki w izolowanym środowisku. Wyniki analizy są udostępniane wszystkim subskrybentom w ciągu 5 minut.",
        "GlobalProtect to klient VPN Palo Alto Networks. Obsługuje: SSL VPN, IPsec VPN, always-on VPN, pre-logon. Gateway i Portal to dwa komponenty architektury GlobalProtect.",
        "Panorama to centralne narzędzie zarządzania firewallami Palo Alto. Umożliwia: zarządzanie politykami, zbieranie logów, generowanie raportów, wdrażanie konfiguracji na wielu urządzeniach.",
        "High Availability (HA) w PAN-OS zapewnia redundancję. Tryby HA: Active/Passive (jeden urządzenie aktywne), Active/Active (oba aktywne). Synchronizacja stanu sesji przez HA link.",
        "Interfejsy w PAN-OS: Physical (Ethernet), Logical (VLAN, Loopback, Tunnel, AE). Każdy interfejs przypisany do strefy bezpieczeństwa. LACP/802.3ad dla agregacji łączy.",
        "Routing w PAN-OS: Virtual Router obsługuje routing statyczny i dynamiczny (OSPF, BGP, RIP). Policy-Based Forwarding (PBF) umożliwia routing oparty na politykach.",
        "Certyfikaty SSL i inspekcja TLS w PAN-OS: SSL Forward Proxy (dla ruchu wychodzącego), SSL Inbound Inspection (dla ruchu przychodzącego). Wymaga instalacji certyfikatu CA.",
        "Logi w PAN-OS: Traffic, Threat, URL Filtering, WildFire, Authentication, System, Configuration, HIP Match. Forwarding logów do Syslog, SNMP, Email, Panorama.",
        "API PAN-OS umożliwia automatyzację zarządzania. Typy API: XML API (REST-like), REST API. Autentykacja przez API key lub OAuth. Endpointy: /api/?type=config, /api/?type=log.",
    ]

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    from langchain_core.documents import Document
    docs = [Document(page_content=text, metadata={"source": "PAN-OS Knowledge Base", "page": i})
            for i, text in enumerate(default_docs)]

    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(VECTOR_DB_PATH)
    print("Stworzono domyslny vectorstore z syntetycznymi danymi PAN-OS")


def add_pdf_to_vectorstore(file_path: str) -> int:
    global vectorstore
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(pages)

    if vectorstore is None:
        vectorstore = FAISS.from_documents(chunks, embeddings)
    else:
        vectorstore.add_documents(chunks)

    vectorstore.save_local(VECTOR_DB_PATH)
    return len(chunks)


def rag_answer(question: str) -> Tuple[str, List[str]]:
    if vectorstore is None:
        load_vectorstore()

    docs = vectorstore.similarity_search(question, k=4)
    context = "\n\n".join([f"[{d.metadata.get('source','Doc')} p.{d.metadata.get('page',0)}]\n{d.page_content}"
                           for d in docs])
    sources = list(set([d.metadata.get('source', 'Unknown') for d in docs]))

    prompt = f"""Jestes ekspertem Palo Alto Networks PAN-OS. Odpowiedz na pytanie uzywajac TYLKO podanego kontekstu.
Jezeli kontekst nie zawiera odpowiedzi, powiedz to wprost.

KONTEKST:
{context}

PYTANIE: {question}

Odpowiedz konkretnie i technicznie. Jezeli to konfiguracja, podaj przyklad komendy lub kroki."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text, sources


# Zaladuj vectorstore przy starcie
load_vectorstore()
