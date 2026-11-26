import requests


def check_url(url: str) -> None:
    try:
        response = requests.get(url, timeout=10)
        # A raise_for_status() hibát dob, ha a kód 4xx vagy 5xx
        response.raise_for_status()
        print(f"Sikeres hívás! HTTP státuszkód: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Hiba történt a hívás során: {e}")


def check_urls(urls: list[str]) -> None:
    for url in urls:
        check_url(url)


def main() -> None:
    check_urls(["https://httpbin.org/get", "https://httpbin.org/ip", "https://httpbin.org/user-agent"])


if __name__ == "__main__":
    main()
