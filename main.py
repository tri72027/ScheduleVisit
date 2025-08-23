from utils import read_accounts, random_sleep
from browser import init_driver
from login import login
from progress import get_case_numbers, process_case_link, notify_done
from config import ACCOUNT_FILE
from logger import setup_logger

DEBUG_KEEP_BROWSER = True  # set True nếu muốn giữ browser để debug
logger = setup_logger()

def main(max_days=10):
    accounts = read_accounts(ACCOUNT_FILE)
    if not accounts:
        return

    driver = init_driver()
    total_users = len(accounts)

    for idx, (username, password) in enumerate(accounts, start=1):
        logger.info(f"🚀 BẮT ĐẦU XỬ LÝ USER {idx}/{total_users}: {username}")
        try:
            login_success = login(username, password, driver)
            if not login_success:
                logger.error(f"❌ Login thất bại cho USER {idx}: {username}")
                continue

            logger.info(f"🎉 USER {idx}: {username} login thành công!")
            cases = get_case_numbers(driver)

            if not cases:
                logger.warning(f"⚠️ USER {idx}: {username} không tìm thấy case nào")
                continue

            for case_text, case_href in cases:
                logger.info(f"➡️ USER {idx}: Case {case_text} - {case_href}")
                process_case_link(driver, case_href, max_days=max_days)
                random_sleep(1.5, 3.5)

        except Exception as e:
            logger.exception(f"💥 Lỗi khi xử lý USER {idx}: {username} → {e}")
        finally:
            logger.info(f"✅ KẾT THÚC USER {idx}/{total_users}: {username}")

    if not DEBUG_KEEP_BROWSER:
        driver.quit()
        logger.info("✅ Đã đóng browser")
    else:
        logger.info("🔒 Browser vẫn mở để debug")

    notify_done()


if __name__ == "__main__":
    main()
    notify_done()
