from utils import read_accounts, random_sleep
from browser import init_driver
from login import login
from progress import get_case_numbers, process_case_link, notify_done
from config import ACCOUNT_FILE, DEBUG_KEEP_BROWSER
from logger import setup_logger

logger = setup_logger()

#max_retry_case = 5  # số lần refresh nếu chưa thấy case "Temporary residence permit"


def main(max_days=10, max_retry_case=5):
    accounts = read_accounts(ACCOUNT_FILE)
    if not accounts:
        logger.error("❌ Không đọc được tài khoản nào")
        return

    driver = init_driver()
    total_users = len(accounts)

    for idx, (username, password) in enumerate(accounts, start=1):
        logger.info(f"🚀 BẮT ĐẦU XỬ LÝ USER {idx}/{total_users}: {username}")
        try:
            if not login(username, password, driver):
                logger.error(f"❌ Login thất bại cho USER {idx}: {username}")
                continue

            # Thử tìm case đúng loại nhiều lần
            attempts, cases = 0, []
            while attempts < max_retry_case:
                cases = get_case_numbers(driver)
                if cases:
                    break
                attempts += 1
                logger.warning(
                    f"⚠️ USER {idx}: chưa tìm thấy case 'Temporary residence permit' → thử lại {attempts}/{max_retry_case}"
                )
                driver.refresh()
                random_sleep(5, 9)

            if not cases:
                logger.warning(f"⛔ USER {idx}: {username} không có case Temporary residence permit, bỏ qua")
                continue

            for case_type, case_href in cases:
                logger.info(f"➡️ USER {idx}: Case {case_type} - {case_href}")
                try:
                    process_case_link(driver, case_href, max_days=max_days)
                except Exception as e:
                    logger.error(f"💥 Driver crash khi xử lý {username}: {e}")
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = init_driver()  # tạo lại browser
                    if login(driver, username, password):
                        process_case_link(driver, case_href, max_days=max_days)
                random_sleep(1.2, 2.5)

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
