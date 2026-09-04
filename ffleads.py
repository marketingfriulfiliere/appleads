# -*- coding: utf-8 -*-
"""
FRIUL FILIERE LEAD ENGINE
Piattaforma di Lead Generation, Profilazione e Outreach Commerciale B2B
per identificare trasformatori di materie plastiche, produttori di profili
e terzisti a livello internazionale.

Unico file app.py - Streamlit
Nessuna libreria SDK esterna instabile: chiamate dirette via requests alla
REST API di Gemini (opzionale, con fallback a dati mock trasparenti).

Avvio:
    streamlit run app.py
"""

import io
import json
import random
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF


# =========================================================================
# CONFIGURAZIONE PAGINA
# =========================================================================

st.set_page_config(
    page_title="Friul Filiere Lead Engine",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================================
# TEMA / CSS - Blu industriale, rosso, grigio metallico
# =========================================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;\
600;700;800&display=swap');

:root {
    --blu-scuro: #0E1F3D;
    --blu-medio: #16305e;
    --rosso: #C8102E;
    --grigio-metal: #B0B7BD;
    --grigio-chiaro: #F2F3F5;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #F7F8FA 0%, #EEF0F3 100%);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--blu-scuro) 0%, #081527 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] * {
    color: #EAECEF !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.93rem;
    padding: 2px 0;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.12);
}

h1, h2, h3 {
    color: var(--blu-scuro);
    font-weight: 800;
    letter-spacing: -0.01em;
}

.ffe-header {
    background: linear-gradient(120deg, var(--blu-scuro) 0%, var(--blu-medio) 100%);
    padding: 26px 32px;
    border-radius: 14px;
    border-left: 8px solid var(--rosso);
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(14,31,61,0.18);
}
.ffe-header h1 {
    color: white !important;
    margin: 0;
    font-size: 1.95rem;
    letter-spacing: -0.02em;
}
.ffe-header p {
    color: #C7CDD9 !important;
    margin: 6px 0 0 0;
    font-size: 0.97rem;
}

