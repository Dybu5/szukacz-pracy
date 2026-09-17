import os
import sys
import json
import re
import requests
from dotenv import load_dotenv
from fetch_jobs import get_jobs

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

PROFIL = """
Student I roku Mechatroniki (Politechnika Rzeszowska), szuka stażu LUB pracy (obie opcje).
Dostępność: cały rok, równolegle ze studiami (nie tylko wakacje).

Zainteresowania zawodowe (w kolejności otwartości, nie sztywnych priorytetów):
- Programowanie: backend, frontend, embedded
- Sieci / IT infrastruktura / DevOps
- Otwarty na role związane z AI w różnej formie (ML/dane, albo AI jako narzędzie w automatyzacji/DevOps) -
  nie ma jeszcze sprecyzowanej preferencji, chce zobaczyć różne opcje w tym obszarze

Umiejętności:
- Python (podstawy), C++ (Advanced Beginner)
- Git/GitHub (początkujący, pierwszy własny projekt)
- Docker (podstawy, z własnego projektu)
- AutoCAD (grafika inżynierska)
- Linux: brak doświadczenia, dopiero zaczyna
- Angielski: komunikatywny (rozmowa techniczna, mail)

Doświadczenie zawodowe:
- 3 miesiące jako elektromechanik/automatyk w Thoni Alutec - serwis i naprawa maszyn CNC.
  To dobry atut przy ofertach łączących IT z automatyką przemysłową/produkcją/IoT.

Preferencje:
- Lokalizacja: Rzeszów lub zdalnie
- Wielkość i branża firmy: bez znaczenia
- Płatność: mile widziana, ale nie kluczowa (nie odrzucaj bezpłatnych staży)
- Poziom: szuka stanowisk juniorskich/stażowych/entry-level, NIE seniorskich ani wymagających
  wieloletniego doświadczenia
- Brak dealbreakerów co do branży - najważniejsze żeby stanowisko dawało uczyć się realnie
  ciekawych, wartościowych rzeczy technicznych (nie czysty helpdesk/sprzedaż/call center bez
  strony technicznej)
"""

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
    )
    data = response.json()
    if "content" not in data:
        print("BŁĄD Z API:")
        print(data)
        raise SystemExit(1)
    result_text = None
    for block in data["content"]:
        if block["type"] == "text":
            result_text = block["text"]
            break
    if result_text is None:
        print("BRAK BLOKU TEKSTOWEGO:")
        print(data["content"])
        raise SystemExit(1)
    # Model czasem owija odpowiedź w markdown code fence (```json ... ```) -
    # zdejmujemy ją przed parsowaniem JSON-a.
    result_text = result_text.strip()
    result_text = re.sub(r"^```(?:json)?\s*", "", result_text)
    result_text = re.sub(r"\s*```$", "", result_text)
    return json.loads(result_text)

if __name__ == "__main__":
    jobs = get_jobs()
    oceny = evaluate_jobs(jobs)

    for ocena in oceny:
        if ocena["pasuje"]:
            job = jobs[ocena["id"]]
            print(f"\n✅ {job['title']} - {job.get('company', {}).get('display_name', '?')}")
            print(f"   Powód: {ocena['powod']}")
            print(f"   Link: {job['redirect_url']}")