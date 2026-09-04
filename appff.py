import io
import json
import re
import time
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF


# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(
    page_title="FRIUL FILIERE LEAD ENGINE",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0b1220;
        color: #e5e7eb;
    }

    section[data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #263244;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 12px;
        padding: 18px;
        min-height: 110px;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
    }

    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
    }

    .lead-card {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }

    .source-real {
        color: #34d399;
        font-weight: 700;
    }

    .source-mock {
        color: #fbbf24;
        font-weight: 700;
    }

    .small-muted {
        color: #94a3b8;
        font-size: 0.82rem;
    }

    .score {
        font-size: 1.6rem;
        font-weight: 800;
    }

    .badge {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 999px;
        background: #1f2937;
        margin-right: 5px;
        font-size: 0.78rem;
    }

    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #263244;
        padding: 12px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# COSTANTI
# ============================================================

SETTORI = [
    "Metalmeccanica",
    "Carpenteria",
    "Automazione industriale",
    "Macchinari industriali",
    "Packaging",
    "Alimentare",
    "Legno e arredamento",
    "Plastica",
    "Elettronica",
    "Logistica",
    "Tessile",
    "Chimica",
    "Energia",
    "Edilizia",
    "Altro",
]

PAESI = [
    "Italia",
    "Austria",
    "Germania",
    "Slovenia",
    "Croazia",
    "Francia",
    "Svizzera",
]

REGIONI_ITALIA = [
    "Tutte",
    "Friuli-Venezia Giulia",
    "Veneto",
    "Lombardia",
    "Emilia-Romagna",
    "Trentino-Alto Adige",
    "Piemonte",
    "Liguria",
    "Toscana",
    "Lazio",
    "Campania",
    "Puglia",
    "Sicilia",
    "Sardegna",
]

DIMENSIONI = [
    "Tutte",
    "Micro",
    "Piccola",
    "Media",
    "Grande",
    "Da verificare",
]

URGENZE = [
    "Tutte",
    "Bassa",
    "Media",
    "Alta",
]

STATI_LEAD = [
    "Nuovo",
    "Contattato",
    "In trattativa",
    "Qualificato",
    "Cliente",
    "Perso",
]

TECNOLOGIE = [
    "Automazione",
    "Robotica",
    "CNC",
    "ERP",
    "MES",
    "IoT",
    "AI",
    "Packaging",
    "Logistica",
    "Energia",
    "Da verificare",
]


# ============================================================
# SESSION STATE
# ============================================================