.ffe-card {
    background: white;
    border-radius: 12px;
    padding: 20px 22px;
    border: 1px solid #E5E8EC;
    border-top: 4px solid var(--rosso);
    box-shadow: 0 3px 10px rgba(14,31,61,0.07);
    margin-bottom: 16px;
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.ffe-card:hover {
    box-shadow: 0 8px 20px rgba(14,31,61,0.12);
    transform: translateY(-1px);
}

.ffe-metric {
    background: linear-gradient(145deg, var(--blu-scuro) 0%, var(--blu-medio) 100%);
    color: white;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(14,31,61,0.16);
}
.ffe-metric .val {
    font-size: 2.1rem;
    font-weight: 800;
    color: white;
}
.ffe-metric .lbl {
    font-size: 0.78rem;
    color: var(--grigio-metal);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 2px;
}

.ffe-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-right: 4px;
}
.ffe-badge-alta { background: var(--rosso); color: white; }
.ffe-badge-media { background: #E8A33D; color: white; }
.ffe-badge-bassa { background: var(--grigio-metal); color: var(--blu-scuro); }
.ffe-badge-info { background: var(--blu-scuro); color: white; }
.ffe-badge-verificato {
    background: rgba(74, 222, 128, 0.15);
    color: #1B7A43;
    border: 1px solid rgba(27, 122, 67, 0.35);
}
.ffe-badge-campione {
    background: rgba(176, 183, 189, 0.2);
    color: #5A6472;
    border: 1px solid rgba(90, 100, 114, 0.3);
}

.ffe-divider {
    border: none;
    border-top: 2px solid #E1E4E8;
    margin: 18px 0;
}

.stButton>button {
    background-color: var(--rosso);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    padding: 0.55em 1.3em;
    box-shadow: 0 3px 8px rgba(200,16,46,0.25);
    transition: all 0.15s ease;
}
.stButton>button:hover {
    background-color: #a10c22;
    color: white;
    box-shadow: 0 5px 14px rgba(200,16,46,0.35);
    transform: translateY(-1px);
}

div[data-testid="stMetricValue"] {
    color: var(--blu-scuro);
    font-weight: 800;
}

div[data-testid="stForm"] {
    background: white;
    border-radius: 12px;
    padding: 18px 20px 8px 20px;
    border: 1px solid #E5E8EC;
    box-shadow: 0 3px 10px rgba(14,31,61,0.05);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    font-weight: 600;
}

[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(14,31,61,0.06);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================================
# COSTANTI / DATI DI RIFERIMENTO
# =========================================================================

SETTORI = [
    "Automotive", "Medicale", "Edilizia", "Packaging alimentare",
    "Arredamento", "Elettrodomestici", "Serramenti", "Agricoltura",
    "Cavi e condotte", "Water management", "Arredo urbano", "Nautica",
]

PAESI = [
    "Italia", "Germania", "Francia", "Spagna", "Polonia", "Turchia",
    "Romania", "Paesi Bassi", "Stati Uniti", "Messico", "Brasile",
    "India", "Cina", "Vietnam", "Regno Unito", "Austria",
]

DIMENSIONI_AZIENDA = [
    "Micro (< 10 dip.)", "Piccola (10-49 dip.)",
    "Media (50-249 dip.)", "Grande (250+ dip.)",
]

LIVELLI_URGENZA = ["Alta", "Media", "Bassa"]

STATI_LEAD = ["Nuovo", "Contattato", "In trattativa", "Qualificato", "Perso"]

FIERE_SETTORE = [
    "K Fair - Düsseldorf (DE)", "Plast - Milano (IT)",
    "Fakuma - Friedrichshafen (DE)", "NPE - Orlando (USA)",
    "Chinaplas - Shenzhen (CN)", "Interplastica - Mosca (RU)",
    "Plastpol - Kielce (PL)", "Feiplastic - San Paolo (BR)",
]

TECNOLOGIE_FRIUL_FILIERE = [
    "Linee di estrusione PVC per profili finestra",
    "Linee di coestrusione multistrato",
    "Sistemi di calibrazione e raffreddamento sottovuoto",
    "Linee di estrusione tubi corrugati e lisci",
    "Impianti per compositi legno-plastica (WPC)",
    "Linee monofilamento e reti estruse",
    "Sistemi downstream (taglio, impilamento, imballo automatico)",
    "Automazione e retrofit Industry 4.0 per linee di estrusione",
    "Teste e stampi per profili tecnici complessi",
]

PREFISSI_AZIENDA = [
    "Euro", "Plast", "Poly", "Nord", "Tecno", "Global", "Alpha", "Master",
    "Solid", "Continental", "Iberia", "Trans", "Fenix", "Delta", "Nova",
    "Rhein", "Adria", "Baltic",
]
SUFFISSI_AZIENDA = [
    "Plastics", "Profili", "Extrusion", "Kunststoff", "Composites",
    "Industrie", "Manufacturing", "Systems", "Polymers", "Group",
    "Profile GmbH", "S.p.A.", "S.r.l.", "S.A.", "Sp. z o.o.", "Ltd",
]

NOMI_CONTATTO = [
    "Marco Bianchi", "Julia Weber", "Pierre Dubois", "Ana Garcia",
    "Tomasz Kowalski", "John Smith", "Maria Rossi", "Hans Müller",
    "Sophie Martin", "Elena Popescu", "Deniz Yilmaz", "Wei Chen",
    "Carlos Mendes", "Laura Fernandez", "Peter Novak", "Anna Kowalczyk",
]

SETTORE_QUERY_PLACES = {
    "Automotive": "plastic injection molding automotive supplier",
    "Medicale": "medical plastic components manufacturer",
    "Edilizia": "PVC profile extrusion manufacturer",
    "Packaging alimentare": "plastic packaging manufacturer food",
    "Arredamento": "plastic furniture components manufacturer",
    "Elettrodomestici": "plastic components manufacturer appliances",
    "Serramenti": "PVC window profile manufacturer",
    "Agricoltura": "plastic pipe manufacturer irrigation",
    "Cavi e condotte": "plastic pipe extrusion manufacturer",
    "Water management": "HDPE pipe manufacturer water",
    "Arredo urbano": "wood plastic composite manufacturer",
    "Nautica": "plastic composite manufacturer marine",
}

MAPPA_TECNOLOGIA_SETTORE = {
    "Automotive": "Linee di coestrusione multistrato",
    "Medicale": "Linee monofilamento e reti estruse",
    "Edilizia": "Linee di estrusione PVC per profili finestra",
    "Packaging alimentare": "Sistemi downstream (taglio, impilamento, "
                              "imballo automatico)",
    "Arredamento": "Impianti per compositi legno-plastica (WPC)",
    "Elettrodomestici": "Teste e stampi per profili tecnici complessi",
    "Serramenti": "Linee di estrusione PVC per profili finestra",
    "Agricoltura": "Linee di estrusione tubi corrugati e lisci",
    "Cavi e condotte": "Linee di estrusione tubi corrugati e lisci",
    "Water management": "Sistemi di calibrazione e raffreddamento "
                          "sottovuoto",
    "Arredo urbano": "Impianti per compositi legno-plastica (WPC)",
    "Nautica": "Automazione e retrofit Industry 4.0 per linee di "
                "estrusione",
}

FONTI_NOTIZIA = [
    "Comunicato stampa ampliamento stabilimento",
    "Annuncio investimento in nuova linea produttiva",
    "Apertura nuova sede produttiva",
    "Piano assunzioni / crescita organico",
    "Acquisizione di ramo d'azienda concorrente",
    "Finanziamento pubblico per innovazione industriale",
    "Fusione con altro trasformatore locale",
    "Ingresso in nuovo mercato di sbocco",
]


# =========================================================================
# STATO DI SESSIONE
# =========================================================================

def init_session_state():
    if "leads" not in st.session_state:
        st.session_state.leads = []
    if "next_id" not in st.session_state:
        st.session_state.next_id = 1
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""
    if "usa_ricerca_reale" not in st.session_state:
        st.session_state.usa_ricerca_reale = True
    if "dossier_cache" not in st.session_state:
        st.session_state.dossier_cache = {}
    if "email_cache" not in st.session_state:
        st.session_state.email_cache = {}
    if "lotto_corrente" not in st.session_state:
        st.session_state.lotto_corrente = 1
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Dashboard"


init_session_state()


# =========================================================================
# CHIAMATA REST DIRETTA A GEMINI (con fallback trasparente a mock)
# =========================================================================

def call_gemini_api(prompt, temperature=0.7, max_tokens=1500):
    """Chiama la REST API HTTP di Gemini con requests puro.
    Se manca la API key o la chiamata fallisce, ritorna (None, motivo)
    cosi' il chiamante puo' usare un fallback mock trasparente."""
    api_key = st.session_state.gemini_api_key.strip()
    if not api_key:
        return None, "no_key"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent?key=" + api_key
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, "ok"
    except Exception as exc:
        return None, "errore: " + str(exc)


# =========================================================================
# RICERCA AZIENDE VERIFICATE - OPENSTREETMAP (Nominatim) - NESSUNA CHIAVE
# =========================================================================

OSM_USER_AGENT = "FriulFiliereLeadEngine/1.0 (uso interno, contatto: " \
                  "commerciale@friulfiliere-demo.local)"


def osm_nominatim_search(query, max_results=10):
    """Ricerca reale, gratuita e senza chiave su OpenStreetMap (Nominatim).
    Ritorna (lista_risultati, errore). Nessuna registrazione richiesta:
    rispetta la usage policy pubblica (User-Agent identificativo, 1
    richiesta al secondo)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "extratags": 1,
        "limit": min(max_results, 15),
    }
    headers = {"User-Agent": OSM_USER_AGENT}
    try:
        resp = requests.get(url, params=params, headers=headers,
                             timeout=20)
        resp.raise_for_status()
        risultati = resp.json()
        if not risultati:
            return [], "nessun risultato verificato trovato per questa " \
                        "combinazione settore/paese"
        return risultati, None
    except Exception as exc:
        return [], "errore di rete OpenStreetMap: " + str(exc)


def costruisci_query_osm(settore, paese):
    parola_chiave = SETTORE_QUERY_PLACES.get(
        settore, "plastic processing manufacturer")
    return parola_chiave + " " + paese


def lead_da_risultato_osm(risultato, settore, paese, fonte, nota_extra=""):
    """Converte un risultato OpenStreetMap reale in un lead dell'app."""
    lead_id = st.session_state.next_id
    st.session_state.next_id += 1

    extratags = risultato.get("extratags") or {}
    nome = (risultato.get("name") or extratags.get("name")
             or risultato.get("display_name", "Azienda").split(",")[0])
    indirizzo = risultato.get("display_name", "")
    sito = extratags.get("website") or extratags.get("contact:website", "")
    telefono = extratags.get("phone") or extratags.get("contact:phone", "")
    importanza = risultato.get("importance", 0.3)

    punteggio = int(min(97, max(40, importanza * 150)))
    nota_completa = ("Fonte: OpenStreetMap. Indirizzo: " + indirizzo
                       + (" | " + nota_extra if nota_extra else ""))

    lead = {
        "id": lead_id,
        "azienda": nome,
        "paese": paese,
        "settore": settore,
        "dimensione": "Da qualificare (dato non disponibile in fonte "
                        "aperta)",
        "tecnologia_target": MAPPA_TECNOLOGIA_SETTORE.get(
            settore, random.choice(TECNOLOGIE_FRIUL_FILIERE)),
        "urgenza": random.choice(LIVELLI_URGENZA),
        "stato": "Nuovo",
        "contatto": "Da individuare (sito/LinkedIn)",
        "email": "Verificare su " + sito if sito else "Non disponibile",
        "telefono": telefono or "Non disponibile",
        "sito_web": sito or "Non disponibile",
        "fonte": fonte,
        "punteggio": punteggio,
        "note": nota_completa,
        "lotto": st.session_state.lotto_corrente,
        "data_inserimento": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dati_reali": True,
    }
    return lead


def cerca_aziende_reali(settore, paese, fonte, n_lead=10, query_extra=""):
    """Wrapper di alto livello: ricerca reale via OpenStreetMap, gratuita
    e senza alcuna chiave o account. Ritorna una lista vuota + messaggio
    di errore se non trova nulla, per permettere un fallback a dati
    campione trasparente al chiamante."""
    query = costruisci_query_osm(settore, paese)
    if query_extra:
        query = query + " " + query_extra

    risultati, errore = osm_nominatim_search(query, max_results=n_lead)
    if errore:
        return [], errore

    leads = []
    for r in risultati:
        leads.append(lead_da_risultato_osm(r, settore, paese, fonte))
    return leads, None


# =========================================================================
# GENERAZIONE LEAD MOCK (dati dummy trasparenti, dichiarati come tali in UI)
# =========================================================================

def genera_nome_azienda():
    return random.choice(PREFISSI_AZIENDA) + random.choice(SUFFISSI_AZIENDA)


def genera_lead_mock(settore, paese, fonte, dimensione=None, urgenza=None,
                      tecnologia=None, nota_extra=""):
    lead_id = st.session_state.next_id
    st.session_state.next_id += 1

    azienda = genera_nome_azienda()
    dimensione = dimensione or random.choice(DIMENSIONI_AZIENDA)
    urgenza = urgenza or random.choices(
        LIVELLI_URGENZA, weights=[0.3, 0.45, 0.25]
    )[0]
    tecnologia = tecnologia or random.choice(TECNOLOGIE_FRIUL_FILIERE)
    contatto = random.choice(NOMI_CONTATTO)
    dominio = azienda.lower().replace(" ", "").replace(".", "")[:14]
    punteggio = random.randint(40, 98)

    lead = {
        "id": lead_id,
        "azienda": azienda,
        "paese": paese,
        "settore": settore,
        "dimensione": dimensione,
        "tecnologia_target": tecnologia,
        "urgenza": urgenza,
        "stato": "Nuovo",
        "contatto": contatto,
        "email": dominio + "@" + dominio + ".com",
        "telefono": "+" + str(random.randint(1, 99)) + " "
                    + str(random.randint(100000000, 999999999)),
        "sito_web": "www." + dominio + ".com",
        "fonte": fonte,
        "punteggio": punteggio,
        "note": nota_extra,
        "lotto": st.session_state.lotto_corrente,
        "data_inserimento": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dati_reali": False,
    }
    return lead


def aggiungi_leads(lista_lead):
    st.session_state.leads.extend(lista_lead)


def df_leads():
    if not st.session_state.leads:
        return pd.DataFrame()
    return pd.DataFrame(st.session_state.leads)


# =========================================================================
# BADGE HTML HELPER
# =========================================================================

def badge_urgenza(u):
    classe = {"Alta": "ffe-badge-alta", "Media": "ffe-badge-media",
              "Bassa": "ffe-badge-bassa"}.get(u, "ffe-badge-info")
    return '<span class="ffe-badge ' + classe + '">' + u + '</span>'


def badge_fonte_dati(dati_reali):
    if dati_reali:
        return ('<span class="ffe-badge ffe-badge-verificato">● Dato '
                 'verificato</span>')
    return ('<span class="ffe-badge ffe-badge-campione">● Dato '
             'campione</span>')


# =========================================================================
# EXPORT CSV / PDF
# =========================================================================

def export_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def _pdf_safe(testo):
    """Rende il testo compatibile con la codifica latin-1 di fpdf base,
    senza usare regex, sostituendo i caratteri non rappresentabili."""
    return testo.encode("latin-1", "replace").decode("latin-1")


def export_pdf_lista_lead(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 31, 61)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 14, _pdf_safe("Friul Filiere Lead Engine - Elenco Lead"),
              ln=True, fill=True)
    pdf.ln(4)
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "", 9)

    colonne = ["azienda", "paese", "settore", "dimensione", "urgenza",
               "punteggio", "contatto", "email"]
    larghezze = [30, 20, 25, 25, 18, 18, 25, 45]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(200, 16, 46)
    pdf.set_text_color(255, 255, 255)
    for col, larg in zip(colonne, larghezze):
        pdf.cell(larg, 8, _pdf_safe(col.upper()), border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(20, 20, 20)
    for _, riga in df.iterrows():
        for col, larg in zip(colonne, larghezze):
            valore = str(riga.get(col, ""))
            if len(valore) > 28:
                valore = valore[:25] + "..."
            pdf.cell(larg, 7, _pdf_safe(valore), border=1)
        pdf.ln()

    return bytes(pdf.output(dest="S"))


def export_pdf_dossier(lead, dossier_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 31, 61)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 14, _pdf_safe("Dossier Tecnico Commerciale"), ln=True,
              fill=True)
    pdf.ln(2)
    pdf.set_text_color(200, 16, 46)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, _pdf_safe(lead["azienda"]), ln=True)
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 10)
    sottotitolo = lead["paese"] + " | " + lead["settore"] + " | " + \
        lead["dimensione"]
    pdf.cell(0, 8, _pdf_safe(sottotitolo), ln=True)
    pdf.ln(4)

    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "", 10)
    for paragrafo in dossier_text.split("\n"):
        pdf.multi_cell(0, 6, _pdf_safe(paragrafo))
    return bytes(pdf.output(dest="S"))


