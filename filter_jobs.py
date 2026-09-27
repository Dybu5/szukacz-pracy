import json
import os
from typing import List, Literal

import anthropic
from pydantic import BaseModel

PROFIL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profil_kandydata.txt")


def load_profil():
    try:
        with open(PROFIL_PATH, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(
            f"Brak pliku {PROFIL_PATH}. Skopiuj profil_kandydata.example.txt do "
            "profil_kandydata.txt i uzupełnij własnymi danymi (ten plik nie jest w repo - "
            "zawiera prywatne informacje o kandydacie)."
        ) from None


class OcenaOferty(BaseModel):
    id: int
    pasuje: bool
    powod: str
    kategoria: Literal["informatyka", "pokrewna"]


class WynikOceny(BaseModel):
    oceny: List[OcenaOferty]


def evaluate_jobs(jobs):
    profil = load_profil()
    client = anthropic.Anthropic()  # klucz z ANTHROPIC_API_KEY w środowisku

    jobs_short = [
        {"id": i, "title": j["title"], "company": j.get("company", {}).get("display_name", "?"),
         "description": j.get("description", "")[:300]}
        for i, j in enumerate(jobs)
    ]

    prompt = f"""Oto profil kandydata:
{profil}

Oto lista ofert pracy (JSON):
{json.dumps(jobs_short, ensure_ascii=False)}

Dla każdej oferty oceń czy pasuje do profilu (staż/junior, zgodna z zainteresowaniami).
Oceń też kategorię oferty - to rozstrzygnięcie binarne, wybierz "informatyka" ZAWSZE gdy
stanowisko choćby częściowo dotyczy któregokolwiek z: programowania (dowolny język),
sieci komputerowych/telekomunikacyjnych, infrastruktury IT, DevOps, chmury, cyberbezpieczeństwa,
wsparcia IT/helpdesk, analizy danych, systemów informatycznych, testowania oprogramowania.
Przykłady które MUSZĄ dostać "informatyka": "Inżynier ds. Sieci Szkieletowej", "IT Support
Specialist", "Technology Risk Intern", "Junior AML Analyst" (jeśli opis wspomina systemy/dane),
"Cybersecurity Intern", "Data Engineer".

Wybierz "pokrewna" TYLKO gdy stanowisko jest czysto mechaniczne/elektryczne/produkcyjne bez
JAKIEGOKOLWIEK elementu IT/sieci/oprogramowania - np. "Inżynier Serwisu" (naprawa sprzętu
fizycznego bez software'u), "Technik wózków widłowych", czysto produkcyjne stanowiska.

W razie wątpliwości między "informatyka" a "pokrewna" - wybierz "informatyka".

Dla każdej oferty z listy podaj ocenę (id musi odpowiadać polu "id" z listy ofert powyżej)."""

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=4096,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": prompt}],
        output_format=WynikOceny,
    )

    return [ocena.model_dump() for ocena in response.parsed_output.oceny]
