import unicodedata
from urllib.parse import quote


def content_disposition_pdf(nazwa_pliku):
    """Buduje wartość nagłówka Content-Disposition dla pliku PDF do pobrania.
    HTTP wymaga ASCII w wartościach nagłówków - polskie znaki wywalają wysyłkę
    odpowiedzi, jeśli trafią tam surowo, więc dajemy transliterowany ASCII fallback
    (filename=) i poprawny UTF-8 (filename*=) dla przeglądarek, które go wspierają."""
    ascii_nazwa = unicodedata.normalize("NFKD", nazwa_pliku).encode("ascii", "ignore").decode("ascii")
    utf8_nazwa = quote(nazwa_pliku)
    return f'attachment; filename="{ascii_nazwa}"; filename*=UTF-8\'\'{utf8_nazwa}'
