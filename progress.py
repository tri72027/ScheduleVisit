from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils import random_sleep
from config import HOME_URL
from logger import setup_logger

logger = setup_logger()


def get_case_numbers(driver):
    random_sleep(2, 4)
    cases = []
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/home/cases/"]')
        for el in elements:
            case_text = el.text.strip()
            case_href = el.get_attribute("href")
            cases.append((case_text, case_href))
        return cases
    except Exception as e:
        logger.exception(f"Lỗi khi lấy case numbers: {e}")
        return []


def process_case_link(driver, case_url, max_days=10):
    driver.get(case_url)
    wait = WebDriverWait(driver, 10)
    try:
        section = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//h3[contains(text(), 'Make an appointment at the office')]/..")
            )
        )
        logger.info(f"✅ Tìm thấy mục 'Make an appointment at the office' tại {case_url}")
        button = section.find_element(By.XPATH, ".//following-sibling::button[contains(@class, 'btn--accordion')]")
        driver.execute_script("arguments[0].click();", button)
        random_sleep(2.2, 4.3)
        select_location_and_queue(driver, max_days, round_count=1)
    except TimeoutException:
        logger.warning("❌ Không có mục 'Make an appointment...' → quay lại home")
        driver.get(HOME_URL)


def select_location_and_queue(driver, max_days=10, round_count=1):
    """Chọn location + queue, sau đó xử lý calendar"""
    wait = WebDriverWait(driver, 10)

    _select_location(driver, wait, round_count=round_count)
    _select_queue(driver, wait, round_count=round_count)
    random_sleep(2.0, 4.0)

    try:
        calendar = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'mat-calendar.mat-calendar.reservation-calander')
            )
        )
        logger.info("🔄 Calendar đã xuất hiện")

        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "mat-calendar.mat-calendar.reservation-calander td.mat-calendar-body-cell .mat-calendar-body-cell-content")
            )
        )
        logger.info("✅ Calendar đã load ít nhất 1 ngày hiển thị")

        _wait_for_calendar_spinner(driver, wait)
        check_calendar_and_click(driver, max_days=max_days, round_count=round_count)

    except Exception as e:
        logger.exception(f"❌ Không load được calendar: {e}")
        return None


def _select_location(driver, wait, round_count=1):
    location_select = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'mat-select[name="location"]'))
    )
    location_select.click()

    if round_count == 1:
        option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//mat-option//span[contains(text(), 'ul. Marszałkowska 3/5, 00-624 Warszawa')]")
            )
        )
        option.click()
        logger.info("✅ Đã chọn location (Marszałkowska)")
    else:
        option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//mat-option//span[contains(text(), 'pl. Bankowy 3/5 00-950 Warszawa')]")
            )
        )
        option.click()
        logger.info("✅ Đã chọn location (Bankowy)")


def _select_queue(driver, wait, round_count=1):
    queue_select = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'mat-select[name="queueName"]'))
    )
    queue_select.click()

    if round_count == 1:
        option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//mat-option//span[contains(text(), 'X - applications for TEMPORARY STAY')]")
            )
        )
        option.click()
        logger.info("✅ Đã chọn queue (X - TEMPORARY STAY)")
    else:
        option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//mat-option//span[contains(text(), 'G - Applications for TEMPORARY STAY - marriages and family stays 3/5 Bankowy Square entrance G')]")
            )
        )
        option.click()
        logger.info("✅ Đã chọn queue (Bankowy G)")


def _wait_for_calendar_spinner(driver, wait):
    spinner_locator = (By.CSS_SELECTOR, ".reservation__calendar .spinner")
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(spinner_locator))
        logger.info("⏳ Spinner xuất hiện, chờ biến mất...")
        wait.until(EC.invisibility_of_element_located(spinner_locator))
        random_sleep(2.0, 4.0)
        logger.info("✅ Calendar đã load xong")
    except TimeoutException:
        logger.warning("⚠️ Không thấy spinner (có thể load quá nhanh)")


def check_calendar_and_click(driver, max_days=10, round_count=1):
    wait = WebDriverWait(driver, 8)
    day_clicked_count = 0

    while day_clicked_count < max_days:
        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "mat-calendar.mat-calendar.reservation-calander")
                )
            )
        except TimeoutException:
            logger.error("❌ Calendar biến mất bất thường")
            return

        try:
            month_label = driver.find_element(
                By.CSS_SELECTOR, "button.mat-calendar-period-button span"
            ).text.strip()
        except Exception:
            month_label = "UNKNOWN"

        days = driver.find_elements(
            By.CSS_SELECTOR,
            "mat-calendar.mat-calendar.reservation-calander td.mat-calendar-body-cell .mat-calendar-body-cell-content"
        )

        clickable_days = []
        for day in days:
            try:
                parent_td = day.find_element(By.XPATH, "..")
                cls = parent_td.get_attribute("class")
                if "mat-calendar-body-disabled" not in cls:
                    clickable_days.append(day)
            except Exception:
                continue

        if clickable_days:
            logger.info(f"✅ {month_label}: Tìm thấy {len(clickable_days)} ngày khả dụng")
            for d in clickable_days:
                if day_clicked_count >= max_days:
                    break
                try:
                    driver.execute_script("arguments[0].click();", d)
                    random_sleep(2.2, 4.3)
                    logger.info(f"👉 Đã click ngày {d.text}")
                    select_time_slot(driver)
                    day_clicked_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Không click được ngày {d.text}: {e}")
        else:
            logger.warning(f"⚠️ {month_label}: Không có ngày khả dụng")

        if day_clicked_count >= max_days:
            logger.info(f"⛔ Đã click đủ {max_days} ngày, dừng lại")
            if round_count == 1:
                select_location_and_queue(driver, max_days, round_count=2)
            else:
                logger.info("✅ Đã hoàn tất cả hai vòng. Kết thúc.")
            return

        try:
            next_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mat-calendar-next-button"))
            )
            driver.execute_script("arguments[0].click();", next_btn)
            random_sleep(2.0, 3.5)
        except:
            logger.error("❌ Không tìm thấy nút next month, dừng lại")
            break


def select_time_slot(driver):
    wait = WebDriverWait(driver, 10)

    logger.info("🔄 Đang load giờ...")
    try:
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".reservation__hours .spinner")))
    except:
        logger.warning("⚠️ Không thấy spinner giờ hoặc biến mất quá nhanh")

    try:
        hours = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".reservation__hours .tiles--hours .row button")
            )
        )
        logger.info(f"✅ Tìm thấy {len(hours)} giờ khả dụng")

        for h in hours:
            try:
                driver.execute_script("arguments[0].click();", h)
                logger.info(f"👉 Đã click giờ: {h.text.strip()}")
                random_sleep(1, 4.3)
                break
            except Exception as e:
                logger.warning(f"⚠️ Không click được giờ: {e}")
    except Exception as e:
        logger.error(f"❌ Không tìm thấy giờ: {e}")


def notify_done():
    """Thông báo khi tất cả user đã hoàn thành"""
    logger.info("\n🎉🎉🎉 TẤT CẢ USER ĐÃ HOÀN THÀNH QUY TRÌNH 🎉🎉🎉\n")
