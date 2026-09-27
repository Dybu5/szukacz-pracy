"""Uruchamiane przez Harmonogram zadań Windows raz dziennie - wykonuje to samo
wyszukiwanie co przycisk "Szukaj" w aplikacji, po czym pokazuje powiadomienie
systemowe z wynikiem (bez potrzeby otwierania przeglądarki)."""
import sys

from plyer import notification

from search import wykonaj_wyszukiwanie


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    try:
        wyniki = wykonaj_wyszukiwanie()
    except Exception as e:
        print(f"BŁĄD: {e}")
        notification.notify(
            title="Szukacz Pracy - błąd wyszukiwania",
            message=str(e)[:250],
            app_name="Szukacz Pracy",
            timeout=15,
        )
        return

    if wyniki:
        tytuly = "\n".join(f"• {o['title']}" for o in wyniki[:5])
        if len(wyniki) > 5:
            tytuly += f"\n... i {len(wyniki) - 5} więcej"
        wiadomosc = tytuly
    else:
        wiadomosc = "Dziś nic nie znaleziono."

    print(f"Znaleziono {len(wyniki)} pasujących ofert.")
    notification.notify(
        title=f"Szukacz Pracy - {len(wyniki)} nowych ofert",
        message=wiadomosc,
        app_name="Szukacz Pracy",
        timeout=20,
    )


if __name__ == "__main__":
    main()
