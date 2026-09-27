const stan = {
    zakladka: "wszystkie",
    sort: "data_znalezienia",
    szukaj: "",
    zrodlo: "wszystkie",
    kategoria: "wszystkie",
};

const ETYKIETY_STATUSU = {
    nowa: "Nowa",
    aplikowalem: "Aplikowałem",
    rozmowa: "Rozmowa",
    odrzucona: "Odrzucona",
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

function opcjeStatusu(aktualny) {
    return Object.entries(ETYKIETY_STATUSU)
        .map(([wartosc, etykieta]) =>
            `<option value="${wartosc}" ${wartosc === aktualny ? "selected" : ""}>${etykieta}</option>`
        )
        .join("");
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
        <div class="panel-statusu">
            <select class="status-select" data-id="${oferta.id}">
                ${opcjeStatusu(oferta.status || "nowa")}
            </select>
            <textarea class="notatka-input" data-id="${oferta.id}" placeholder="Notatka...">${escapeHtml(oferta.notatka || "")}</textarea>
        </div>
        <div class="stopka">
            <span class="data">${formatData(oferta.data_znalezienia)}</span>
            <div class="stopka-akcje">
                <button class="generuj-cv-btn" data-id="${oferta.id}">Generuj CV</button>
                <a href="${bezpiecznyLink(oferta.link)}" target="_blank" rel="noopener noreferrer">Zobacz ofertę →</a>
            </div>
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
    listaEl.querySelectorAll(".status-select").forEach(el => {
        el.addEventListener("change", onZmianaStatusu);
    });
    listaEl.querySelectorAll(".notatka-input").forEach(el => {
        el.addEventListener("blur", onZapiszNotatke);
    });
    listaEl.querySelectorAll(".generuj-cv-btn").forEach(el => {
        el.addEventListener("click", onGenerujCv);
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

async function onZmianaStatusu(e) {
    const select = e.currentTarget;
    const id = select.dataset.id;
    try {
        await fetch(`/api/status/${id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: select.value }),
        });
    } catch (err) {
        // status zostaje jak wybrany lokalnie - przy następnym odświeżeniu i tak
        // wróci do wartości z bazy, jeśli zapis się nie udał
    }
}

async function onZapiszNotatke(e) {
    const textarea = e.currentTarget;
    const id = textarea.dataset.id;
    try {
        await fetch(`/api/notatka/${id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ notatka: textarea.value }),
        });
    } catch (err) {}
}

async function onGenerujCv(e) {
    const btn = e.currentTarget;
    const id = btn.dataset.id;
    const oryginalnyTekst = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Generuję...";

    try {
        const resp = await fetch(`/api/generate-cv/${id}`, { method: "POST" });
        if (!resp.ok) {
            const dane = await resp.json().catch(() => ({}));
            throw new Error(dane.error || `HTTP ${resp.status}`);
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "CV.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert("Generowanie CV nie powiodło się: " + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = oryginalnyTekst;
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
