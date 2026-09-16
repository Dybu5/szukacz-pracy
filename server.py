import sys
from flask import Flask, jsonify, send_from_directory, request

from fetch_jobs import get_jobs
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
<meta name="theme-color" content="#0f172a">
<link rel="manifest" href="/manifest.json">
<title>Szukacz Pracy</title>
<style>
    body {
        margin: 0;
        padding: 24px 16px;
        background: #0f172a;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    h1 {
        font-size: 28px;
        margin: 0 0 24px 0;
        text-align: center;
    }
    button {
        display: block;
        width: 100%;
        max-width: 400px;
        margin: 0 auto 24px auto;
        padding: 18px;
        font-size: 18px;
        font-weight: bold;
        color: #0f172a;
        background: #38bdf8;
        border: none;
        border-radius: 12px;
    }
    button:active {
        background: #0ea5e9;
    }
    #wyniki {
        max-width: 500px;
        margin: 0 auto;
    }
    .karta {
        background: #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .karta h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
    }
    .karta p {
        margin: 4px 0;
        font-size: 15px;
        color: #cbd5e1;
    }
    .karta a {
        color: #38bdf8;
    }
    .info {
        text-align: center;
        color: #94a3b8;
    }
</style>
</head>
<body>
<h1>Szukacz Pracy</h1>
<button id="szukaj-btn">Szukaj ofert</button>
<div id="wyniki"></div>

<script>
document.getElementById("szukaj-btn").addEventListener("click", async () => {
    const wyniki = document.getElementById("wyniki");
    wyniki.innerHTML = "<p class=\\"info\\">Szukam...</p>";

    try {
        const response = await fetch("/api/report");
        const oferty = await response.json();

        if (oferty.length === 0) {
            wyniki.innerHTML = "<p class=\\"info\\">Dziś nic nie znaleziono.</p>";
            return;
        }

        wyniki.innerHTML = oferty.map(oferta => `
            <div class="karta">
                <h3>${oferta.title}</h3>
                <p>${oferta.company}</p>
                <p>${oferta.powod}</p>
                <p><a href="${oferta.link}" target="_blank">Zobacz ofertę</a></p>
            </div>
        `).join("");
    } catch (err) {
        wyniki.innerHTML = "<p class=\\"info\\">Błąd podczas wyszukiwania.</p>";
    }
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return INDEX_HTML


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/api/report")
def api_report():
    if get_last_search_time() is None:
        jobs = get_jobs()
    else:
        jobs = get_jobs(max_days_old=1)

    oceny = evaluate_jobs(jobs)

    wyniki = []
    for ocena in oceny:
        if ocena["pasuje"]:
            job = jobs[ocena["id"]]
            wyniki.append({
                "title": job["title"],
                "company": job.get("company", {}).get("display_name", "?"),
                "powod": ocena["powod"],
                "link": job["redirect_url"],
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
