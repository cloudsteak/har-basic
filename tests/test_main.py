import requests
from har_basic.main import check_url


def test_check_url_success(mocker, capsys):
    # 1. Előkészítés (Arrange): Létrehozunk egy hamis választ 200-as kóddal
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    # Beállítjuk, hogy a requests.get ezt a hamis választ adja vissza
    mocker.patch("har_basic.main.requests.get", return_value=mock_response)

    # 2. Futtatás (Act)
    check_url("https://pelda.hu")

    # 3. Ellenőrzés (Assert): Megnézzük, mit írt ki a print()
    captured = capsys.readouterr()
    assert "Sikeres hívás! HTTP státuszkód: 200" in captured.out


def test_check_url_http_error(mocker, capsys):
    # Előkészítés: Szimulálunk egy 404-es hibát (a raise_for_status hibát dob)
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "404 Not Found"
    )
    mocker.patch("har_basic.main.requests.get", return_value=mock_response)

    # Futtatás
    check_url("https://pelda.hu/nem-letezik")

    # Ellenőrzés
    captured = capsys.readouterr()
    assert "Hiba történt a hívás során" in captured.out