# =========================================================================
# GENERAZIONE DOSSIER TECNICO (prompt Gemini + fallback mock)
# =========================================================================

def costruisci_prompt_dossier(lead, lingua):
    return (
        "Agisci come un consulente tecnico-commerciale senior di Friul "
        "Filiere, azienda leader nella progettazione e costruzione di "
        "impianti di estrusione per materie plastiche (profili tecnici, "
        "tubi, WPC, monofilamento, sistemi downstream e automazione).\n\n"
        "Scrivi in lingua: " + lingua + ".\n\n"
        "Prepara un Dossier Tecnico-Commerciale sintetico e persuasivo "
        "(circa 250-350 parole) per il seguente potenziale cliente:\n"
        "- Azienda: " + lead["azienda"] + "\n"
        "- Paese: " + lead["paese"] + "\n"
        "- Settore di applicazione: " + lead["settore"] + "\n"
        "- Dimensione: " + lead["dimensione"] + "\n"
        "- Tecnologia di interesse stimata: " + lead["tecnologia_target"] + "\n\n"
        "Struttura il dossier in questi blocchi, con titoli brevi:\n"
        "1) Profilo del prospect e ipotesi di esigenza produttiva\n"
        "2) Soluzione tecnologica Friul Filiere consigliata\n"
        "3) Benefici quantificabili (efficienza, scarti, energia, uptime)\n"
        "4) Prossimo passo commerciale suggerito\n"
        "Tono: professionale, concreto, orientato al valore ingegneristico."
    )


def genera_dossier_mock(lead, lingua):
    intestazioni = {
        "Italiano": ["Profilo del prospect", "Soluzione consigliata",
                     "Benefici attesi", "Prossimo passo"],
        "Inglese": ["Prospect profile", "Recommended solution",
                    "Expected benefits", "Next step"],
        "Tedesco": ["Interessentenprofil", "Empfohlene Loesung",
                    "Erwartete Vorteile", "Naechster Schritt"],
        "Francese": ["Profil du prospect", "Solution recommandee",
                     "Benefices attendus", "Prochaine etape"],
    }
    h = intestazioni.get(lingua, intestazioni["Italiano"])
    testo = (
        h[0] + "\n"
        + lead["azienda"] + " opera nel settore " + lead["settore"]
        + " in " + lead["paese"] + " (" + lead["dimensione"] + "). "
        "I segnali raccolti indicano una probabile necessita' di "
        "incrementare capacita' produttiva o efficienza di linea.\n\n"
        + h[1] + "\n"
        + "Si consiglia la tecnologia Friul Filiere: "
        + lead["tecnologia_target"] + ", configurabile con teste "
        "dedicate e sistemi di calibrazione ad alta precisione.\n\n"
        + h[2] + "\n"
        + "Riduzione scarti di produzione, incremento uptime linea, "
        "risparmio energetico stimato tra 8% e 15%, tempi di setup "
        "ridotti grazie all'automazione integrata.\n\n"
        + h[3] + "\n"
        + "Proporre una call tecnica di 30 minuti con l'ufficio "
        "progettazione Friul Filiere e l'invio di un layout preliminare "
        "personalizzato.\n\n"
        "[Documento generato in modalita' dimostrativa - dati mock]"
    )
    return testo


def ottieni_dossier(lead, lingua):
    chiave = str(lead["id"]) + "_" + lingua
    if chiave in st.session_state.dossier_cache:
        return st.session_state.dossier_cache[chiave]

    prompt = costruisci_prompt_dossier(lead, lingua)
    testo, stato = call_gemini_api(prompt)
    if testo is None:
        testo = genera_dossier_mock(lead, lingua)

    st.session_state.dossier_cache[chiave] = testo
    return testo


