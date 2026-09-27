import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()

PROFIL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profil_kandydata.txt")

try:
    with open(PROFIL_PATH, encoding="utf-8") as f:
        PROFIL = f.read()
except FileNotFoundError:
    raise RuntimeError(
        f"Brak pliku {PROFIL_PATH}. Skopiuj profil_kandydata.example.txt do "
        "profil_kandydata.txt i uzupełnij własnymi danymi (ten plik nie jest w repo - "
        "zawiera prywatne informacje o kandydacie)."
    ) from None

def evaluate_jobs(jobs):
    api_key = os.getenv("ANTHROPIC_API_KEY")

    jobs_short = [
        {"id": i, "title": j["title"], "company": j.get("company", {}).get("display_name", "?"),
         "description": j.get("description", "")[:300]}
        for i, j in enumerate(jobs)
    ]

    prompt = f"""Oto profil kandydata:
{PROFIL}

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

Zwróć WYŁĄCZNIE JSON (bez żadnego innego tekstu) w formacie:
[{{"id": 0, "pasuje": true, "powod": "krótkie uzasadnienie po polsku", "kategoria": "informatyka"}}, ...]
"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-5",
            "max_tokens": 4096,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    data = response.json()
    if "content" not in data:
        raise RuntimeError(f"Claude API: {data.get('error', data)}")
    result_text = None
    for block in data["content"]:
        if block["type"] == "text":
            result_text = block["text"]
            break
    if result_text is None:
        raise RuntimeError(f"Claude API: brak bloku tekstowego (stop_reason={data.get('stop_reason')})")
    # Model czasem owija odpowiedź w markdown code fence (```json ... ```) -
    # zdejmujemy ją przed parsowaniem JSON-a.
    result_text = result_text.strip()
    result_text = re.sub(r"^```(?:json)?\s*", "", result_text)
    result_text = re.sub(r"\s*```$", "", result_text)
    return json.loads(result_text)