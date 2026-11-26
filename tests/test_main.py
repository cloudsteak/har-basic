import requests

from har_basic.main import check_url, check_urls


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


def test_check_urls_checks_each_url(mocker, capsys):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_get = mocker.patch("har_basic.main.requests.get", return_value=mock_response)

    check_urls(["https://pelda.hu/a", "https://pelda.hu/b"])

    assert mock_get.call_count == 2
    captured = capsys.readouterr()
    assert captured.out.count("Sikeres hívás! HTTP státuszkód: 200") == 2


def test_check_urls_continues_after_error(mocker, capsys):
    ok = mocker.Mock()
    ok.status_code = 200
    bad = mocker.Mock()
    bad.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mocker.patch("har_basic.main.requests.get", side_effect=[bad, ok])

    check_urls(["https://pelda.hu/rossz", "https://pelda.hu/jo"])

    captured = capsys.readouterr()
    assert "Hiba történt a hívás során" in captured.out
    assert "Sikeres hívás! HTTP státuszkód: 200" in captured.out