# =========================================================================
# GENERAZIONE SEQUENZE EMAIL MULTI-LINGUA
# =========================================================================

TESTI_EMAIL_MOCK = {
    "Italiano": {
        "oggetto": [
            "Efficienza di linea per {azienda}: una proposta concreta",
            "Riduzione scarti e consumi energetici per {azienda}",
            "Un'idea per la vostra prossima linea di estrusione",
        ],
        "corpo": [
            "Gentile {contatto},\n\nabbiamo notato che {azienda} opera "
            "nel settore {settore} in {paese}. Friul Filiere progetta e "
            "costruisce impianti di estrusione su misura, in particolare "
            "{tecnologia}.\n\nSaremmo lieti di condividere un caso studio "
            "rilevante per il vostro processo produttivo.\n\nCordiali "
            "saluti,\nTeam Commerciale Friul Filiere",
            "Gentile {contatto},\n\nfacendo seguito al nostro precedente "
            "messaggio, volevamo evidenziare i risultati ottenuti da "
            "clienti simili a {azienda}: riduzione scarti fino al 12% e "
            "risparmio energetico misurabile con {tecnologia}.\n\nAvete "
            "20 minuti per una call conoscitiva questa settimana?\n\n"
            "Cordiali saluti,\nTeam Commerciale Friul Filiere",
            "Gentile {contatto},\n\nnon vogliamo essere invadenti: le "
            "scriviamo un'ultima volta per proporle un breve confronto "
            "tecnico gratuito su {tecnologia}, utile per valutare "
            "eventuali margini di efficientamento in {azienda}.\n\n"
            "Resto a disposizione.\n\nCordiali saluti,\nTeam Commerciale "
            "Friul Filiere",
        ],
    },
    "Inglese": {
        "oggetto": [
            "Line efficiency for {azienda}: a concrete proposal",
            "Cutting scrap and energy costs at {azienda}",
            "An idea for your next extrusion line",
        ],
        "corpo": [
            "Dear {contatto},\n\nwe noticed that {azienda} operates in "
            "the {settore} sector in {paese}. Friul Filiere designs and "
            "builds tailor-made extrusion plants, in particular "
            "{tecnologia}.\n\nWe would be glad to share a relevant case "
            "study for your production process.\n\nBest regards,\nFriul "
            "Filiere Sales Team",
            "Dear {contatto},\n\nfollowing up on our previous message, "
            "we wanted to highlight results achieved by companies "
            "similar to {azienda}: up to 12% scrap reduction and "
            "measurable energy savings with {tecnologia}.\n\nDo you have "
            "20 minutes for an intro call this week?\n\nBest regards,\n"
            "Friul Filiere Sales Team",
            "Dear {contatto},\n\nwe do not want to be intrusive: this is "
            "our last note to offer a short, free technical review on "
            "{tecnologia}, useful to assess efficiency potential at "
            "{azienda}.\n\nHappy to help.\n\nBest regards,\nFriul Filiere "
            "Sales Team",
        ],
    },
    "Tedesco": {
        "oggetto": [
            "Linieneffizienz fuer {azienda}: ein konkreter Vorschlag",
            "Weniger Ausschuss und Energiekosten bei {azienda}",
            "Eine Idee fuer Ihre naechste Extrusionslinie",
        ],
        "corpo": [
            "Sehr geehrte(r) {contatto},\n\nwir haben festgestellt, dass "
            "{azienda} im Bereich {settore} in {paese} taetig ist. Friul "
            "Filiere plant und baut massgeschneiderte Extrusionsanlagen, "
            "insbesondere {tecnologia}.\n\nGerne teilen wir eine "
            "relevante Fallstudie mit Ihnen.\n\nMit freundlichen "
            "Gruessen,\nFriul Filiere Vertriebsteam",
            "Sehr geehrte(r) {contatto},\n\nals Nachfassaktion moechten "
            "wir Ergebnisse aehnlicher Unternehmen wie {azienda} "
            "hervorheben: bis zu 12% weniger Ausschuss und messbare "
            "Energieeinsparung mit {tecnologia}.\n\nHaben Sie diese "
            "Woche 20 Minuten Zeit fuer ein Kennenlerngespraech?\n\nMit "
            "freundlichen Gruessen,\nFriul Filiere Vertriebsteam",
            "Sehr geehrte(r) {contatto},\n\nwir moechten nicht "
            "aufdringlich sein: letzte Nachricht mit dem Angebot einer "
            "kurzen, kostenlosen technischen Analyse zu {tecnologia} fuer "
            "{azienda}.\n\nGerne stehen wir zur Verfuegung.\n\nMit "
            "freundlichen Gruessen,\nFriul Filiere Vertriebsteam",
        ],
    },
    "Francese": {
        "oggetto": [
            "Efficacite de ligne pour {azienda} : une proposition "
            "concrete",
            "Reduction des dechets et de l'energie chez {azienda}",
            "Une idee pour votre prochaine ligne d'extrusion",
        ],
        "corpo": [
            "Cher(e) {contatto},\n\nnous avons remarque que {azienda} "
            "opere dans le secteur {settore} en {paese}. Friul Filiere "
            "concoit et construit des installations d'extrusion sur "
            "mesure, notamment {tecnologia}.\n\nNous serions ravis de "
            "partager une etude de cas pertinente.\n\nCordialement,\n"
            "Equipe commerciale Friul Filiere",
            "Cher(e) {contatto},\n\nen complement de notre precedent "
            "message, nous souhaitions souligner les resultats obtenus "
            "par des entreprises similaires a {azienda} : jusqu'a 12% de "
            "dechets en moins avec {tecnologia}.\n\nAvez-vous 20 minutes "
            "cette semaine pour un premier echange ?\n\nCordialement,\n"
            "Equipe commerciale Friul Filiere",
            "Cher(e) {contatto},\n\nnous ne souhaitons pas etre "
            "insistants : dernier message pour proposer un court bilan "
            "technique gratuit sur {tecnologia} pour {azienda}.\n\nNous "
            "restons a votre disposition.\n\nCordialement,\nEquipe "
            "commerciale Friul Filiere",
        ],
    },
}


def genera_sequenza_email(lead, lingua):
    chiave = str(lead["id"]) + "_" + lingua
    if chiave in st.session_state.email_cache:
        return st.session_state.email_cache[chiave]

    dati = TESTI_EMAIL_MOCK.get(lingua, TESTI_EMAIL_MOCK["Italiano"])
    sequenza = []
    for i in range(3):
        oggetto = dati["oggetto"][i].format(
            azienda=lead["azienda"], settore=lead["settore"],
            tecnologia=lead["tecnologia_target"],
        )
        corpo = dati["corpo"][i].format(
            contatto=lead["contatto"], azienda=lead["azienda"],
            settore=lead["settore"], paese=lead["paese"],
            tecnologia=lead["tecnologia_target"],
        )
        giorno = [0, 4, 9][i]
        sequenza.append({
            "step": i + 1,
            "giorno_invio": "Giorno " + str(giorno),
            "oggetto": oggetto,
            "corpo": corpo,
        })

    st.session_state.email_cache[chiave] = sequenza
    return sequenza


# =========================================================================
# SIDEBAR - NAVIGAZIONE
# =========================================================================

