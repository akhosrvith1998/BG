import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    تنظیم لاگر با قابلیت لاگینگ به فایل و کنسول، با پشتیبانی از محیط‌های چند نخی.
    
    Returns:
        logging.Logger: لاگر تنظیم‌شده.
    """
    logger = logging.getLogger('bot_logger')
    logger.setLevel(logging.INFO)
    
    # جلوگیری از اضافه شدن handlerهای تکراری
    if not logger.hasHandlers():
        # Handler برای فایل با RotatingFileHandler برای مدیریت حجم فایل
        log_file = 'bot.log'
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)  # 5MB per file, keep 3 backups
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        # Handler برای کنسول
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)
        
        # Handler برای خطاهای بحرانی به یک فایل جداگانه
        critical_handler = logging.FileHandler('critical.log')
        critical_handler.setLevel(logging.ERROR)
        critical_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(critical_handler)
    
    return logger

# ایجاد لاگر
logger = setup_logger()

# تابع برای لاگینگ در threadهای مختلف
def log_from_thread(message):
    """
    تابع برای لاگینگ از threadهای مختلف.
    
    Args:
        message (str): پیام لاگ.
    """
    logger.info(f"{message} from thread {threading.current_thread().name}")

# مثال استفاده
if __name__ == "__main__":
    logger.info("This is an info message")
    logger.error("This is an error message")
    
    # تست لاگینگ از thread
    thread = threading.Thread(target=log_from_thread, args=("Test message",))
    thread.start()
    thread.join()
