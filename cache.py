import time
from collections import defaultdict, OrderedDict
import threading

class LRUCache:
    """
    یک کلاس کش با الگوریتم LRU (Least Recently Used) و پشتیبانی از TTL (Time To Live).
    """
    def __init__(self, capacity: int, ttl: int):
        self.cache = OrderedDict()  # استفاده از OrderedDict برای حفظ ترتیب ورودی‌ها
        self.capacity = capacity    # حداکثر ظرفیت کش
        self.ttl = ttl              # زمان انقضا (ثانیه)
        self.lock = threading.Lock()  # قفل برای ایمنی در محیط چند نخی

    def get(self, key):
        """
        دریافت مقدار از کش بر اساس کلید.
        اگر کلید موجود باشد و منقضی نشده باشد، مقدار را برمی‌گرداند و آن را به انتهای لیست منتقل می‌کند.
        """
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry["timestamp"] < self.ttl:
                    self.cache.move_to_end(key)  # به‌روزرسانی ترتیب استفاده
                    return entry["results"]
                else:
                    del self.cache[key]  # حذف ورودی منقضی‌شده
            return None

    def set(self, key, results):
        """
        ذخیره مقدار در کش.
        اگر ظرفیت پر باشد، قدیمی‌ترین ورودی حذف می‌شود.
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]  # حذف ورودی قدیمی با همین کلید
            elif len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)  # حذف قدیمی‌ترین ورودی (LRU)
            self.cache[key] = {
                "results": results,
                "timestamp": time.time()
            }
            self.cache.move_to_end(key)  # انتقال به انتها (جدیدترین)

# تنظیمات کش
CACHE_CAPACITY_PER_USER = 100  # حداکثر 100 پرس‌وجو برای هر کاربر
CACHE_TTL = 10                 # زمان انقضا: 10 ثانیه

# ساختار کش برای هر کاربر
INLINE_QUERY_CACHE = defaultdict(lambda: LRUCache(CACHE_CAPACITY_PER_USER, CACHE_TTL))

def get_cached_inline_query(sender_id, query):
    """
    دریافت پرس‌وجوی کش‌شده برای یک کاربر خاص.
    """
    user_cache = INLINE_QUERY_CACHE[sender_id]
    key = query  # کلید می‌تواند بر اساس نیاز تغییر کند
    return user_cache.get(key)

def set_cached_inline_query(sender_id, query, results):
    """
    ذخیره پرس‌وجوی کش‌شده برای یک کاربر خاص.
    """
    user_cache = INLINE_QUERY_CACHE[sender_id]
    key = query
    user_cache.set(key, results)

# مثال استفاده
if __name__ == "__main__":
    sender_id = "user123"
    query = "test query"
    
    # ذخیره در کش
    set_cached_inline_query(sender_id, query, ["result1", "result2"])
    print(f"ذخیره شد: {query}")
    
    # دریافت از کش
    result = get_cached_inline_query(sender_id, query)
    print(f"دریافت از کش: {result}")
    
    # تست انقضا
    time.sleep(11)  # منتظر انقضا
    result = get_cached_inline_query(sender_id, query)
    print(f"بعد از انقضا: {result}")
