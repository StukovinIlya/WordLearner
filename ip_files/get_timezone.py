import requests


def get_timezone(ip):
    try:
        response = requests.get(f'https://ipapi.co/{ip}/json/')
        if response.status_code == 200:
            data = response.json()
            return data.get('timezone')
        print(f"Ошибка {response.status_code}")
        return None
    except Exception as e:
        print(f"Ошибка при запросе к API: {e}")
        return None
