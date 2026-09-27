import sys
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

from cv_generator import generate_cv, load_profil_kacpra
from db import (
    DOZWOLONE_STATUSY,
    get_history,
    get_offer_by_id,
    init_db,
    toggle_favorite,
    update_notatka,
    update_status,
)
from search import wykonaj_wyszukiwanie
from utils import content_disposition_pdf

init_db()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(app.static_folder, "manifest.json")


@app.route("/api/report", methods=["POST"])
def api_report():
    try:
        wyniki = wykonaj_wyszukiwanie()
    except Exception as e:
        print(f"BŁĄD: wyszukiwanie ofert nie powiodło się: {e}")
        return jsonify({"error": str(e)}), 502

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


@app.route("/api/status/<int:id>", methods=["POST"])
def api_status(id):
    dane = request.get_json(silent=True) or {}
    status = dane.get("status")
    if status not in DOZWOLONE_STATUSY:
        return jsonify({"error": f"Nieprawidłowy status, dozwolone: {DOZWOLONE_STATUSY}"}), 400
    update_status(id, status)
    return jsonify({"ok": True})


@app.route("/api/notatka/<int:id>", methods=["POST"])
def api_notatka(id):
    dane = request.get_json(silent=True) or {}
    update_notatka(id, dane.get("notatka", ""))
    return jsonify({"ok": True})


@app.route("/api/generate-cv/<int:id>", methods=["POST"])
def api_generate_cv(id):
    oferta = get_offer_by_id(id)
    if oferta is None:
        return jsonify({"error": "Nie znaleziono oferty o takim id"}), 404

    try:
        profil = load_profil_kacpra()
        pdf_bytes = generate_cv(oferta, profil)
    except Exception as e:
        print(f"BŁĄD: generowanie CV nie powiodło się: {e}")
        return jsonify({"error": str(e)}), 502

    nazwa_pliku = f"CV_{oferta['title']}".replace(" ", "_").replace("/", "-")[:80] + ".pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": content_disposition_pdf(nazwa_pliku)},
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    app.run(host="0.0.0.0", port=5000)
