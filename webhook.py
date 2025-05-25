from flask import Flask, request, Response, jsonify
import requests
import os
import threading
from queue import Queue
from main import process_update
from logger import logger

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN", "7672898225:AAHymEtVaPhC9SbKKSjCaRlkPx68S4ujLEc")
URL = f"https://api.telegram.org/bot{TOKEN}/"

# صف برای مدیریت به‌روزرسانی‌ها
update_queue = Queue()
MAX_WORKERS = 5  # تعداد threadهای پردازش‌کننده

def worker():
    """تابع worker برای پردازش به‌روزرسانی‌ها از صف"""
    while True:
        update = update_queue.get()
        if update is None:
            break
        try:
            process_update(update)
        except Exception as e:
            logger.error("Error processing update: %s", str(e))
        update_queue.task_done()

# راه‌اندازی workerها
for _ in range(MAX_WORKERS):
    t = threading.Thread(target=worker)
    t.start()

@app.route("/webhook", methods=["POST"])
def webhook():
    """مدیریت درخواست‌های وب‌هوک از تلگرام"""
    try:
        update = request.get_json()
        logger.info("Received update: %s", update)
        update_queue.put(update)
        return Response(status=200)
    except Exception as e:
        logger.error("Webhook error: %s", str(e))
        return Response(status=500)

@app.route("/status", methods=["GET"])
def status():
    """بررسی وضعیت سرور"""
    return jsonify({"status": "running", "queue_size": update_queue.qsize()})

if __name__ == "__main__":
    webhook_url = os.getenv("WEBHOOK_URL", "https://your-render-app.onrender.com/webhook")
    try:
        response = requests.get(f"{URL}setWebhook?url={webhook_url}")
        if response.json().get("ok"):
            logger.info("Webhook set successfully: %s", response.text)
        else:
            logger.error("Failed to set webhook: %s", response.text)
    except requests.RequestException as e:
        logger.error("Error setting webhook: %s", str(e))
    
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
