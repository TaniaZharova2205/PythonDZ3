import requests


def get_requests_session() -> requests.Session:
    return requests.Session()


def delete_link(api_url: str, short_code: str, session: requests.Session) -> dict:
    url = f"{api_url}/api/links/{short_code}"
    response = session.delete(url)
    try:
        # Если тело ответа пустое, возвращаем пустой dict
        return response.json() if response.text else {}
    except Exception:
        return {"detail": "Ошибка удаления ссылки"}


def register(api_url: str, username: str, password: str, email: str = None) -> dict:
    url = f"{api_url}/api/auth/register"
    payload = {"username": username, "password": password, "email": email}
    response = requests.post(url, json=payload)
    try:
        return response.json()
    except Exception:
        return {"detail": "Ошибка регистрации"}


def login(api_url: str, username: str, password: str, session: requests.Session) -> dict:
    url = f"{api_url}/api/auth/login"
    payload = {"username": username, "password": password}
    response = session.post(url, json=payload)
    try:
        return response.json()
    except Exception:
        return {"detail": "Ошибка входа"}


def logout(api_url: str, session: requests.Session) -> None:
    url = f"{api_url}/api/auth/logout"
    session.post(url)


def get_links(api_url: str, session: requests.Session) -> list:
    url = f"{api_url}/api/links"
    response = session.get(url)
    try:
        return response.json()
    except Exception:
        return []


def create_link(api_url: str, payload: dict, session: requests.Session) -> dict:
    url = f"{api_url}/api/links"
    response = session.post(url, json=payload)
    try:
        return response.json()
    except Exception:
        return {"detail": "Ошибка создания ссылки"}


def delete_user(api_url: str, session: requests.Session) -> dict:
    url = f"{api_url}/api/auth/user"
    response = session.delete(url)
    try:
        return response.json()
    except Exception:
        return {"detail": "Ошибка удаления аккаунта"}
