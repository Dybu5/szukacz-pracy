from utils import content_disposition_pdf


def test_polskie_znaki_nie_trafiaja_surowo_do_naglowka():
    naglowek = content_disposition_pdf("CV_Staż_w_Dziale_Automatyzacji.pdf")
    # Wartość nagłówka HTTP musi dać się zakodować w latin-1 (surowy protokół HTTP/1.1) -
    # to dokładnie ten błąd (UnicodeEncodeError), który wywalał odpowiedź serwera.
    naglowek.encode("latin-1")


def test_ascii_fallback_transliteruje_znaki():
    naglowek = content_disposition_pdf("CV_Staż.pdf")
    assert 'filename="CV_Staz.pdf"' in naglowek


def test_utf8_wersja_zachowuje_oryginalne_znaki():
    naglowek = content_disposition_pdf("CV_Staż.pdf")
    assert "filename*=UTF-8''CV_Sta%C5%BC.pdf" in naglowek