def init_session_state():
    defaults = {
        "leads": [],
        "next_id": 1,
        "gemini_api_key": "",
        "usa_ricerca_reale": True,
        "dossier_cache": {},
        "email_cache": {},
        "lotto_corrente": 1,
        "pagina": "Dashboard",
        "ultimo_risultato_ricerca": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============================================================
# UTILITY
# ============================================================

def safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default

    text = str(value).strip()

    if text.lower() in {"none", "nan", "null"}:
        return default

    return text


def normalizza_testo(value: Any) -> str:
    text = safe_str(value).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_url(url: str) -> str:
    url = safe_str(url)

    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        return "https://" + url

    return url


def nuovo_id() -> int:
    value = int(st.session_state.next_id)
    st.session_state.next_id += 1
    return value


def score_label(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def source_badge(lead: Dict[str, Any]) -> str:
    if lead.get("dati_reali"):
        return '<span class="source-real">● DATI REALI</span>'

    return '<span class="source-mock">● MOCK / DEMO</span>'


# ============================================================
# MAPPING OSM / OVERPASS
# ============================================================

QUERY_OSM = {
    "Metalmeccanica": [
        '"industrial"="factory"',
        '"craft"="metal_construction"',
        '"industrial"="works"',
    ],
    "Carpenteria": [
        '"craft"="metal_construction"',
        '"industrial"="works"',
    ],
    "Automazione industriale": [
        '"industrial"="factory"',
        '"industrial"="works"',
    ],
    "Macchinari industriali": [
        '"industrial"="factory"',
        '"industrial"="works"',
    ],
    "Packaging": [
        '"industrial"="factory"',
        '"industrial"="works"',
    ],
    "Alimentare": [
        '"industrial"="factory"',
        '"craft"="food"',
    ],
    "Legno e arredamento": [
        '"craft"="carpenter"',
        '"shop"="furniture"',
        '"industrial"="factory"',
    ],
    "Plastica": [
        '"industrial"="factory"',
        '"industrial"="works"',
    ],
    "Elettronica": [
        '"industrial"="factory"',
        '"shop"="electronics"',
    ],
    "Logistica": [
        '"industrial"="warehouse"',
        '"amenity"="loading_dock"',
        '"building"="warehouse"',
    ],
    "Tessile": [
        '"craft"="tailor"',
        '"industrial"="factory"',
    ],
    "Chimica": [
        '"industrial"="factory"',
    ],
    "Energia": [
        '"power"="plant"',
        '"power"="substation"',
    ],
    "Edilizia": [
        '"industrial"="works"',
        '"craft"="builder"',
    ],
    "Altro": [
        '"industrial"="factory"',
        '"industrial"="works"',
    ],
}


# Coordinate approssimative delle regioni italiane.
# Servono soltanto come fallback quando non viene specificata una città.
REGIONI_BBOX = {
    "Friuli-Venezia Giulia": (45.55, 12.35, 46.70, 14.00),
    "Veneto": (44.80, 10.60, 46.70, 13.10),
    "Lombardia": (44.65, 8.50, 46.65, 11.50),
    "Emilia-Romagna": (43.70, 9.20, 45.20, 12.80),
    "Trentino-Alto Adige": (45.65, 10.35, 47.10, 12.50),
    "Piemonte": (44.00, 6.60, 46.50, 9.30),
    "Liguria": (43.80, 7.40, 44.70, 10.10),
    "Toscana": (42.20, 9.70, 44.50, 12.00),
    "Lazio": (40.70, 11.40, 42.90, 14.00),
    "Campania": (39.90, 13.70, 41.60, 15.80),
    "Puglia": (39.70, 15.30, 42.10, 18.60),
    "Sicilia": (36.60, 12.40, 38.80, 15.70),
    "Sardegna": (38.80, 8.00, 41.30, 9.90),
}


# ============================================================
# GEOCODING NOMINATIM
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def geocodifica_luogo(luogo: str) -> Optional[Tuple[float, float]]:
    """
    Usa Nominatim/OpenStreetMap per ottenere le coordinate.
    Non richiede API key.
    """

    luogo = safe_str(luogo)

    if not luogo:
        return None

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": luogo,
        "format": "json",
        "limit": 1,
        "countrycodes": "it",
    }

    headers = {
        "User-Agent": "FriulFiliereLeadEngine/1.0"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        return float(data[0]["lat"]), float(data[0]["lon"])

    except Exception:
        return None


# ============================================================
# OVERPASS
# ============================================================

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def costruisci_area_query(
    paese: str,
    regione: str,
    citta: str,
) -> Tuple[str, Optional[Tuple[float, float, float, float]]]:

    paese = safe_str(paese)
    regione = safe_str(regione)
    citta = safe_str(citta)

    if citta:
        coords = geocodifica_luogo(f"{citta}, {regione}, {paese}")

        if coords:
            lat, lon = coords
            radius = 25000

            return (
                f'around:{radius},{lat},{lon}',
                None,
            )

    if regione and regione != "Tutte" and regione in REGIONI_BBOX:
        return "", REGIONI_BBOX[regione]

    if paese == "Italia":
        return "", (35.0, 6.0, 47.5, 19.0)

    return "", None


def costruisci_overpass_query(
    settore: str,
    paese: str,
    regione: str = "Tutte",
    citta: str = "",
    limite: int = 50,
) -> str:

    area_filter, bbox = costruisci_area_query(
        paese,
        regione,
        citta,
    )

    tags = QUERY_OSM.get(
        settore,
        QUERY_OSM["Altro"],
    )

    statements = []

    for tag in tags:
        if "=" not in tag:
            continue

        key, value = tag.split("=", 1)
        key = key.strip('"')
        value = value.strip('"')

        if area_filter:
            statements.append(
                f'nwr["{key}"="{value}"]({area_filter});'
            )

        elif bbox:
            south, west, north, east = bbox

            statements.append(
                f'nwr["{key}"="{value}"]'
                f'({south},{west},{north},{east});'
            )

        else:
            statements.append(
                f'nwr["{key}"="{value}"]'
                f'(area.searchArea);'
            )

    body = "\n".join(statements)

    query = f"""
[out:json][timeout:45];

(
{body}
);

out center tags;
"""

    return query


@st.cache_data(ttl=900, show_spinner=False)
def overpass_search(
    settore: str,
    paese: str,
    regione: str,
    citta: str,
    limite: int,
) -> List[Dict[str, Any]]:

    query = costruisci_overpass_query(
        settore=settore,
        paese=paese,
        regione=regione,
        citta=citta,
        limite=limite,
    )

    last_error = None

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            response = requests.post(
                endpoint,
                data=query.encode("utf-8"),
                headers={
                    "User-Agent": "FriulFiliereLeadEngine/1.0"
                },
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()

            elements = data.get("elements", [])

            if not elements:
                return []

            # Limitazione lato client per evitare dataset enormi.
            return elements[:limite]

        except Exception as exc:
            last_error = exc
            continue

    if last_error:
        raise RuntimeError(
            f"Overpass non disponibile: {last_error}"
        )

    return []


# ============================================================
# TRASFORMAZIONE OSM -> LEAD
# ============================================================

def estrai_coordinate(element: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    if element.get("lat") is not None and element.get("lon") is not None:
        return float(element["lat"]), float(element["lon"])

    center = element.get("center") or {}

    if center.get("lat") is not None and center.get("lon") is not None:
        return float(center["lat"]), float(center["lon"])

    return None, None


def indirizzo_da_tags(tags: Dict[str, Any]) -> str:
    parts = []

    street = safe_str(tags.get("addr:street"))
    house = safe_str(tags.get("addr:housenumber"))
    postcode = safe_str(tags.get("addr:postcode"))
    city = safe_str(
        tags.get("addr:city")
        or tags.get("addr:town")
        or tags.get("addr:village")
    )

    if street:
        address = street

        if house:
            address += f" {house}"

        parts.append(address)

    if postcode:
        parts.append(postcode)

    if city:
        parts.append(city)

    return ", ".join(parts)


def determina_dimensione(tags: Dict[str, Any]) -> str:
    employees = safe_str(
        tags.get("employees")
        or tags.get("staff")
        or tags.get("capacity")
    )

    if not employees:
        return "Da verificare"

    match = re.search(r"\d+", employees)

    if not match:
        return "Da verificare"

    try:
        n = int(match.group())

        if n < 10:
            return "Micro"
        if n < 50:
            return "Piccola"
        if n < 250:
            return "Media"

        return "Grande"

    except ValueError:
        return "Da verificare"


def determina_tecnologia(
    settore: str,
    tags: Dict[str, Any],
) -> str:

    text = " ".join(
        [
            settore,
            safe_str(tags.get("name")),
            safe_str(tags.get("description")),
            safe_str(tags.get("industrial")),
        ]
    ).lower()

    mapping = [
        ("robot", "Robotica"),
        ("automat", "Automazione"),
        ("cnc", "CNC"),
        ("erp", "ERP"),
        ("mes", "MES"),
        ("iot", "IoT"),
        ("energy", "Energia"),
        ("solar", "Energia"),
        ("logistic", "Logistica"),
        ("packag", "Packaging"),
    ]

    for keyword, technology in mapping:
        if keyword in text:
            return technology

    return "Da verificare"


def calcola_score_lead(lead: Dict[str, Any]) -> int:
    score = 35

    if lead.get("nome"):
        score += 10

    if lead.get("indirizzo"):
        score += 10

    if lead.get("sito"):
        score += 15

    if lead.get("telefono"):
        score += 10

    if lead.get("email"):
        score += 10

    if lead.get("tecnologia") != "Da verificare":
        score += 5

    if lead.get("settore"):
        score += 5

    return min(score, 100)


def lead_da_osm(
    element: Dict[str, Any],
    settore: str,
    paese: str,
) -> Optional[Dict[str, Any]]:

    tags = element.get("tags", {})

    nome = safe_str(
        tags.get("name")
        or tags.get("brand")
        or tags.get("operator")
    )

    if not nome:
        return None

    lat, lon = estrai_coordinate(element)

    sito = safe_str(
        tags.get("website")
        or tags.get("contact:website")
    )

    telefono = safe_str(
        tags.get("phone")
        or tags.get("contact:phone")
    )

    email = safe_str(
        tags.get("email")
        or tags.get("contact:email")
    )

    indirizzo = indirizzo_da_tags(tags)

    lead = {
        "id": nuovo_id(),
        "nome": nome,
        "paese": paese,
        "regione": safe_str(tags.get("addr:state")),
        "citta": safe_str(
            tags.get("addr:city")
            or tags.get("addr:town")
            or tags.get("addr:village")
        ),
        "indirizzo": indirizzo,
        "telefono": telefono,
        "email": email,
        "sito": clean_url(sito),
        "settore": settore,
        "dimensione": determina_dimensione(tags),
        "urgenza": random.choice(["Bassa", "Media", "Alta"]),
        "tecnologia": determina_tecnologia(settore, tags),
        "stato": "Nuovo",
        "fonte": "OpenStreetMap",
        "dati_reali": True,
        "lat": lat,
        "lon": lon,
        "osm_type": element.get("type"),
        "osm_id": element.get("id"),
        "creato_il": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "note": "Lead individuato tramite dati OpenStreetMap.",
    }

    lead["score"] = calcola_score_lead(lead)
    lead["classe"] = score_label(lead["score"])

    return lead


def deduplica_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    seen = set()

    for lead in leads:
        key = (
            normalizza_testo(lead.get("nome")),
            normalizza_testo(lead.get("citta")),
            normalizza_testo(lead.get("indirizzo")),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(lead)

    return result


# ============================================================
# RICERCA AZIENDE REALI
# ============================================================

def cerca_aziende_reali(
    settore: str,
    paese: str,
    regione: str,
    citta: str,
    numero: int,
) -> List[Dict[str, Any]]:

    elements = overpass_search(
        settore=settore,
        paese=paese,
        regione=regione,
        citta=citta,
        limite=max(numero * 2, numero),
    )

    leads = []

    for element in elements:
        lead = lead_da_osm(
            element,
            settore,
            paese,
        )

        if lead:
            leads.append(lead)

        if len(leads) >= numero:
            break

    return deduplica_leads(leads)


# ============================================================
# MOCK
# ============================================================

MOCK_PREFIX = [
    "Friul",
    "Nord",
    "Alpina",
    "Tecno",
    "Euro",
    "Industrial",
    "Meccanica",
    "Futura",
    "Pro",
]

MOCK_SUFFIX = [
    "Engineering",
    "Industriale",
    "Systems",
    "Automation",
    "Group",
    "Solutions",
    "Srl",
]


def genera_mock_lead(
    settore: str,
    paese: str,
    indice: int,
) -> Dict[str, Any]:

    nome = (
        f"{random.choice(MOCK_PREFIX)} "
        f"{random.choice(MOCK_SUFFIX)} {indice}"
    )

    lead = {
        "id": nuovo_id(),
        "nome": nome,
        "paese": paese,
        "regione": "Friuli-Venezia Giulia",
        "citta": random.choice(
            ["Udine", "Pordenone", "Gorizia", "Trieste"]
        ),
        "indirizzo": "DATO DEMO",
        "telefono": "",
        "email": "",
        "sito": "",
        "settore": settore,
        "dimensione": random.choice(
            ["Piccola", "Media", "Da verificare"]
        ),
        "urgenza": random.choice(URGENZE[1:]),
        "tecnologia": random.choice(TECNOLOGIE),
        "stato": "Nuovo",
        "fonte": "MOCK",
        "dati_reali": False,
        "lat": None,
        "lon": None,
        "osm_type": "",
        "osm_id": "",
        "creato_il": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "note": (
            "Record dimostrativo generato automaticamente. "
            "NON utilizzare come dato aziendale reale."
        ),
    }

    lead["score"] = calcola_score_lead(lead)
    lead["classe"] = score_label(lead["score"])

    return lead


# ============================================================
# INSERIMENTO LEAD
# ============================================================

def aggiungi_leads(leads: List[Dict[str, Any]]) -> int:
    existing_keys = {
        (
            normalizza_testo(x.get("nome")),
            normalizza_testo(x.get("citta")),
            normalizza_testo(x.get("indirizzo")),
        )
        for x in st.session_state.leads
    }

    added = 0

    for lead in leads:
        key = (
            normalizza_testo(lead.get("nome")),
            normalizza_testo(lead.get("citta")),
            normalizza_testo(lead.get("indirizzo")),
        )

        if key in existing_keys:
            continue

        st.session_state.leads.append(lead)
        existing_keys.add(key)
        added += 1

    return added


# ============================================================
# GEMINI OPZIONALE
# ============================================================

def call_gemini_api(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> Optional[str]:

    api_key = safe_str(
        st.session_state.get("gemini_api_key", "")
    )

    if not api_key:
        return None

    # Modello configurabile.
    model = st.session_state.get(
        "gemini_model",
        "gemini-2.5-flash",
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
    )

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return None

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        texts = [
            safe_str(part.get("text"))
            for part in parts
            if part.get("text")
        ]

        return "\n".join(texts).strip() or None

    except requests.RequestException as exc:
        st.warning(
            f"Gemini non disponibile: {exc}"
        )
        return None

    except Exception as exc:
        st.warning(
            f"Errore Gemini: {exc}"
        )
        return None


# ============================================================
# DOSSIER
# ============================================================

def genera_dossier_mock(lead: Dict[str, Any]) -> str:
    return f"""
DOSSIER COMMERCIALE

Azienda: {lead.get("nome", "")}
Settore: {lead.get("settore", "")}
Paese: {lead.get("paese", "")}
Città: {lead.get("citta", "")}
Dimensione: {lead.get("dimensione", "")}
Tecnologia: {lead.get("tecnologia", "")}
Score: {lead.get("score", 0)}/100

ANALISI

Il lead presenta una compatibilità preliminare con il
profilo target selezionato.

PUNTI DI ATTENZIONE

- Dimensione aziendale: {lead.get("dimensione", "Da verificare")}
- Tecnologia: {lead.get("tecnologia", "Da verificare")}
- Presenza web: {"Sì" if lead.get("sito") else "Da verificare"}
- Contatto telefonico: {"Sì" if lead.get("telefono") else "Da verificare"}

PROSSIMO PASSO

Verificare il sito aziendale e identificare il referente
decisionale prima del primo contatto commerciale.

NOTA

Questa analisi è preliminare e non sostituisce una verifica
manuale dell'azienda.
""".strip()


def genera_dossier(lead: Dict[str, Any]) -> str:
    cache_key = str(lead.get("id"))

    if cache_key in st.session_state.dossier_cache:
        return st.session_state.dossier_cache[cache_key]

    prompt = f"""
Sei un analista commerciale B2B.

Crea un dossier sintetico e professionale sull'azienda seguente.

NON inventare dati mancanti.
Distingui chiaramente fatti e ipotesi.

Azienda: {lead.get("nome")}
Settore: {lead.get("settore")}
Paese: {lead.get("paese")}
Regione: {lead.get("regione")}
Città: {lead.get("citta")}
Indirizzo: {lead.get("indirizzo")}
Sito: {lead.get("sito")}
Telefono: {lead.get("telefono")}
Dimensione: {lead.get("dimensione")}
Tecnologia: {lead.get("tecnologia")}
Score: {lead.get("score")}

Produci:
1. Profilo aziendale
2. Possibili esigenze
3. Fit commerciale
4. Argomenti di vendita
5. Informazioni da verificare
6. Prossima azione consigliata
"""

    result = call_gemini_api(prompt)

    if not result:
        result = genera_dossier_mock(lead)

    st.session_state.dossier_cache[cache_key] = result

    return result


# ============================================================
# EMAIL OUTREACH
# ============================================================

def genera_email_sequence(lead: Dict[str, Any]) -> List[Dict[str, Any]]:
    key = str(lead.get("id"))

    if key in st.session_state.email_cache:
        return st.session_state.email_cache[key]

    nome = lead.get("nome", "azienda")
    settore = lead.get("settore", "")
    tecnologia = lead.get("tecnologia", "")

    prompt = f"""
Scrivi una sequenza commerciale B2B di 3 email.

Azienda: {nome}
Settore: {settore}
Tecnologia: {tecnologia}

Non inventare nomi di persone, numeri, clienti o risultati.

Restituisci JSON con questa struttura:

[
  {{
    "giorno": 0,
    "oggetto": "...",
    "testo": "..."
  }},
  {{
    "giorno": 4,
    "oggetto": "...",
    "testo": "..."
  }},
  {{
    "giorno": 9,
    "oggetto": "...",
    "testo": "..."
  }}
]
"""

    result = call_gemini_api(
        prompt,
        temperature=0.6,
        max_tokens=1800,
    )

    if result:
        try:
            cleaned = result.strip()

            if cleaned.startswith("```"):
                cleaned = re.sub(
                    r"^```(?:json)?",
                    "",
                    cleaned,
                )
                cleaned = re.sub(
                    r"```$",
                    "",
                    cleaned,
                )

            sequence = json.loads(cleaned)

            if isinstance(sequence, list):
                st.session_state.email_cache[key] = sequence
                return sequence

        except Exception:
            pass

    sequence = [
        {
            "giorno": 0,
            "oggetto": f"Possibile collaborazione con {nome}",
            "testo": (
                f"Buongiorno,\n\n"
                f"sto analizzando aziende del settore "
                f"{settore} e {nome} è emersa tra i potenziali "
                f"interlocutori.\n\n"
                f"Mi farebbe piacere capire se ci sono iniziative "
                f"legate a {tecnologia} che possiamo approfondire.\n\n"
                f"Possiamo sentirci brevemente?\n"
            ),
        },
        {
            "giorno": 4,
            "oggetto": "Un rapido follow-up",
            "testo": (
                f"Buongiorno,\n\n"
                f"riprendo la mia precedente comunicazione.\n\n"
                f"Se il tema è di interesse, possiamo organizzare "
                f"una breve conversazione per capire eventuali "
                f"necessità di {nome}.\n\n"
                f"Grazie."
            ),
        },
        {
            "giorno": 9,
            "oggetto": "Ultimo contatto",
            "testo": (
                f"Buongiorno,\n\n"
                f"chiudo questo breve follow-up.\n\n"
                f"Se {nome} sta valutando progetti collegati a "
                f"{settore}, resto volentieri a disposizione.\n\n"
                f"Un saluto."
            ),
        },
    ]

    st.session_state.email_cache[key] = sequence

    return sequence


# ============================================================
# EXPORT CSV
# ============================================================

def prepara_dataframe(leads: List[Dict[str, Any]]) -> pd.DataFrame:
    if not leads:
        return pd.DataFrame()

    columns = [
        "id",
        "nome",
        "paese",
        "regione",
        "citta",
        "indirizzo",
        "telefono",
        "email",
        "sito",
        "settore",
        "dimensione",
        "urgenza",
        "tecnologia",
        "score",
        "classe",
        "stato",
        "fonte",
        "dati_reali",
        "creato_il",
        "note",
    ]

    data = []

    for lead in leads:
        data.append(
            {
                column: lead.get(column, "")
                for column in columns
            }
        )

    return pd.DataFrame(data)


def export_csv(leads: List[Dict[str, Any]]) -> bytes:
    df = prepara_dataframe(leads)

    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


# ============================================================
# EXPORT PDF
# ============================================================

def export_pdf_lista_lead(leads: List[Dict[str, Any]]) -> bytes:
    pdf = FPDF(
        orientation="L",
        unit="mm",
        format="A4",
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=12,
    )

    pdf.add_page()

    pdf.set_font(
        "Helvetica",
        "B",
        18,
    )

    pdf.cell(
        0,
        10,
        "FRIUL FILIERE LEAD ENGINE",
        ln=True,
    )

    pdf.set_font(
        "Helvetica",
        "",
        9,
    )

    pdf.cell(
        0,
        7,
        "Lista lead commerciali",
        ln=True,
    )

    pdf.cell(
        0,
        7,
        datetime.now().strftime(
            "Generato il %Y-%m-%d %H:%M"
        ),
        ln=True,
    )

    pdf.ln(4)

    headers = [
        "ID",
        "Azienda",
        "Paese",
        "Città",
        "Settore",
        "Score",
        "Classe",
        "Stato",
        "Fonte",
    ]

    widths = [
        12,
        60,
        24,
        35,
        48,
        18,
        18,
        28,
        30,
    ]

    pdf.set_font(
        "Helvetica",
        "B",
        8,
    )

    for header, width in zip(headers, widths):
        pdf.cell(
            width,
            8,
            header,
            border=1,
        )

    pdf.ln()

    pdf.set_font(
        "Helvetica",
        "",
        7,
    )

    for lead in leads:
        values = [
            safe_str(lead.get("id")),
            safe_str(lead.get("nome"))[:35],
            safe_str(lead.get("paese"))[:14],
            safe_str(lead.get("citta"))[:20],
            safe_str(lead.get("settore"))[:25],
            safe_str(lead.get("score")),
            safe_str(lead.get("classe")),
            safe_str(lead.get("stato"))[:15],
            safe_str(lead.get("fonte"))[:15],
        ]

        for value, width in zip(values, widths):
            pdf.cell(
                width,
                7,
                value,
                border=1,
            )

        pdf.ln()

    output = pdf.output()

    if isinstance(output, bytes):
        return output

    return bytes(output)


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    st.sidebar.markdown(
        "## 🎯 FRIUL FILIERE"
    )

    st.sidebar.caption(
        "B2B LEAD ENGINE"
    )

    pagine = [
        "Dashboard",
        "Ricerca aziende",
        "Fiere",
        "Progetti investimento",
        "Lookalike",
        "Radar espansione",
        "Sales Twin",
        "Dossier",
        "Outreach",
        "CRM",
    ]

    st.session_state.pagina = st.sidebar.radio(
        "MODULI",
        pagine,
        index=pagine.index(
            st.session_state.pagina
        )
        if st.session_state.pagina in pagine
        else 0,
    )

    st.sidebar.divider()

    st.sidebar.markdown(
        "### ⚙️ Configurazione"
    )

    st.sidebar.text_input(
        "Gemini API Key (opzionale)",
        type="password",
        key="gemini_api_key",
        help=(
            "Non è necessaria per la ricerca aziende. "
            "Serve solo per dossier e testi AI."
        ),
    )

    st.sidebar.text_input(
        "Modello Gemini",
        key="gemini_model",
        value=st.session_state.get(
            "gemini_model",
            "gemini-2.5-flash",
        ),
    )

    st.sidebar.divider()

    total = len(st.session_state.leads)

    reali = sum(
        1
        for x in st.session_state.leads
        if x.get("dati_reali")
    )

    mock = total - reali

    st.sidebar.metric(
        "Lead totali",
        total,
    )

    st.sidebar.metric(
        "Lead reali",
        reali,
    )

    st.sidebar.metric(
        "Mock / demo",
        mock,
    )

    st.sidebar.divider()

    st.sidebar.info(
        "La ricerca aziende utilizza OpenStreetMap/Overpass "
        "e non richiede Google Places API Key."
    )


# ============================================================
# HEADER
# ============================================================

def header(
    title: str,
    subtitle: str = "",
):
    st.markdown(
        f'<div class="main-title">{title}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# DASHBOARD
# ============================================================

def pagina_dashboard():

    header(
        "Dashboard",
        "Panoramica del motore commerciale.",
    )

    leads = st.session_state.leads

    total = len(leads)

    reali = sum(
        1 for x in leads
        if x.get("dati_reali")
    )

    qualificati = sum(
        1 for x in leads
        if x.get("stato") == "Qualificato"
    )

    clienti = sum(
        1 for x in leads
        if x.get("stato") == "Cliente"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Lead totali", total)

    with c2:
        st.metric("Dati reali", reali)

    with c3:
        st.metric("Qualificati", qualificati)

    with c4:
        st.metric("Clienti", clienti)

    st.divider()

    if not leads:
        st.info(
            "Nessun lead presente. Vai su 'Ricerca aziende' "
            "per iniziare."
        )
        return

    df = prepara_dataframe(leads)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Lead per settore")

        sector_counts = (
            df["settore"]
            .value_counts()
            .rename_axis("Settore")
            .reset_index(name="Lead")
        )

        st.dataframe(
            sector_counts,
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.subheader("Lead per stato")

        status_counts = (
            df["stato"]
            .value_counts()
            .rename_axis("Stato")
            .reset_index(name="Lead")
        )

        st.dataframe(
            status_counts,
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Top lead")

    top = (
        df.sort_values(
            "score",
            ascending=False,
        )
        .head(10)
    )

    st.dataframe(
        top[
            [
                "nome",
                "settore",
                "citta",
                "score",
                "classe",
                "stato",
                "fonte",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# RICERCA
# ============================================================

def pagina_ricerca():

    header(
        "Ricerca aziende",
        "Ricerca di aziende reali tramite OpenStreetMap / Overpass.",
    )

    st.success(
        "✓ Nessuna API key necessaria"
    )

    with st.form("form_ricerca"):

        c1, c2 = st.columns(2)

        with c1:
            settore = st.selectbox(
                "Settore",
                SETTORI,
            )

            paese = st.selectbox(
                "Paese",
                PAESI,
            )

            regione = st.selectbox(
                "Regione",
                REGIONI_ITALIA,
            )

        with c2:
            citta = st.text_input(
                "Città (opzionale)",
                placeholder="es. Udine",
            )

            numero = st.slider(
                "Numero massimo aziende",
                min_value=5,
                max_value=100,
                value=25,
                step=5,
            )

            usa_reale = st.checkbox(
                "Usa ricerca reale OpenStreetMap",
                value=True,
            )

        submitted = st.form_submit_button(
            "🔎 CERCA AZIENDE",
            use_container_width=True,
        )

    if not submitted:
        return

    with st.spinner(
        "Ricerca aziende in corso..."
    ):

        if usa_reale:

            try:
                results = cerca_aziende_reali(
                    settore=settore,
                    paese=paese,
                    regione=regione,
                    citta=citta,
                    numero=numero,
                )

                if not results:
                    st.warning(
                        "Nessuna azienda trovata con questi parametri."
                    )
                    return

            except Exception as exc:

                st.error(
                    f"Errore durante la ricerca: {exc}"
                )

                st.info(
                    "Puoi riprovare modificando area o settore."
                )

                return

        else:

            results = [
                genera_mock_lead(
                    settore,
                    paese,
                    i + 1,
                )
                for i in range(numero)
            ]

    st.session_state.ultimo_risultato_ricerca = results

    st.success(
        f"Trovate {len(results)} aziende."
    )

    st.subheader("Risultati")

    for lead in results:

        with st.container():

            st.markdown(
                f"""
                <div class="lead-card">
                    <div>
                        <strong>{lead.get("nome")}</strong>
                        &nbsp;&nbsp;
                        {source_badge(lead)}
                    </div>

                    <div class="small-muted">
                        {lead.get("settore")} ·
                        {lead.get("citta")} ·
                        {lead.get("dimensione")}
                    </div>

                    <div>
                        Score:
                        <strong>{lead.get("score")}/100</strong>
                        · Classe {lead.get("classe")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if results:

        st.divider()

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "➕ Aggiungi tutti al CRM",
                use_container_width=True,
            ):
                added = aggiungi_leads(results)

                st.success(
                    f"{added} nuovi lead aggiunti al CRM."
                )

        with c2:
            csv = export_csv(results)

            st.download_button(
                "⬇️ Scarica CSV",
                data=csv,
                file_name="lead_osm.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ============================================================
# FILTRI CRM
# ============================================================

def filtra_leads(
    leads: List[Dict[str, Any]],
    ricerca: str = "",
    settore: str = "Tutti",
    stato: str = "Tutti",
    classe: str = "Tutte",
    solo_reali: bool = False,
) -> List[Dict[str, Any]]:

    result = []

    ricerca_norm = normalizza_testo(ricerca)

    for lead in leads:

        if ricerca_norm:
            searchable = normalizza_testo(
                " ".join(
                    [
                        safe_str(lead.get("nome")),
                        safe_str(lead.get("citta")),
                        safe_str(lead.get("settore")),
                        safe_str(lead.get("sito")),
                    ]
                )
            )

            if ricerca_norm not in searchable:
                continue

        if settore != "Tutti":
            if lead.get("settore") != settore:
                continue

        if stato != "Tutti":
            if lead.get("stato") != stato:
                continue

        if classe != "Tutte":
            if lead.get("classe") != classe:
                continue

        if solo_reali and not lead.get("dati_reali"):
            continue

        result.append(lead)

    return result


# ============================================================
# CRM
# ============================================================

def pagina_crm():

    header(
        "CRM Lead",
        "Gestione, filtraggio e aggiornamento dei prospect.",
    )

    if not st.session_state.leads:
        st.info(
            "Il CRM è vuoto."
        )
        return

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        ricerca = st.text_input(
            "Cerca",
            placeholder="azienda, città, settore...",
        )

    with c2:
        settore = st.selectbox(
            "Settore",
            ["Tutti"] + SETTORI,
        )

    with c3:
        stato = st.selectbox(
            "Stato",
            ["Tutti"] + STATI_LEAD,
        )

    with c4:
        classe = st.selectbox(
            "Classe",
            ["Tutte", "A", "B", "C", "D"],
        )

    solo_reali = st.checkbox(
        "Mostra solo dati reali",
        value=False,
    )

    filtered = filtra_leads(
        st.session_state.leads,
        ricerca=ricerca,
        settore=settore,
        stato=stato,
        classe=classe,
        solo_reali=solo_reali,
    )

    st.write(
        f"**{len(filtered)}** lead visualizzati"
    )

    if not filtered:
        st.warning(
            "Nessun lead corrisponde ai filtri."
        )
        return

    for lead in filtered:

        with st.expander(
            f'{lead.get("nome")} — '
            f'Score {lead.get("score")}/100'
        ):

            c1, c2 = st.columns(2)

            with c1:

                st.write(
                    f"**Settore:** {lead.get('settore')}"
                )

                st.write(
                    f"**Paese:** {lead.get('paese')}"
                )

                st.write(
                    f"**Città:** {lead.get('citta')}"
                )

                st.write(
                    f"**Indirizzo:** {lead.get('indirizzo')}"
                )

                st.write(
                    f"**Telefono:** {lead.get('telefono') or 'Da verificare'}"
                )

            with c2:

                st.write(
                    f"**Sito:** {lead.get('sito') or 'Da verificare'}"
                )

                st.write(
                    f"**Tecnologia:** {lead.get('tecnologia')}"
                )

                st.write(
                    f"**Fonte:** {lead.get('fonte')}"
                )

                st.write(
                    f"**Classe:** {lead.get('classe')}"
                )

                new_status = st.selectbox(
                    "Stato CRM",
                    STATI_LEAD,
                    index=(
                        STATI_LEAD.index(
                            lead.get("stato")
                        )
                        if lead.get("stato") in STATI_LEAD
                        else 0
                    ),
                    key=f"status_{lead.get('id')}",
                )

                if new_status != lead.get("stato"):

                    lead["stato"] = new_status

                    st.rerun()

            st.caption(
                lead.get("note", "")
            )

    st.divider()

    csv = export_csv(filtered)

    st.download_button(
        "⬇️ Esporta CSV",
        data=csv,
        file_name="friul_filiere_leads.csv",
        mime="text/csv",
    )

    try:
        pdf = export_pdf_lista_lead(filtered)

        st.download_button(
            "📄 Esporta PDF",
            data=pdf,
            file_name="friul_filiere_leads.pdf",
            mime="application/pdf",
        )

    except Exception as exc:
        st.warning(
            f"PDF non disponibile: {exc}"
        )

    st.divider()

    if st.button(
        "🗑️ Svuota database",
        type="secondary",
    ):

        st.session_state.confirm_delete = True

    if st.session_state.get(
        "confirm_delete",
        False,
    ):

        st.warning(
            "Questa operazione eliminerà tutti i lead."
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "Conferma eliminazione",
                type="primary",
            ):
                st.session_state.leads = []
                st.session_state.next_id = 1
                st.session_state.confirm_delete = False
                st.session_state.dossier_cache = {}
                st.session_state.email_cache = {}

                st.success(
                    "Database svuotato."
                )

                st.rerun()

        with c2:
            if st.button(
                "Annulla",
            ):
                st.session_state.confirm_delete = False
                st.rerun()


# ============================================================
# DOSSIER PAGE
# ============================================================

def pagina_dossier():

    header(
        "Dossier aziendale",
        "Analisi commerciale del singolo lead.",
    )

    leads = st.session_state.leads

    if not leads:
        st.info(
            "Aggiungi prima alcuni lead al CRM."
        )
        return

    options = {
        f'{x.get("nome")} — #{x.get("id")}': x
        for x in leads
    }

    selected_label = st.selectbox(
        "Seleziona azienda",
        list(options.keys()),
    )

    lead = options[selected_label]

    st.markdown(
        f"### {lead.get('nome')}"
    )

    st.write(
        f"Score: **{lead.get('score')}/100**"
    )

    if st.button(
        "🧠 Genera dossier",
        use_container_width=True,
    ):

        with st.spinner(
            "Generazione dossier..."
        ):
            dossier = genera_dossier(lead)

        st.markdown(dossier)

    else:

        if str(lead.get("id")) in st.session_state.dossier_cache:
            st.markdown(
                st.session_state.dossier_cache[
                    str(lead.get("id"))
                ]
            )
        else:
            st.info(
                "Premi il pulsante per generare il dossier."
            )


# ============================================================
# OUTREACH
# ============================================================

def pagina_outreach():

    header(
        "Outreach",
        "Sequenze commerciali personalizzate.",
    )

    leads = st.session_state.leads

    if not leads:
        st.info(
            "Nessun lead disponibile."
        )
        return

    options = {
        f'{x.get("nome")} — #{x.get("id")}': x
        for x in leads
    }

    selected = st.selectbox(
        "Azienda",
        list(options.keys()),
    )

    lead = options[selected]

    if st.button(
        "✉️ Genera sequenza",
        use_container_width=True,
    ):

        with st.spinner(
            "Preparazione sequenza..."
        ):

            sequence = genera_email_sequence(
                lead
            )

        for email in sequence:

            st.markdown(
                f"### Giorno {email.get('giorno', 0)}"
            )

            st.text_input(
                "Oggetto",
                value=safe_str(
                    email.get("oggetto")
                ),
                key=f"subject_{lead.get('id')}_{email.get('giorno')}",
            )

            st.text_area(
                "Testo",
                value=safe_str(
                    email.get("testo")
                ),
                height=220,
                key=f"body_{lead.get('id')}_{email.get('giorno')}",
            )


# ============================================================
# LOOKALIKE
# ============================================================

def pagina_lookalike():

    header(
        "Lookalike",
        "Trova aziende simili partendo da un settore o da un lead.",
    )

    if not st.session_state.leads:

        st.info(
            "Puoi iniziare scegliendo direttamente un settore."
        )

        settore = st.selectbox(
            "Settore di riferimento",
            SETTORI,
        )

    else:

        options = {
            f'{x.get("nome")} — {x.get("settore")}': x
            for x in st.session_state.leads
        }

        selected = st.selectbox(
            "Azienda di riferimento",
            list(options.keys()),
        )

        lead = options[selected]
        settore = lead.get("settore", "Altro")

        st.write(
            f"Settore utilizzato: **{settore}**"
        )

    paese = st.selectbox(
        "Paese",
        PAESI,
        key="lookalike_country",
    )

    regione = st.selectbox(
        "Regione",
        REGIONI_ITALIA,
        key="lookalike_region",
    )

    if st.button(
        "🔍 Trova aziende simili",
        use_container_width=True,
    ):

        try:

            results = cerca_aziende_reali(
                settore,
                paese,
                regione,
                "",
                30,
            )

            if results:

                st.success(
                    f"Trovate {len(results)} aziende."
                )

                st.dataframe(
                    prepara_dataframe(results)[
                        [
                            "nome",
                            "settore",
                            "citta",
                            "dimensione",
                            "tecnologia",
                            "score",
                            "fonte",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                if st.button(
                    "➕ Aggiungi al CRM",
                    key="add_lookalike",
                ):

                    added = aggiungi_leads(results)

                    st.success(
                        f"{added} lead aggiunti."
                    )

            else:
                st.warning(
                    "Nessun risultato."
                )

        except Exception as exc:

            st.error(
                f"Ricerca non riuscita: {exc}"
            )


# ============================================================
# MODULI MOCK / ROADMAP
# ============================================================

def pagina_fiere():

    header(
        "Fiere",
        "Radar fiere e manifestazioni B2B.",
    )

    fairs = [
        {
            "evento": "MECSPE",
            "settore": "Manifattura",
            "paese": "Italia",
        },
        {
            "evento": "SPS Italia",
            "settore": "Automazione",
            "paese": "Italia",
        },
        {
            "evento": "A&T",
            "settore": "Tecnologia",
            "paese": "Italia",
        },
    ]

    st.dataframe(
        pd.DataFrame(fairs),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Modulo informativo/demo: gli eventi devono essere "
        "verificati prima dell'utilizzo commerciale."
    )


def pagina_progetti():

    header(
        "Progetti investimento",
        "Individuazione preliminare di segnali di investimento.",
    )

    st.info(
        "Questo modulo è predisposto per integrare in futuro "
        "fonti open-data su bandi, investimenti e progetti industriali."
    )

    projects = pd.DataFrame(
        [
            {
                "Azienda": "Esempio demo",
                "Area": "Friuli-Venezia Giulia",
                "Tema": "Automazione",
                "Fonte": "DEMO",
            }
        ]
    )

    st.dataframe(
        projects,
        use_container_width=True,
        hide_index=True,
    )


def pagina_radar_espansione():

    header(
        "Radar espansione",
        "Monitoraggio di potenziali aree di espansione.",
    )

    st.info(
        "Modulo predisposto per essere collegato a fonti "
        "open-data territoriali e aziendali."
    )

    regions = pd.DataFrame(
        [
            {
                "Area": "Friuli-Venezia Giulia",
                "Priorità": "Alta",
                "Motivo": "Area target",
            },
            {
                "Area": "Veneto",
                "Priorità": "Alta",
                "Motivo": "Alta densità industriale",
            },
            {
                "Area": "Lombardia",
                "Priorità": "Media",
                "Motivo": "Ampio mercato",
            },
        ]
    )

    st.dataframe(
        regions,
        use_container_width=True,
        hide_index=True,
    )


def pagina_sales_twin():

    header(
        "Sales Twin",
        "Profilazione del prospect e prossima azione commerciale.",
    )

    if not st.session_state.leads:
        st.info(
            "Aggiungi almeno un lead al CRM."
        )
        return

    options = {
        f'{x.get("nome")} — #{x.get("id")}': x
        for x in st.session_state.leads
    }

    selected = st.selectbox(
        "Lead",
        list(options.keys()),
    )

    lead = options[selected]

    score = lead.get("score", 0)

    st.metric(
        "Lead score",
        f"{score}/100",
    )

    if score >= 85:
        action = "Contatto commerciale prioritario"
    elif score >= 70:
        action = "Qualificare telefonicamente"
    elif score >= 55:
        action = "Arricchire dati"
    else:
        action = "Mantenere in nurturing"

    st.markdown(
        f"### Prossima azione consigliata\n\n**{action}**"
    )

    st.write(
        "Tecnologia:",
        lead.get("tecnologia"),
    )

    st.write(
        "Dimensione:",
        lead.get("dimensione"),
    )

    st.write(
        "Presenza sito:",
        "Sì" if lead.get("sito") else "No / da verificare",
    )

    st.write(
        "Presenza telefono:",
        "Sì" if lead.get("telefono") else "No / da verificare",
    )


# ============================================================
# ROUTER
# ============================================================

def main():

    sidebar()

    page = st.session_state.pagina

    if page == "Dashboard":
        pagina_dashboard()

    elif page == "Ricerca aziende":
        pagina_ricerca()

    elif page == "Fiere":
        pagina_fiere()

    elif page == "Progetti investimento":
        pagina_progetti()

    elif page == "Lookalike":
        pagina_lookalike()

    elif page == "Radar espansione":
        pagina_radar_espansione()

    elif page == "Sales Twin":
        pagina_sales_twin()

    elif page == "Dossier":
        pagina_dossier()

    elif page == "Outreach":
        pagina_outreach()

    elif page == "CRM":
        pagina_crm()


if __name__ == "__main__":
    main()