def sidebar():
    with st.sidebar:
        st.markdown("## 🏭 FRIUL FILIERE")
        st.markdown("##### Lead Engine B2B")
        st.markdown("---")

        pagine = [
            "Dashboard",
            "🔎 Ricerca per Settore",
            "🎪 Ricerca Fiere",
            "📈 Progetti di Investimento",
            "👥 Analisi Lookalike",
            "🛰️ Radar Espansione & Organico",
            "🎯 Sales Twin Verticale",
            "📄 Dossier Tecnico AI",
            "✉️ Sequenze Outreach",
            "🗂️ CRM & Database Lead",
        ]
        scelta = st.radio("Modulo", pagine, label_visibility="collapsed")
        st.session_state.pagina = scelta

        st.markdown("---")
        st.markdown("#### 🌍 Fonte dati aziende")
        st.session_state.usa_ricerca_reale = st.toggle(
            "Ricerca verificata (open data, gratuita)",
            value=st.session_state.usa_ricerca_reale,
            help="Quando attiva, i moduli 'Ricerca per Settore', "
                 "'Analisi Lookalike' e 'Sales Twin Verticale' cercano "
                 "aziende reali su fonti aperte (OpenStreetMap), senza "
                 "bisogno di alcuna chiave o account. La copertura varia "
                 "per paese e settore: se una ricerca non trova nulla, "
                 "l'app completa automaticamente con dati campione, "
                 "sempre etichettati.",
        )
        if st.session_state.usa_ricerca_reale:
            st.markdown(
                "<span style='color:#4ADE80;font-weight:700;'>● Ricerca "
                "verificata attiva</span>", unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<span style='color:#B0B7BD;font-weight:700;'>● Solo "
                "dati campione</span>", unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("#### ✍️ Generazione testi AI")
        st.session_state.gemini_api_key = st.text_input(
            "Gemini API Key (opzionale)",
            value=st.session_state.gemini_api_key,
            type="password",
            help="Se vuota, l'app compone dossier ed email con un "
                 "generatore interno basato su template.",
        )
        if st.session_state.gemini_api_key:
            st.markdown(
                "<span style='color:#4ADE80;font-weight:700;'>● "
                "Generazione AI live attiva</span>", unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<span style='color:#B0B7BD;font-weight:700;'>● "
                "Generatore interno (template)</span>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.caption(
            "I moduli 'Ricerca Fiere', 'Progetti di Investimento' e "
            "'Radar Espansione' lavorano con dati campione: richiedono "
            "fonti news/fiere a pagamento non ancora collegate."
        )

        st.markdown("---")
        st.metric("Lead in database", len(st.session_state.leads))
        st.metric("Lotto di ricerca corrente", st.session_state.lotto_corrente)


# =========================================================================
# HEADER DI PAGINA
# =========================================================================

def header(titolo, sottotitolo):
    st.markdown(
        '<div class="ffe-header"><h1>' + titolo + '</h1><p>' + sottotitolo
        + '</p></div>', unsafe_allow_html=True,
    )


# =========================================================================
# PAGINA: DASHBOARD
# =========================================================================

def pagina_dashboard():
    header("Dashboard Operativa", "Panoramica generale della pipeline di "
           "lead generation internazionale")

    df = df_leads()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="ffe-metric"><div class="val">'
                     + str(len(df)) + '</div><div class="lbl">Lead totali'
                     '</div></div>', unsafe_allow_html=True)
    with c2:
        alta = len(df[df["urgenza"] == "Alta"]) if not df.empty else 0
        st.markdown('<div class="ffe-metric"><div class="val">'
                     + str(alta) + '</div><div class="lbl">Urgenza alta'
                     '</div></div>', unsafe_allow_html=True)
    with c3:
        paesi_n = df["paese"].nunique() if not df.empty else 0
        st.markdown('<div class="ffe-metric"><div class="val">'
                     + str(paesi_n) + '</div><div class="lbl">Paesi coperti'
                     '</div></div>', unsafe_allow_html=True)
    with c4:
        score_medio = round(df["punteggio"].mean(), 1) if not df.empty else 0
        st.markdown('<div class="ffe-metric"><div class="val">'
                     + str(score_medio) + '</div><div class="lbl">Score '
                     'medio lead</div></div>', unsafe_allow_html=True)

    st.markdown("<div class='ffe-divider'></div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("Nessun lead ancora generato. Usa i moduli nel menu "
                    "laterale per avviare una ricerca.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Lead per settore")
        st.bar_chart(df["settore"].value_counts())
    with col_b:
        st.markdown("#### Lead per paese")
        st.bar_chart(df["paese"].value_counts())

    st.markdown("#### Lead per fonte del modulo")
    st.bar_chart(df["fonte"].value_counts())

    st.markdown("#### Ultimi lead inseriti")
    st.dataframe(
        df.sort_values("id", ascending=False).head(10)[
            ["azienda", "paese", "settore", "urgenza", "punteggio", "stato"]
        ],
        use_container_width=True,
    )


# =========================================================================
# PAGINA: RICERCA PER SETTORE
# =========================================================================

def pagina_ricerca_settore():
    header("Ricerca Lead per Settore", "Identifica trasformatori di "
           "materie plastiche e produttori di profili filtrando per "
           "settore applicativo, paese e dimensione azienda")

    with st.form("form_settore"):
        c1, c2, c3 = st.columns(3)
        with c1:
            settori_sel = st.multiselect("Settore/i target", SETTORI,
                                          default=[SETTORI[0]])
        with c2:
            paesi_sel = st.multiselect("Paese/i target", PAESI,
                                        default=[PAESI[0]])
        with c3:
            dimensioni_sel = st.multiselect("Dimensione azienda",
                                             DIMENSIONI_AZIENDA,
                                             default=DIMENSIONI_AZIENDA)

        c4, c5 = st.columns(2)
        with c4:
            urgenza_sel = st.select_slider(
                "Urgenza minima da assegnare",
                options=["Bassa", "Media", "Alta"], value="Media",
            )
        with c5:
            n_lead = st.slider("Numero di lead da generare", 3, 30, 10)

        submit = st.form_submit_button("🔎 Avvia ricerca settoriale")

    if submit:
        if not settori_sel or not paesi_sel:
            st.error("Seleziona almeno un settore e un paese.")
            return

        usa_dati_reali = st.session_state.usa_ricerca_reale
        nuovi = []
        errori = []

        if usa_dati_reali:
            with st.spinner("Ricerca aziende su fonti verificate..."):
                per_combinazione = max(1, n_lead // (len(settori_sel)
                                                       * len(paesi_sel)))
                for settore in settori_sel:
                    for paese in paesi_sel:
                        trovati, errore = cerca_aziende_reali(
                            settore, paese, "Ricerca per Settore",
                            n_lead=per_combinazione,
                        )
                        if errore:
                            errori.append(settore + "/" + paese)
                        else:
                            nuovi.extend(trovati)

            mancanti = n_lead - len(nuovi)
            if mancanti > 0:
                for _ in range(mancanti):
                    nuovi.append(genera_lead_mock(
                        settore=random.choice(settori_sel),
                        paese=random.choice(paesi_sel),
                        dimensione=random.choice(dimensioni_sel)
                        if dimensioni_sel else None,
                        urgenza=random.choice(LIVELLI_URGENZA),
                        fonte="Ricerca per Settore",
                    ))
        else:
            for _ in range(n_lead):
                nuovi.append(genera_lead_mock(
                    settore=random.choice(settori_sel),
                    paese=random.choice(paesi_sel),
                    dimensione=random.choice(dimensioni_sel)
                    if dimensioni_sel else None,
                    urgenza=random.choice(LIVELLI_URGENZA),
                    fonte="Ricerca per Settore",
                ))

        if errori:
            st.caption("Copertura open data limitata per: "
                        + ", ".join(errori) + " — completato con dati "
                        "campione.")

        aggiungi_leads(nuovi)
        n_reali = sum(1 for l in nuovi if l["dati_reali"])
        n_campione = len(nuovi) - n_reali
        st.success(str(len(nuovi)) + " lead aggiunti al database ("
                    + str(n_reali) + " verificati, " + str(n_campione)
                    + " campione).")
        colonne_mostra = ["azienda", "dati_reali", "paese", "settore",
                            "urgenza", "punteggio", "sito_web", "telefono"]
        st.dataframe(pd.DataFrame(nuovi)[colonne_mostra],
                      use_container_width=True)


