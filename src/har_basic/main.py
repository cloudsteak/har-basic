import requests


def check_url(url: str) -> None:
    try:
        response = requests.get(url, timeout=10)
        # A raise_for_status() hibát dob, ha a kód 4xx vagy 5xx
        response.raise_for_status()
        print(f"Sikeres hívás! HTTP státuszkód: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Hiba történt a hívás során: {e}")


def main() -> None:
    check_url("https://httpbin.org/get")


if __name__ == "__main__":
    main()
