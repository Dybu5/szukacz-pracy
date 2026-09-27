from unittest.mock import MagicMock, patch

import cv_generator


def _mock_response(podsumowanie="Podsumowanie", umiejetnosci=None, osiagniecia=None):
    parsed = MagicMock()
    parsed.podsumowanie = podsumowanie
    parsed.umiejetnosci_uporzadkowane = umiejetnosci or ["Python"]
    parsed.wybrane_osiagniecia = osiagniecia or ["Osiągnięcie 1"]
    response = MagicMock()
    response.parsed_output = parsed
    return response


@patch("cv_generator.anthropic.Anthropic")
def test_brak_klucza_opis_oferty_nie_wywala_promptu(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _mock_response()
    mock_anthropic_cls.return_value = mock_client

    oferta_bez_opisu = {"title": "Staż", "company": "Firma", "powod": "pasuje"}
    cv_generator._dopasuj_tresc(oferta_bez_opisu, "{}")

    prompt = mock_client.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert "(brak pełnego opisu)" in prompt


@patch("cv_generator.anthropic.Anthropic")
def test_puste_opis_oferty_daje_fallback(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _mock_response()
    mock_anthropic_cls.return_value = mock_client

    oferta = {"title": "Staż", "company": "Firma", "powod": "pasuje", "opis_oferty": ""}
    cv_generator._dopasuj_tresc(oferta, "{}")

    prompt = mock_client.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert "(brak pełnego opisu)" in prompt


@patch("cv_generator.anthropic.Anthropic")
def test_none_opis_oferty_daje_fallback(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _mock_response()
    mock_anthropic_cls.return_value = mock_client

    oferta = {"title": "Staż", "company": "Firma", "powod": "pasuje", "opis_oferty": None}
    cv_generator._dopasuj_tresc(oferta, "{}")

    prompt = mock_client.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert "(brak pełnego opisu)" in prompt


@patch("cv_generator.anthropic.Anthropic")
def test_prawdziwy_opis_oferty_trafia_do_promptu(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _mock_response()
    mock_anthropic_cls.return_value = mock_client

    oferta = {"title": "Staż", "company": "Firma", "powod": "pasuje", "opis_oferty": "Szukamy Pythona"}
    cv_generator._dopasuj_tresc(oferta, "{}")

    prompt = mock_client.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert "Szukamy Pythona" in prompt
    assert "(brak pełnego opisu)" not in prompt
