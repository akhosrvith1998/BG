from flask import Flask, jsonify
import logging
import requests
import time
from threading import Thread, Event

# ایجاد اپلیکیشن Flask
app = Flask(__name__)

# تنظیم سیستم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تابع پینگ کردن سرور
def ping(stop_event):
    """
    تابع برای ارسال درخواست پینگ به سرور به صورت دوره‌ای.
    
    Args:
        stop_event (threading.Event): برای کنترل توقف حلقه پینگ.
    """
    session = requests.Session()  # استفاده از Session برای بهبود عملکرد درخواست‌ها
    while not stop_event.is_set():
        try:
            response = session.get("https://xbegoo.onrender.com")
            logger.info(f"Ping successful: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Ping failed: {e}")
        time.sleep(600)  # هر 10 دقیقه

# تابع اجرای سرور Flask
def run_server():
    """
    تابع برای اجرای سرور Flask.
    """
    try:
        app.run(host='0.0.0.0', port=8080, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to run server: {e}")

# endpoint اصلی
@app.route('/')
def home():
    """بازگشت پیام ساده برای نشان دادن زنده بودن سرور."""
    logger.info("Home endpoint accessed")
    return "I’m alive"

# endpoint جدید برای بررسی وضعیت
@app.route('/status')
def status():
    """بازگشت وضعیت سرور به همراه زمان فعلی."""
    logger.info("Status endpoint accessed")
    return jsonify({"status": "running", "timestamp": time.time()})

# تابع اصلی برای نگه‌داری سرور و پینگ
def keep_alive():
    """
    تابع اصلی برای اجرای سرور و پینگ در threadهای جداگانه.
    """
    stop_event = Event()  # برای کنترل توقف پینگ
    
    # اجرای سرور در یک thread
    server_thread = Thread(target=run_server)
    server_thread.start()
    
    # اجرای پینگ در thread دیگر
    ping_thread = Thread(target=ping, args=(stop_event,))
    ping_thread.start()
    
    # منتظر ماندن برای توقف برنامه
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_event.set()  # توقف پینگ
        server_thread.join()  # انتظار برای اتمام thread سرور
        ping_thread.join()  # انتظار برای اتمام thread پینگ

# اجرای برنامه
if __name__ == "__main__":
    keep_alive()
