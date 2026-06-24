import requests

url = "http://127.0.0.1:8000/chat"
payload = {
    "session_id": "test_user_1",
    "message": "What is the main topic discussed in my uploaded file?"
}

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Answer:", response.json().get("response"))