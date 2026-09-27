import io
import json
import os
from typing import List

import anthropic
from flask import render_template
from pydantic import BaseModel
from xhtml2pdf import pisa

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "fonts").replace("\\", "/")
PROFIL_KACPRA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profil_kacpra.json")


def load_profil_kacpra():
    try:
        with open(PROFIL_KACPRA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(
            f"Brak pliku {PROFIL_KACPRA_PATH}. Skopiuj profil_kacpra.example.json do "
            "profil_kacpra.json i uzupełnij prawdziwymi danymi (ten plik nie jest w repo - "
            "zawiera dane osobowe)."
        ) from None


class WynikDopasowania(BaseModel):
    podsumowanie: str
    umiejetnosci_uporzadkowane: List[str]
    wybrane_osiagniecia: List[str]


def _dopasuj_tresc(oferta, profil):
    client = anthropic.Anthropic()

    prompt = f"""Oto oferta pracy, do której kandydat chce dopasować CV:

Tytuł: {oferta.get('title', '')}
Firma: {oferta.get('company', '')}
Opis oferty: {oferta.get('opis_oferty', '') or '(brak pełnego opisu)'}
Powód wcześniejszego dopasowania (z naszej oceny AI): {oferta.get('powod', '')}

Oto pełny, prawdziwy profil kandydata (JSON):
{profil}

Twoje zadanie - przygotuj treść CV dopasowaną do TEJ KONKRETNEJ oferty, na podstawie
WYŁĄCZNIE prawdziwych elementów z profilu powyżej. Nigdy nie wymyślaj doświadczenia,
umiejętności ani osiągnięć, których nie ma w profilu.

1. Napisz podsumowanie zawodowe (3-4 zdania), naturalnym, konkretnym językiem - bez
   sztampowych fraz typu "ambitny", "zmotywowany", "dynamiczny", "pasjonat". Użyj
   dokładnych słów kluczowych z opisu oferty tam, gdzie to szczere i zgodne z prawdą
   o kandydacie.
2. Uporządkuj umiejętności kandydata (dokładnie te z profilu, możesz zmienić TYLKO
   kolejność, nie treść) tak, żeby najbardziej trafne dla tej oferty były pierwsze.
3. Wybierz 2-3 punkty z doświadczenia lub projektów kandydata najbardziej trafne dla
   tej oferty - możesz je lekko przeredagować pod kątem tej oferty, ale bez zmyślania
   nowych faktów, liczb ani osiągnięć.

Zwróć wynik jako podsumowanie, umiejetnosci_uporzadkowane (lista stringów - dokładne
nazwy umiejętności z profilu, tylko w innej kolejności) i wybrane_osiagniecia (lista
2-3 stringów)."""

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=2048,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": prompt}],
        output_format=WynikDopasowania,
    )
    return response.parsed_output


def generate_cv(oferta: dict, profil: dict) -> bytes:
    """Generuje CV (PDF jako bytes) dopasowane do konkretnej oferty, na bazie
    prawdziwego profilu kandydata. Wywołuje Claude API - kosztuje tyle co jedna ocena
    ofert."""
    dopasowanie = _dopasuj_tresc(oferta, json.dumps(profil, ensure_ascii=False))

    html = render_template(
        "cv_template.html",
        profil=profil,
        dopasowanie=dopasowanie,
        fonts_dir=FONTS_DIR,
    )

    buf = io.BytesIO()
    wynik = pisa.CreatePDF(html, dest=buf)
    if wynik.err:
        raise RuntimeError(f"Błąd renderowania PDF (xhtml2pdf), kod: {wynik.err}")
    return buf.getvalue()
