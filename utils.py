import time, random
from logger import setup_logger

logger = setup_logger()

def random_sleep(min_sec=0.3, max_sec=1.2):
    time.sleep(random.uniform(min_sec, max_sec))

def read_accounts(file_path):
    accounts = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if "|" in line:
                    username, password = line.split("|", 1)
                    accounts.append((username, password))
        logger.info(f"✅ Đã đọc {len(accounts)} tài khoản từ file {file_path}")
    except Exception as e:
        logger.exception(f"❌ Lỗi đọc account: {e}")
    return accounts
