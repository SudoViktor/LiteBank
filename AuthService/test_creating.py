import requests

url = "http://localhost:5001/users/"

payload = {
    "username": "viktor_test",
    "password": "secure_password_123"
}

print(f"Відправляємо POST-запит на {url}...")

response = requests.post(url, json=payload)

print(f"Статус код: {response.status_code}")

if response.status_code == 200:
    print("✅ Користувача успішно створено!")
    print("Відповідь сервера:", response.json())
else:
    print("❌ Сталася помилка!")
    print("Деталі:", response.text)