import requests
import json

url = "http://127.0.0.1:5000/ask"

payload = {
    "question": "HC4407 的最大漏极电流是多少"
}

response = requests.post(url, json=payload)

print("Status:", response.status_code)
print("Response:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
