import sqlite3
import json
import threading
from collections import deque

DATABASE = "history.db"
HISTORY_LIMIT_PER_USER = 10  # محدودیت تعداد گیرنده‌ها برای هر کاربر

class HistoryManager:
    def __init__(self):
        self.history = {}
        self.lock = threading.Lock()  # برای ایمنی در محیط چند نخی
        self._init_database()
        self._load_history()

    def _init_database(self):
        """ایجاد جدول‌های مورد نیاز در دیتابیس"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                sender_id TEXT,
                receiver_id TEXT,
                display_name TEXT,
                first_name TEXT,
                profile_photo_url TEXT,
                PRIMARY KEY (sender_id, receiver_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT,
                receiver_id TEXT,
                message_text TEXT,
                timestamp REAL
            )
        """)
        conn.commit()
        conn.close()

    def _load_history(self):
        """بارگذاری تاریخچه از دیتابیس به حافظه"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT sender_id, receiver_id, display_name, first_name, profile_photo_url FROM history")
        rows = cursor.fetchall()
        for row in rows:
            sender_id, receiver_id, display_name, first_name, profile_photo_url = row
            if sender_id not in self.history:
                self.history[sender_id] = deque(maxlen=HISTORY_LIMIT_PER_USER)
            self.history[sender_id].append({
                "receiver_id": receiver_id,
                "display_name": display_name,
                "first_name": first_name,
                "profile_photo_url": profile_photo_url,
                "curious_users": set()  # برای سازگاری با کد قبلی
            })
        conn.close()

    def save_receiver(self, sender_id, receiver):
        """ذخیره گیرنده در تاریخچه"""
        with self.lock:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO history (sender_id, receiver_id, display_name, first_name, profile_photo_url)
                VALUES (?, ?, ?, ?, ?)
            """, (sender_id, receiver["receiver_id"], receiver["display_name"], receiver["first_name"], receiver["profile_photo_url"]))
            conn.commit()
            conn.close()
            # به‌روزرسانی حافظه
            if sender_id not in self.history:
                self.history[sender_id] = deque(maxlen=HISTORY_LIMIT_PER_USER)
            existing = next((r for r in self.history[sender_id] if r["receiver_id"] == receiver["receiver_id"]), None)
            if existing:
                self.history[sender_id].remove(existing)
            self.history[sender_id].append(receiver)

    def save_message(self, sender_id, receiver_id, message_text, timestamp):
        """ذخیره پیام در دیتابیس"""
        with self.lock:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, message_text, timestamp)
                VALUES (?, ?, ?, ?)
            """, (sender_id, receiver_id, message_text, timestamp))
            conn.commit()
            conn.close()

    def get_history(self, sender_id):
        """دریافت تاریخچه گیرنده‌ها برای یک کاربر"""
        with self.lock:
            return list(self.history.get(sender_id, []))

    def search_history(self, sender_id, query):
        """جستجو در تاریخچه گیرنده‌ها بر اساس نام یا نام کاربری"""
        with self.lock:
            if sender_id in self.history:
                return [r for r in self.history[sender_id] if query.lower() in r["display_name"].lower() or query.lower() in r["first_name"].lower()]
            return []

    def get_messages(self, sender_id, receiver_id, limit=50):
        """دریافت آخرین پیام‌ها بین sender و receiver"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_text, timestamp FROM messages
            WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
            ORDER BY timestamp DESC LIMIT ?
        """, (sender_id, receiver_id, receiver_id, sender_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"message_text": row[0], "timestamp": row[1]} for row in rows]

# ایجاد یک instance از HistoryManager
history_manager = HistoryManager()

# مثال استفاده
if __name__ == "__main__":
    sender_id = "user123"
    receiver = {
        "receiver_id": "user456",
        "display_name": "John Doe",
        "first_name": "John",
        "profile_photo_url": "http://example.com/photo.jpg"
    }
    
    # ذخیره گیرنده
    history_manager.save_receiver(sender_id, receiver)
    print(f"گیرنده ذخیره شد: {receiver['display_name']}")
    
    # ذخیره پیام
    import time
    timestamp = time.time()
    history_manager.save_message(sender_id, receiver["receiver_id"], "Hello!", timestamp)
    print("پیام ذخیره شد")
    
    # دریافت تاریخچه
    history = history_manager.get_history(sender_id)
    print(f"تاریخچه: {history}")
    
    # جستجو در تاریخچه
    search_results = history_manager.search_history(sender_id, "john")
    print(f"نتایج جستجو: {search_results}")
    
    # دریافت پیام‌ها
    messages = history_manager.get_messages(sender_id, receiver["receiver_id"])
    print(f"پیام‌ها: {messages}")