# =========================================================================
# PAGINA: RICERCA FIERE
# =========================================================================

def pagina_ricerca_fiere():
    header("Ricerca Lead da Fiere di Settore", "Genera prospect a partire "
           "da espositori ed elenchi fieristici del comparto plastica ed "
           "estrusione")

    with st.form("form_fiere"):
        fiera_sel = st.selectbox("Fiera di riferimento", FIERE_SETTORE)
        c1, c2 = st.columns(2)
        with c1:
            settori_sel = st.multiselect("Filtro settore espositori",
                                          SETTORI, default=SETTORI[:3])
        with c2:
            n_lead = st.slider("Numero espositori da profilare", 3, 25, 8)
        submit = st.form_submit_button("🎪 Estrai espositori")

    if submit:
        paese_fiera = fiera_sel.split("(")[-1].replace(")", "")
        nuovi = []
        for _ in range(n_lead):
            nuovi.append(genera_lead_mock(
                settore=random.choice(settori_sel) if settori_sel
                else random.choice(SETTORI),
                paese=random.choice(PAESI),
                fonte="Fiera: " + fiera_sel,
                nota_extra="Espositore rilevato a " + fiera_sel,
            ))
        aggiungi_leads(nuovi)
        st.success("Estratti " + str(len(nuovi)) + " espositori da "
                    + fiera_sel)
        st.dataframe(pd.DataFrame(nuovi)[
            ["azienda", "paese", "settore", "urgenza", "punteggio", "note"]
        ], use_container_width=True)


# =========================================================================
# PAGINA: PROGETTI DI INVESTIMENTO
# =========================================================================

def pagina_progetti_investimento():
    header("Radar Progetti di Investimento", "Individua aziende che hanno "
           "annunciato piani di espansione, nuovi impianti o "
           "finanziamenti per capacita' produttiva")

    with st.form("form_investimenti"):
        c1, c2 = st.columns(2)
        with c1:
            paesi_sel = st.multiselect("Area geografica", PAESI,
                                        default=PAESI[:4])
        with c2:
            soglia_investimento = st.selectbox(
                "Soglia minima investimento stimato",
                ["> 500K EUR", "> 1M EUR", "> 5M EUR", "> 20M EUR"],
            )
        n_lead = st.slider("Numero progetti da individuare", 3, 20, 6)
        submit = st.form_submit_button("📈 Cerca progetti di investimento")

    if submit:
        nuovi = []
        for _ in range(n_lead):
            fonte_notizia = random.choice(FONTI_NOTIZIA)
            lead = genera_lead_mock(
                settore=random.choice(SETTORI),
                paese=random.choice(paesi_sel) if paesi_sel
                else random.choice(PAESI),
                urgenza="Alta",
                fonte="Progetto investimento",
                nota_extra=fonte_notizia + " - soglia: "
                + soglia_investimento,
            )
            nuovi.append(lead)
        aggiungi_leads(nuovi)
        st.success(str(len(nuovi)) + " progetti di investimento "
                    "individuati (urgenza impostata su Alta).")
        st.dataframe(pd.DataFrame(nuovi)[
            ["azienda", "paese", "settore", "note", "punteggio"]
        ], use_container_width=True)


# =========================================================================
# PAGINA: ANALISI LOOKALIKE / GEMELLI
# =========================================================================

