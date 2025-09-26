# main.py
from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI

app = Flask(__name__, template_folder='templates', static_folder='static')

# โหลด OpenRouter API Key จาก Secrets
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")  # ใช้สำหรับเปิดเพลง/ดูหนัง

if not OPENROUTER_API_KEY:
    raise ValueError("❌ กรุณาตั้งค่า OPENROUTER_API_KEY ใน Secrets ของ Replit")

# สร้าง OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# ========== YouTube Helper ==========
def search_youtube(query):
    if not YOUTUBE_API_KEY:
        return None
    try:
        from googleapiclient.discovery import build
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            video = response['items'][0]
            return {
                'videoId': video['id']['videoId'],
                'title': video['snippet']['title']
            }
    except Exception as e:
        print("YouTube API Error:", e)
    return None

# ========== Routes ==========
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        prompt = data.get("prompt", "").strip()
        history = data.get("history", [])
        user_profile = data.get("profile", {})

        if not prompt:
            return jsonify({
                "response_type": "text",
                "data": "❌ ไม่มีข้อความ prompt"
            }), 400

        prompt_lower = prompt.lower()

        # --- ตรวจจับ: เปิดเพลง ---
        if prompt_lower.startswith("เปิดเพลง"):
            query = prompt.replace("เปิดเพลง", "", 1).strip() or "เพลงผ่อนคลาย"
            video = search_youtube(query)
            if video:
                return jsonify({
                    "response_type": "music",
                    "data": {
                        "text": f"กำลังเปิดเพลง: **{video['title']}** 🎶",
                        "videoId": video['videoId']
                    }
                })
            else:
                return jsonify({
                    "response_type": "text",
                    "data": "ขอโทษค่ะ ไม่พบวิดีโอที่ตรงกับคำค้นหานะคะ 😢"
                })

        # --- ตรวจจับ: ดูหนัง ---
        if prompt_lower.startswith("ดูหนัง"):
            query = prompt.replace("ดูหนัง", "", 1).strip() or "หนังแนะนำ"
            video = search_youtube(query)
            if video:
                return jsonify({
                    "response_type": "movie",
                    "data": {
                        "text": f"กำลังเปิดหนัง: **{video['title']}** 🎬",
                        "videoId": video['videoId'],
                        "title": video['title']
                    }
                })
            else:
                return jsonify({
                    "response_type": "text",
                    "data": "ขอโทษค่ะ ไม่พบหนังที่ตรงกับคำค้นหานะคะ 🎥"
                })

        # --- ถ้าไม่ใช่คำสั่งพิเศษ → ส่งไปหา AI ---
        ai_persona = user_profile.get('aiPersona', 'เป็นเพื่อนที่น่ารักและเป็นมิตร')
        system_message = f"""
คุณคือ 'คู่ใจ' ผู้ช่วย AI ที่มีบุคลิก: "{ai_persona}"
กติกา:
1. ตอบเป็นภาษาไทยเสมอ ใช้คำพูดน่ารัก อ่อนโยน และเข้าใจง่าย ใส่อีโมจิให้เหมาะสม
2. ถ้าคำถามเกี่ยวกับ "สุขภาพจิต" ให้ตอบโดยอ้างอิงจาก กรมสุขภาพจิต เท่านั้น และลงท้ายด้วย:
   <div class='reference'>อ้างอิง: กรมสุขภาพจิต (คำแนะนำเบื้องต้น)</div>
3. ถ้าคำถามเกี่ยวกับ "สุขภาพร่างกาย" ให้ตอบโดยอ้างอิงจาก คณะแพทยศาสตร์ศิริราชพยาบาล หรือ จุฬาลงกรณ์มหาวิทยาลัย และลงท้ายด้วย:
   <div class='reference'>อ้างอิง: คณะแพทยศาสตร์ศิริราชพยาบาล, จุฬาฯ (คำแนะนำเบื้องต้น)</div>
4. สำหรับคำถามอื่นๆ ให้ตอบอย่างถูกต้อง พร้อมอ้างอิงแหล่งที่เชื่อถือได้
5. ห้ามให้คำแนะนำที่เป็นอันตราย หรือขัดต่อกฎหมายไทย
"""

        messages = [{"role": "system", "content": system_message}]
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg.get("parts", [{}])[0].get("text", "")
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="google/gemini-flash-1.5-8b",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        ai_text = completion.choices[0].message.content
        return jsonify({
            "response_type": "text",
            "data": ai_text
        })

    except Exception as e:
        return jsonify({
            "response_type": "text",
            "data": f"⛔️ เกิดข้อผิดพลาด: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 81)))