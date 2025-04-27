import requests

def send_push_notification(token, title, message):
    url = 'https://exp.host/--/api/v2/push/send'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    payload = {
        'to': token,
        'title': title,
        'body': message,
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