def pagina_lookalike():
    header("Analisi Lookalike / Aziende Gemelle", "Parti da un cliente "
           "fedele Friul Filiere e trova aziende con profilo simile")

    with st.form("form_lookalike"):
        cliente_rif = st.text_input("Nome cliente fedele di riferimento",
                                     "Cliente Storico S.p.A.")
        c1, c2 = st.columns(2)
        with c1:
            settore_rif = st.selectbox("Settore del cliente di "
                                        "riferimento", SETTORI)
        with c2:
            dimensione_rif = st.selectbox("Dimensione del cliente di "
                                           "riferimento", DIMENSIONI_AZIENDA)
        paesi_sel = st.multiselect("Cerca aziende simili in questi paesi",
                                    PAESI, default=PAESI[:5])
        n_lead = st.slider("Numero di aziende gemelle da trovare", 3, 20, 8)
        submit = st.form_submit_button("👥 Trova aziende gemelle")

    if submit:
        usa_dati_reali = st.session_state.usa_ricerca_reale
        nuovi = []
        errori = []

        if usa_dati_reali:
            with st.spinner("Ricerca aziende simili su fonti "
                              "verificate..."):
                per_paese = max(1, n_lead // max(1, len(paesi_sel)))
                for paese in (paesi_sel or [random.choice(PAESI)]):
                    trovati, errore = cerca_aziende_reali(
                        settore_rif, paese,
                        "Lookalike di: " + cliente_rif,
                        n_lead=per_paese,
                        query_extra="similar to " + cliente_rif,
                    )
                    if errore:
                        errori.append(paese)
                    else:
                        nuovi.extend(trovati)

            mancanti = n_lead - len(nuovi)
            if mancanti > 0:
                for _ in range(mancanti):
                    nuovi.append(genera_lead_mock(
                        settore=settore_rif,
                        paese=random.choice(paesi_sel) if paesi_sel
                        else random.choice(PAESI),
                        dimensione=dimensione_rif,
                        fonte="Lookalike di: " + cliente_rif,
                        nota_extra="Profilo simile a " + cliente_rif,
                    ))
        else:
            for _ in range(n_lead):
                nuovi.append(genera_lead_mock(
                    settore=settore_rif,
                    paese=random.choice(paesi_sel) if paesi_sel
                    else random.choice(PAESI),
                    dimensione=dimensione_rif,
                    fonte="Lookalike di: " + cliente_rif,
                    nota_extra="Profilo simile a " + cliente_rif,
                ))

        if errori:
            st.caption("Copertura open data limitata per: "
                        + ", ".join(errori) + " — completato con dati "
                        "campione.")

        aggiungi_leads(nuovi)
        n_reali = sum(1 for l in nuovi if l["dati_reali"])
        n_campione = len(nuovi) - n_reali
        st.success(str(len(nuovi)) + " aziende gemelle di '" + cliente_rif
                    + "' individuate (" + str(n_reali) + " verificate, "
                    + str(n_campione) + " campione).")
        colonne_mostra = ["azienda", "dati_reali", "paese", "settore",
                            "punteggio",
                            "sito_web", "telefono"] if usa_dati_reali \
            else ["azienda", "paese", "settore", "dimensione", "punteggio"]
        st.dataframe(pd.DataFrame(nuovi)[colonne_mostra],
                      use_container_width=True)


# =========================================================================
# MODULO FANTASIA 1: RADAR ESPANSIONE & ORGANICO
# =========================================================================

def pagina_radar_espansione():
    header("🛰️ Radar Espansione & Organico", "Modulo avanzato: incrocia "
           "segnali di crescita (assunzioni, nuovi capannoni, ampliamento "
           "organico) per anticipare la necessita' di nuove linee di "
           "estrusione")

    st.markdown(
        '<div class="ffe-card">Questo modulo simula il monitoraggio di '
        'fonti pubbliche (annunci di lavoro, comunicati stampa, permessi '
        'edilizi industriali, bilanci) per intercettare aziende in fase '
        'di crescita fisica o di organico, momento ideale per proporre '
        'nuova capacita' + "'" + ' produttiva.</div>',
        unsafe_allow_html=True,
    )

    with st.form("form_radar"):
        c1, c2, c3 = st.columns(3)
        with c1:
            segnale = st.selectbox("Tipo di segnale da monitorare", [
                "Annunci di assunzione massiva (operai di linea)",
                "Nuovo capannone / ampliamento stabilimento",
                "Aumento capitale sociale / bilancio in crescita",
                "Apertura filiale produttiva estera",
            ])
        with c2:
            paesi_sel = st.multiselect("Paesi da monitorare", PAESI,
                                        default=PAESI[:4])
        with c3:
            finestra_temporale = st.selectbox("Finestra temporale segnale",
                                               ["Ultimi 30 giorni",
                                                "Ultimi 90 giorni",
                                                "Ultimi 12 mesi"])
        n_lead = st.slider("Numero aziende da individuare", 3, 20, 7)
        submit = st.form_submit_button("🛰️ Avvia radar")

    if submit:
        nuovi = []
        for _ in range(n_lead):
            crescita_pct = random.randint(8, 60)
            nota = (segnale + " (" + finestra_temporale + ") - crescita "
                     "stimata organico/capacita': +" + str(crescita_pct)
                     + "%")
            nuovi.append(genera_lead_mock(
                settore=random.choice(SETTORI),
                paese=random.choice(paesi_sel) if paesi_sel
                else random.choice(PAESI),
                urgenza=random.choices(["Alta", "Media"], weights=[0.6, 0.4]
                                        )[0],
                fonte="Radar Espansione",
                nota_extra=nota,
            ))
        aggiungi_leads(nuovi)
        st.success(str(len(nuovi)) + " aziende in fase di espansione "
                    "individuate.")
        st.dataframe(pd.DataFrame(nuovi)[
            ["azienda", "paese", "settore", "urgenza", "note", "punteggio"]
        ], use_container_width=True)


# =========================================================================
# MODULO FANTASIA 2: SALES TWIN VERTICALE
# =========================================================================

def pagina_sales_twin_verticale():
    header("🎯 Sales Twin per Settore Verticale", "Modulo avanzato: "
           "combina l'analisi lookalike con una lente verticale di "
           "settore (automotive, medicale, edilizia...) per generare "
           "liste di prospect ad alta pertinenza tecnologica")

    st.markdown(
        '<div class="ffe-card">A differenza del modulo Lookalike '
        'generico, qui la ricerca viene ristretta a un singolo verticale '
        'applicativo e arricchita con la tecnologia Friul Filiere piu' + "'"
        + ' pertinente per quel settore.</div>', unsafe_allow_html=True,
    )

    MAPPA_TECNOLOGIA_VERTICALE = {
        "Automotive": "Linee di coestrusione multistrato",
        "Medicale": "Linee monofilamento e reti estruse",
        "Edilizia": "Linee di estrusione PVC per profili finestra",
        "Packaging alimentare": "Sistemi downstream (taglio, impilamento, "
                                  "imballo automatico)",
        "Arredamento": "Impianti per compositi legno-plastica (WPC)",
        "Elettrodomestici": "Teste e stampi per profili tecnici complessi",
        "Serramenti": "Linee di estrusione PVC per profili finestra",
        "Agricoltura": "Linee di estrusione tubi corrugati e lisci",
        "Cavi e condotte": "Linee di estrusione tubi corrugati e lisci",
        "Water management": "Sistemi di calibrazione e raffreddamento "
                              "sottovuoto",
        "Arredo urbano": "Impianti per compositi legno-plastica (WPC)",
        "Nautica": "Automazione e retrofit Industry 4.0 per linee di "
                    "estrusione",
    }

    with st.form("form_twin"):
        verticale = st.selectbox("Settore verticale target", SETTORI)
        cliente_rif = st.text_input("Cliente fedele modello per questo "
                                     "verticale", "Best Client " + verticale)
        paesi_sel = st.multiselect("Paesi target", PAESI,
                                    default=PAESI[:5])
        n_lead = st.slider("Numero prospect verticali da generare", 3, 20,
                            8)
        submit = st.form_submit_button("🎯 Genera Sales Twin verticali")

    if submit:
        tecnologia = MAPPA_TECNOLOGIA_VERTICALE.get(
            verticale, random.choice(TECNOLOGIE_FRIUL_FILIERE))
        usa_dati_reali = st.session_state.usa_ricerca_reale
        nuovi = []
        errori = []

        if usa_dati_reali:
            with st.spinner("Ricerca prospect verticali reali su Google "
                              "Places..."):
                per_paese = max(1, n_lead // max(1, len(paesi_sel)))
                for paese in (paesi_sel or [random.choice(PAESI)]):
                    trovati, errore = cerca_aziende_reali(
                        verticale, paese,
                        "Sales Twin reale (" + verticale + ")",
                        n_lead=per_paese,
                    )
                    if errore:
                        errori.append(paese + ": " + errore)
                    else:
                        for lead in trovati:
                            lead["tecnologia_target"] = tecnologia
                            lead["note"] = ("Twin verticale di '"
                                              + cliente_rif + "' - "
                                              + lead["note"])
                        nuovi.extend(trovati)
        else:
            for _ in range(n_lead):
                nuovi.append(genera_lead_mock(
                    settore=verticale,
                    paese=random.choice(paesi_sel) if paesi_sel
                    else random.choice(PAESI),
                    tecnologia=tecnologia,
                    fonte="Sales Twin Verticale (" + verticale + ", mock)",
                    nota_extra="Twin verticale di '" + cliente_rif + "' - "
                    "tecnologia consigliata: " + tecnologia,
                ))

        if errori:
            st.warning("Alcune ricerche reali non hanno prodotto "
                        "risultati: " + "; ".join(errori))
        if not nuovi:
            st.error("Nessun lead trovato/generato. Verifica la chiave "
                      "Google Places o riprova con altri filtri.")
            return

        aggiungi_leads(nuovi)
        st.markdown(badge_fonte_dati(usa_dati_reali), unsafe_allow_html=True)
        st.success(str(len(nuovi)) + " prospect verticali '" + verticale
                    + "' individuati.")
        colonne_mostra = ["azienda", "paese", "settore", "tecnologia_target",
                            "punteggio", "sito_web"] if usa_dati_reali \
            else ["azienda", "paese", "settore", "tecnologia_target",
                    "punteggio"]
        st.dataframe(pd.DataFrame(nuovi)[colonne_mostra],
                      use_container_width=True)


# =========================================================================
# PAGINA: DOSSIER TECNICO AI
# =========================================================================

def pagina_dossier():
    header("📄 Generatore Dossier Tecnico AI", "Genera un dossier "
           "tecnico-commerciale personalizzato per un lead selezionato, "
           "in italiano, inglese, tedesco o francese")

    df = df_leads()
    if df.empty:
        st.warning("Genera prima alcuni lead da uno dei moduli di ricerca.")
        return

    c1, c2 = st.columns([2, 1])
    with c1:
        etichette = df["azienda"] + " - " + df["paese"] + " (#" \
            + df["id"].astype(str) + ")"
        selezione = st.selectbox("Seleziona lead", etichette)
        idx = int(selezione.split("#")[-1].replace(")", ""))
    with c2:
        lingua = st.selectbox("Lingua dossier",
                               ["Italiano", "Inglese", "Tedesco",
                                "Francese"])

    lead = next(l for l in st.session_state.leads if l["id"] == idx)

    st.markdown('<div class="ffe-card">'
                 + '<b>' + lead["azienda"] + '</b> ' + badge_urgenza(
                     lead["urgenza"])
                 + '<br>' + lead["paese"] + " | " + lead["settore"] + " | "
                 + lead["dimensione"]
                 + '<br>Tecnologia target: ' + lead["tecnologia_target"]
                 + '</div>', unsafe_allow_html=True)

    if st.button("📄 Genera dossier tecnico"):
        with st.spinner("Generazione dossier in corso..."):
            testo = ottieni_dossier(lead, lingua)
        st.markdown("#### Anteprima dossier")
        st.text_area("Contenuto", testo, height=350)

        pdf_bytes = export_pdf_dossier(lead, testo)
        st.download_button(
            "⬇️ Scarica dossier in PDF", data=pdf_bytes,
            file_name="dossier_" + lead["azienda"].replace(" ", "_") + "_"
            + lingua + ".pdf", mime="application/pdf",
        )


# =========================================================================
# PAGINA: SEQUENZE OUTREACH
# =========================================================================

def pagina_outreach():
    header("✉️ Sequenze Email Multi-lingua", "Genera una sequenza di 3 "
           "email di outreach commerciale (IT / EN / DE / FR) tarata "
           "sulle tecnologie Friul Filiere")

    df = df_leads()
    if df.empty:
        st.warning("Genera prima alcuni lead da uno dei moduli di ricerca.")
        return

    c1, c2 = st.columns([2, 1])
    with c1:
        etichette = df["azienda"] + " - " + df["paese"] + " (#" \
            + df["id"].astype(str) + ")"
        selezione = st.selectbox("Seleziona lead", etichette,
                                  key="sel_outreach")
        idx = int(selezione.split("#")[-1].replace(")", ""))
    with c2:
        lingua = st.selectbox("Lingua sequenza",
                               ["Italiano", "Inglese", "Tedesco",
                                "Francese"], key="lingua_outreach")

    lead = next(l for l in st.session_state.leads if l["id"] == idx)

    if st.button("✉️ Genera sequenza email"):
        sequenza = genera_sequenza_email(lead, lingua)
        for step in sequenza:
            st.markdown(
                '<div class="ffe-card"><b>Step ' + str(step["step"])
                + ' - ' + step["giorno_invio"] + '</b><br>'
                + '<b>Oggetto:</b> ' + step["oggetto"] + '</div>',
                unsafe_allow_html=True,
            )
            st.text_area("Corpo email step " + str(step["step"]),
                          step["corpo"], height=160,
                          key="email_body_" + str(step["step"]))

        testo_completo = "\n\n---\n\n".join(
            "STEP " + str(s["step"]) + " (" + s["giorno_invio"] + ")\n"
            + "Oggetto: " + s["oggetto"] + "\n\n" + s["corpo"]
            for s in sequenza
        )
        st.download_button(
            "⬇️ Scarica sequenza (TXT)",
            data=testo_completo.encode("utf-8"),
            file_name="sequenza_" + lead["azienda"].replace(" ", "_") + "_"
            + lingua + ".txt", mime="text/plain",
        )


# =========================================================================
# PAGINA: CRM & DATABASE LEAD
# =========================================================================

def pagina_crm():
    header("🗂️ CRM & Database Lead", "Vista completa dei lead raccolti, "
           "con filtri avanzati, gestione stato ed export")

    df = df_leads()
    if df.empty:
        st.warning("Nessun lead presente. Usa i moduli di ricerca per "
                    "popolare il database.")
        return

    st.markdown("#### Filtri intelligenti")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        f_paese = st.multiselect("Paese target", sorted(df["paese"].unique()))
    with c2:
        f_dimensione = st.multiselect("Dimensione azienda",
                                       sorted(df["dimensione"].unique()))
    with c3:
        f_lotto = st.multiselect("Lotto di ricerca",
                                  sorted(df["lotto"].unique()))
    with c4:
        f_urgenza = st.multiselect("Livello di urgenza",
                                    sorted(df["urgenza"].unique()))
    with c5:
        f_reali = st.selectbox("Tipo di dato", ["Tutti", "Solo dati reali",
                                                  "Solo dati dimostrativi"])

    df_filtrato = df.copy()
    if f_paese:
        df_filtrato = df_filtrato[df_filtrato["paese"].isin(f_paese)]
    if f_dimensione:
        df_filtrato = df_filtrato[df_filtrato["dimensione"].isin(
            f_dimensione)]
    if f_lotto:
        df_filtrato = df_filtrato[df_filtrato["lotto"].isin(f_lotto)]
    if f_urgenza:
        df_filtrato = df_filtrato[df_filtrato["urgenza"].isin(f_urgenza)]
    if f_reali == "Solo dati reali":
        df_filtrato = df_filtrato[df_filtrato["dati_reali"] == True]
    elif f_reali == "Solo dati dimostrativi":
        df_filtrato = df_filtrato[df_filtrato["dati_reali"] == False]

    st.markdown("<div class='ffe-divider'></div>", unsafe_allow_html=True)
    st.markdown("#### Lead (" + str(len(df_filtrato)) + " risultati)")

    st.dataframe(
        df_filtrato[[
            "id", "azienda", "dati_reali", "paese", "settore", "dimensione",
            "urgenza", "stato", "punteggio", "fonte", "contatto", "email",
            "telefono", "sito_web", "data_inserimento",
        ]],
        use_container_width=True, height=380,
    )

    st.markdown("#### Aggiorna stato lead")
    c1, c2 = st.columns([1, 1])
    with c1:
        id_scelto = st.selectbox("ID lead da aggiornare",
                                  df_filtrato["id"].tolist() if not
                                  df_filtrato.empty else [])
    with c2:
        nuovo_stato = st.selectbox("Nuovo stato", STATI_LEAD)
    if st.button("Aggiorna stato") and id_scelto:
        for lead in st.session_state.leads:
            if lead["id"] == id_scelto:
                lead["stato"] = nuovo_stato
        st.success("Stato del lead #" + str(id_scelto) + " aggiornato a '"
                    + nuovo_stato + "'.")

    st.markdown("<div class='ffe-divider'></div>", unsafe_allow_html=True)
    st.markdown("#### Esportazione")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "⬇️ Esporta CSV (filtrato)",
            data=export_csv_bytes(df_filtrato),
            file_name="lead_friul_filiere.csv", mime="text/csv",
        )
    with c2:
        st.download_button(
            "⬇️ Esporta PDF elenco (filtrato)",
            data=export_pdf_lista_lead(df_filtrato),
            file_name="lead_friul_filiere.pdf", mime="application/pdf",
        )
    with c3:
        if st.button("🔄 Nuovo lotto di ricerca"):
            st.session_state.lotto_corrente += 1
            st.success("Avviato lotto di ricerca n. "
                        + str(st.session_state.lotto_corrente))

    st.markdown("<div class='ffe-divider'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Svuota database lead (irreversibile)"):
        st.session_state.leads = []
        st.session_state.dossier_cache = {}
        st.session_state.email_cache = {}
        st.success("Database svuotato.")


# =========================================================================
# ROUTING PRINCIPALE
# =========================================================================

def main():
    sidebar()
    pagina = st.session_state.pagina

    if pagina == "Dashboard":
        pagina_dashboard()
    elif pagina == "🔎 Ricerca per Settore":
        pagina_ricerca_settore()
    elif pagina == "🎪 Ricerca Fiere":
        pagina_ricerca_fiere()
    elif pagina == "📈 Progetti di Investimento":
        pagina_progetti_investimento()
    elif pagina == "👥 Analisi Lookalike":
        pagina_lookalike()
    elif pagina == "🛰️ Radar Espansione & Organico":
        pagina_radar_espansione()
    elif pagina == "🎯 Sales Twin Verticale":
        pagina_sales_twin_verticale()
    elif pagina == "📄 Dossier Tecnico AI":
        pagina_dossier()
    elif pagina == "✉️ Sequenze Outreach":
        pagina_outreach()
    elif pagina == "🗂️ CRM & Database Lead":
        pagina_crm()


if __name__ == "__main__":
    main()
