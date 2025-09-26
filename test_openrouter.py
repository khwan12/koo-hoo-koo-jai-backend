import os, requests

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    print("❌ ไม่พบ OPENROUTER_API_KEY ใน Secrets กรุณาตั้งค่าให้ถูกต้อง")
    exit()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "สวัสดี ทดสอบ"}]
}

print("⏳ กำลังทดสอบเรียก API ...")
response = requests.post(API_URL, headers=headers, json=data)
print(f"HTTP Status: {response.status_code}")

try:
    resp_json = response.json()
    print("Response JSON:", resp_json)
except Exception as e:
    print("⚠️ ไม่สามารถอ่าน JSON:", e)
    print("Raw Response:", response.text)
