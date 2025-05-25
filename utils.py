import requests
from datetime import datetime, timezone, timedelta
import json
import threading
from collections import OrderedDict

TOKEN = "7889701836:AAECLBRjjDadhpgJreOctpo5Jc72ekDKNjc"
URL = f"https://api.telegram.org/bot{TOKEN}/"
IRST_OFFSET = timedelta(hours=3, minutes=30)

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            elif len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = value
            self.cache.move_to_end(key)

PROFILE_PHOTO_CACHE = LRUCache(100)  # کش با ظرفیت 100 عکس

def escape_markdown(text):
    """فرار کردن کاراکترهای ویژه در متن برای MarkdownV2"""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def get_irst_time(timestamp):
    """تبدیل timestamp به زمان محلی ایران (IRST)"""
    utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    irst_time = utc_time + IRST_OFFSET
    return irst_time.strftime("%H:%M")

def get_user_profile_photo(user_id):
    """دریافت عکس پروفایل کاربر از تلگرام و ذخیره در کش"""
    cached_photo = PROFILE_PHOTO_CACHE.get(user_id)
    if cached_photo is not None:
        return cached_photo
    
    url = URL + "getUserProfilePhotos"
    params = {"user_id": user_id, "limit": 1}
    try:
        resp = session.get(url, params=params).json()
        if resp.get("ok") and resp["result"]["total_count"] > 0:
            photo = resp["result"]["photos"][0][0]["file_id"]
            PROFILE_PHOTO_CACHE.set(user_id, photo)
            return photo
    except requests.RequestException as e:
        logger.error(f"Error fetching profile photo for user {user_id}: {e}")
    PROFILE_PHOTO_CACHE.set(user_id, None)
    return None

def answer_inline_query(inline_query_id, results):
    """پاسخ به inline query"""
    url = URL + "answerInlineQuery"
    data = {
        "inline_query_id": inline_query_id,
        "results": json.dumps(results),
        "cache_time": 0,
        "is_personal": True
    }
    try:
        session.post(url, data=data)
    except requests.RequestException as e:
        logger.error(f"Error answering inline query {inline_query_id}: {e}")

def answer_callback_query(callback_query_id, text, show_alert=False):
    """پاسخ به callback query"""
    url = URL + "answerCallbackQuery"
    data = {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert
    }
    try:
        session.post(url, data=data)
    except requests.RequestException as e:
        logger.error(f"Error answering callback query {callback_query_id}: {e}")

def edit_message_text(chat_id=None, message_id=None, inline_message_id=None, text=None, reply_markup=None):
    """ویرایش متن پیام"""
    url = URL + "editMessageText"
    data = {
        "text": text,
        "parse_mode": "MarkdownV2",
        "reply_markup": json.dumps(reply_markup) if reply_markup else None
    }
    if chat_id and message_id:
        data["chat_id"] = chat_id
        data["message_id"] = message_id
    elif inline_message_id:
        data["inline_message_id"] = inline_message_id
    else:
        raise ValueError("Either (chat_id and message_id) or inline_message_id must be provided.")
    try:
        return session.post(url, data=data)
    except requests.RequestException as e:
        logger.error(f"Error editing message: {e}")
        return None

def format_block_code(whisper_data):
    """فرمت‌دهی محتوای بلاک کد برای پیام نجوا"""
    receiver_display_name = whisper_data['receiver_display_name']
    view_times = whisper_data.get("receiver_views", [])
    view_count = len(view_times)
    view_time_str = get_irst_time(view_times[-1]) if view_times else "هنوز دیده نشده"
    code_content = f"{escape_markdown(receiver_display_name)} {view_count} | {view_time_str}\n___________"
    code_content += "\n" + ("\n".join([escape_markdown(user) for user in whisper_data["curious_users"]]) if whisper_data["curious_users"] else "Nothing")
    return code_content

# ایجاد session برای requests
session = requests.Session()

# تنظیم لاگر (فرض بر این است که لاگر قبلاً تنظیم شده است)
import logging
logger = logging.getLogger(__name__)
