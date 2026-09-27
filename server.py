import sys
from flask import Flask, jsonify, send_from_directory, request

from fetch_jobs import get_jobs
from fetch_jobs_jooble import get_jobs_jooble
from filter_jobs import evaluate_jobs
from db import init_db, save_jobs, get_last_search_time, get_history, toggle_favorite

sys.stdout.reconfigure(encoding="utf-8")

init_db()

app = Flask(__name__)

INDEX_HTML = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0a0a0a">
<link rel="manifest" href="/manifest.json">
<title>Szukacz Pracy</title>
<style>
    :root {
        --bg: #0a0a0a;
        --card: #1a1a1a;
        --border: #2a2a2a;
        --accent: #d4ff3f;
        --text: #f5f5f5;
        --text-dim: #9a9a9a;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0;
        padding: 20px 16px 40px 16px;
        background: var(--bg);
        color: var(--text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .kontener {
        max-width: 480px;
        margin: 0 auto;
    }
    .pasek-gorny {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    h1 {
        font-size: 24px;
        margin: 0;
    }
    button {
        font-family: inherit;
        cursor: pointer;
    }
    #szukaj-btn {
        border: none;
        border-radius: 999px;
        background: var(--accent);
        color: #0a0a0a;
        font-weight: 700;
        font-size: 15px;
        padding: 12px 22px;
    }
    #szukaj-btn:disabled {
        opacity: 0.6;
    }
    #status {
        margin: -8px 0 16px 0;
        font-size: 13px;
        color: #fca5a5;
    }
    .zakladki {
        display: flex;
        background: var(--card);
        border-radius: 999px;
        padding: 4px;
        gap: 4px;
    }
    .zakladka {
        flex: 1;
        border: none;
        background: transparent;
        color: var(--text-dim);
        font-size: 14px;
        font-weight: 600;
        padding: 10px 8px;
        border-radius: 999px;
    }
    .zakladka.aktywna {
        background: var(--accent);
        color: #0a0a0a;
    }
    #pole-szukaj {
        margin-top: 12px;
    }
    #pole-szukaj-input {
        width: 100%;
        border: 1px solid var(--border);
        background: var(--card);
        color: var(--text);
        border-radius: 999px;
        padding: 12px 18px;
        font-size: 15px;
    }
    #pole-szukaj-input:focus {
        outline: 1px solid var(--accent);
    }
    .sortowanie {
        display: flex;
        gap: 8px;
        margin-top: 16px;
    }
    .chip {
        border: none;
        background: var(--card);
        color: var(--text-dim);
        font-size: 13px;
        font-weight: 600;
        padding: 7px 16px;
        border-radius: 999px;
    }
    .chip.aktywna {
        background: var(--accent);
        color: #0a0a0a;
    }
    #lista {
        margin-top: 20px;
    }
    .karta {
        background: var(--card);
        border-radius: 24px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
    }
    .karta-glowka {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .etykieta-zrodlo {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.3px;
        padding: 4px 10px;
        border-radius: 999px;
    }
    .zrodlo-adzuna {
        background: rgba(56, 189, 248, 0.15);
        color: #7dd3fc;
    }
    .zrodlo-jooble {
        background: rgba(192, 132, 252, 0.18);
        color: #d8b4fe;
    }
    .etykiety {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }
    .kategoria-informatyka {
        background: rgba(212, 255, 63, 0.16);
        color: var(--accent);
    }
    .kategoria-pokrewna {
        background: rgba(255, 255, 255, 0.08);
        color: var(--text-dim);
    }
    .karta h3 {
        margin: 0 8px 4px 0;
        font-size: 18px;
        line-height: 1.3;
    }
    .karta .firma {
        margin: 0 0 10px 0;
        color: var(--text-dim);
        font-size: 14px;
    }
    .karta .powod {
        margin: 0 0 14px 0;
        font-size: 14px;
        line-height: 1.45;
        color: var(--text);
    }
    .stopka {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stopka .data {
        font-size: 12px;
        color: var(--text-dim);
    }
    .stopka a {
        color: var(--accent);
        font-size: 14px;
        font-weight: 700;
        text-decoration: none;
    }
    .gwiazdka {
        flex-shrink: 0;
        border: none;
        background: transparent;
        padding: 4px;
        color: var(--text-dim);
        line-height: 0;
    }
    .gwiazdka.aktywna {
        color: var(--accent);
    }
    .info {
        text-align: center;
        color: var(--text-dim);
        padding: 24px 0;
    }
</style>
</head>
<body>
<div class="kontener">

    <div class="pasek-gorny">
        <h1>Szukacz Pracy</h1>
        <button id="szukaj-btn">Szukaj</button>
    </div>

    <p id="status" hidden></p>

    <div class="zakladki">
        <button class="zakladka aktywna" data-tab="wszystkie">Wszystkie</button>
        <button class="zakladka" data-tab="ulubione">Ulubione</button>
        <button class="zakladka" data-tab="szukaj">Szukaj</button>
    </div>

    <div id="pole-szukaj" hidden>
        <input id="pole-szukaj-input" type="text" placeholder="Szukaj po tytule lub firmie...">
    </div>

    <div class="sortowanie">
        <button class="chip aktywna" data-sort="data_znalezienia">Data</button>
        <button class="chip" data-sort="company">Firma</button>
        <button class="chip" data-sort="title">Tytuł</button>
    </div>

    <div class="sortowanie">
        <button class="chip zrodlo-chip aktywna" data-source="wszystkie">Wszystkie źródła</button>
        <button class="chip zrodlo-chip" data-source="adzuna">Adzuna</button>
        <button class="chip zrodlo-chip" data-source="jooble">Jooble</button>
    </div>

    <div class="sortowanie">
        <button class="chip kategoria-chip aktywna" data-kategoria="wszystkie">Wszystkie</button>
        <button class="chip kategoria-chip" data-kategoria="informatyka">Informatyka</button>
        <button class="chip kategoria-chip" data-kategoria="pokrewna">Pokrewne</button>
    </div>

    <div id="lista"></div>

</div>

<script>
const stan = {
    zakladka: "wszystkie",
    sort: "data_znalezienia",
    szukaj: "",
    zrodlo: "wszystkie",
    kategoria: "wszystkie",
};

let ostatnieOferty = [];

function zastosujFiltry(oferty) {
    return oferty.filter(o => {
        if (stan.zrodlo !== "wszystkie" && o.source !== stan.zrodlo) return false;
        if (stan.kategoria !== "wszystkie" && o.kategoria !== stan.kategoria) return false;
        return true;
    });
}

function escapeHtml(str) {
    return String(str ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

// Linki pochodzą z zewnętrznych API - przepuszczamy tylko http(s),
// żeby ogłoszenie nie mogło podsunąć np. "javascript:...".
function bezpiecznyLink(url) {
    try {
        const u = new URL(url);
        if (u.protocol === "http:" || u.protocol === "https:") return escapeHtml(u.href);
    } catch (err) {}
    return "#";
}

function formatData(iso) {
    const miesiace = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"];
    const d = new Date(iso.replace(" ", "T") + "Z");
    if (isNaN(d.getTime())) return iso;
    const dzien = d.getDate();
    const miesiac = miesiace[d.getMonth()];
    const godziny = String(d.getHours()).padStart(2, "0");
    const minuty = String(d.getMinutes()).padStart(2, "0");
    return `${dzien} ${miesiac}, ${godziny}:${minuty}`;
}

function ikonaGwiazdki(wypelniona) {
    if (wypelniona) {
        return '<svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.9-6.2 3.9 1.6-7L2 9.2l7.1-.6z"/></svg>';
    }
    return '<svg viewBox="0 0 24 24" width="22" height="22"><path fill="none" stroke="currentColor" stroke-width="2" d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.9-6.2 3.9 1.6-7L2 9.2l7.1-.6z"/></svg>';
}

function etykietaZrodla(source) {
    const jestJooble = source === "jooble";
    const klasa = jestJooble ? "zrodlo-jooble" : "zrodlo-adzuna";
    const nazwa = jestJooble ? "Jooble" : "Adzuna";
    return `<span class="etykieta-zrodlo ${klasa}">${nazwa}</span>`;
}

function etykietaKategorii(kategoria) {
    const jestIt = kategoria === "informatyka";
    const klasa = jestIt ? "kategoria-informatyka" : "kategoria-pokrewna";
    const nazwa = jestIt ? "Informatyka" : "Pokrewna";
    return `<span class="etykieta-zrodlo ${klasa}">${nazwa}</span>`;
}

function kartaHtml(oferta) {
    return `
    <div class="karta" data-id="${oferta.id}">
        <div class="karta-glowka">
            <div class="etykiety">
                ${etykietaZrodla(oferta.source)}
                ${etykietaKategorii(oferta.kategoria)}
            </div>
            <button class="gwiazdka ${oferta.ulubione ? "aktywna" : ""}" data-id="${oferta.id}" aria-label="Ulubione">
                ${ikonaGwiazdki(oferta.ulubione)}
            </button>
        </div>
        <h3>${escapeHtml(oferta.title)}</h3>
        <p class="firma">${escapeHtml(oferta.company)}</p>
        <p class="powod">${escapeHtml(oferta.powod)}</p>
        <div class="stopka">
            <span class="data">${formatData(oferta.data_znalezienia)}</span>
            <a href="${bezpiecznyLink(oferta.link)}" target="_blank" rel="noopener noreferrer">Zobacz ofertę →</a>
        </div>
    </div>`;
}

function renderujListe(oferty) {
    const listaEl = document.getElementById("lista");
    if (oferty.length === 0) {
        listaEl.innerHTML = '<p class="info">Brak wyników.</p>';
        return;
    }
    listaEl.innerHTML = oferty.map(kartaHtml).join("");
    listaEl.querySelectorAll(".gwiazdka").forEach(el => {
        el.addEventListener("click", onKliknijGwiazdke);
    });
}

async function wczytajHistorie() {
    const params = new URLSearchParams();
    params.set("sort", stan.sort);
    if (stan.zakladka === "ulubione") params.set("favorites", "true");
    if (stan.zakladka === "szukaj" && stan.szukaj.trim()) params.set("search", stan.szukaj.trim());

    try {
        const resp = await fetch("/api/history?" + params.toString());
        const oferty = await resp.json();
        ostatnieOferty = oferty;
        renderujListe(zastosujFiltry(oferty));
    } catch (err) {
        document.getElementById("lista").innerHTML = '<p class="info">Błąd wczytywania listy.</p>';
    }
}

async function onKliknijGwiazdke(e) {
    const btn = e.currentTarget;
    const id = btn.dataset.id;
    const bylaAktywna = btn.classList.contains("aktywna");

    btn.classList.toggle("aktywna");
    btn.innerHTML = ikonaGwiazdki(!bylaAktywna);

    try {
        await fetch(`/api/favorite/${id}`, { method: "POST" });
    } catch (err) {
        btn.classList.toggle("aktywna");
        btn.innerHTML = ikonaGwiazdki(bylaAktywna);
    }
}

document.querySelectorAll(".zakladka").forEach(btn => {
    btn.addEventListener("click", () => {
        stan.zakladka = btn.dataset.tab;
        document.querySelectorAll(".zakladka").forEach(b => b.classList.toggle("aktywna", b === btn));
        document.getElementById("pole-szukaj").hidden = stan.zakladka !== "szukaj";
        if (stan.zakladka === "szukaj") {
            document.getElementById("pole-szukaj-input").focus();
        }
        wczytajHistorie();
    });
});

document.querySelectorAll(".chip[data-sort]").forEach(btn => {
    btn.addEventListener("click", () => {
        stan.sort = btn.dataset.sort;
        document.querySelectorAll(".chip[data-sort]").forEach(b => b.classList.toggle("aktywna", b === btn));
        wczytajHistorie();
    });
});

document.querySelectorAll(".zrodlo-chip").forEach(btn => {
    btn.addEventListener("click", () => {
        stan.zrodlo = btn.dataset.source;
        document.querySelectorAll(".zrodlo-chip").forEach(b => b.classList.toggle("aktywna", b === btn));
        renderujListe(zastosujFiltry(ostatnieOferty));
    });
});

document.querySelectorAll(".kategoria-chip").forEach(btn => {
    btn.addEventListener("click", () => {
        stan.kategoria = btn.dataset.kategoria;
        document.querySelectorAll(".kategoria-chip").forEach(b => b.classList.toggle("aktywna", b === btn));
        renderujListe(zastosujFiltry(ostatnieOferty));
    });
});

let debounceTimer;
document.getElementById("pole-szukaj-input").addEventListener("input", (e) => {
    stan.szukaj = e.target.value;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(wczytajHistorie, 300);
});

document.getElementById("szukaj-btn").addEventListener("click", async () => {
    const btn = document.getElementById("szukaj-btn");
    const status = document.getElementById("status");
    const oryginalnyTekst = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Szukam...";
    status.hidden = true;
    try {
        const resp = await fetch("/api/report", { method: "POST" });
        if (!resp.ok) {
            const dane = await resp.json().catch(() => ({}));
            throw new Error(dane.error || `HTTP ${resp.status}`);
        }
    } catch (err) {
        status.textContent = "Wyszukiwanie nie powiodło się: " + err.message;
        status.hidden = false;
    } finally {
        btn.disabled = false;
        btn.textContent = oryginalnyTekst;
        wczytajHistorie();
    }
});

wczytajHistorie();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return INDEX_HTML


@app.route("/manifest.json")
def manifest():
    return send_from_directory(app.static_folder, "manifest.json")


@app.route("/api/report", methods=["POST"])
def api_report():
    jobs = []
    try:
        if get_last_search_time() is None:
            jobs += get_jobs()
        else:
            jobs += get_jobs(max_days_old=1)
    except Exception as e:
        print(f"OSTRZEŻENIE: Adzuna nie odpowiedziała poprawnie: {e}")

    try:
        jobs += get_jobs_jooble()
    except Exception as e:
        print(f"OSTRZEŻENIE: Jooble nie odpowiedziało poprawnie: {e}")

    if not jobs:
        return jsonify({"error": "Żadne źródło ofert nie odpowiedziało"}), 502

    try:
        oceny = evaluate_jobs(jobs)
    except Exception as e:
        print(f"BŁĄD: ocena ofert przez Claude API nie powiodła się: {e}")
        return jsonify({"error": "Ocena ofert przez AI nie powiodła się"}), 502

    wyniki = []
    for ocena in oceny:
        # Model może zwrócić id spoza zakresu - pomijamy takie wpisy zamiast wywalać endpoint.
        idx = ocena.get("id")
        if ocena.get("pasuje") and isinstance(idx, int) and 0 <= idx < len(jobs):
            job = jobs[idx]
            wyniki.append({
                "title": job["title"],
                "company": job.get("company", {}).get("display_name", "?"),
                "powod": ocena.get("powod", ""),
                "link": job["redirect_url"],
                "source": job.get("source", "adzuna"),
                "kategoria": ocena.get("kategoria", "pokrewna"),
            })

    save_jobs(wyniki)

    return jsonify(wyniki)


@app.route("/api/history")
def api_history():
    sort_by = request.args.get("sort", "data_znalezienia")
    search = request.args.get("search", None)
    favorites = request.args.get("favorites", "false").lower() == "true"

    historia = get_history(sort_by=sort_by, search=search, only_favorites=favorites)
    return jsonify(historia)


@app.route("/api/favorite/<int:id>", methods=["POST"])
def api_favorite(id):
    toggle_favorite(id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
