from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils import random_sleep
from config import HOME_URL
from logger import setup_logger

logger = setup_logger()

CALENDAR_ROOT = "mat-calendar.mat-calendar.reservation-calander"
DAY_CELL_SELECTOR = (
    f"{CALENDAR_ROOT} td.mat-calendar-body-cell:not(.mat-calendar-body-disabled) "
    ".mat-calendar-body-cell-content"
)

# ===========================
# 1) LẤY DANH SÁCH CASE HỢP LỆ
# ===========================
def get_case_numbers(driver):
    """
    Lấy các case có Case type = 'Temporary residence permit'.
    - Chỉ quét trong khối left 'direct-active-proceedings' để tránh khu khác.
    - Mỗi case là 1 'card card--border' chứa cả 'Case type' và 'Case number'.
    - Dedupe theo href.
    """
    cases = []
    href_seen = set()

    try:
        # Đảm bảo khu 'My active cases' đã render
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//direct-active-proceedings"))
        )
    except TimeoutException:
        logger.warning("⚠️ Không thấy khu 'direct-active-proceedings' sau 15s")
        return []

    random_sleep(0.8, 1.6)

    # Lấy đúng card gốc (mỗi case 1 card)
    case_cards = driver.find_elements(
        By.XPATH,
        "//direct-active-proceedings"
        "//div[contains(@class,'card') and contains(@class,'card--border')]"
        "[.//h3[normalize-space()='Case type'] and .//h3[normalize-space()='Case number']]"
    )

    logger.info(f"🔎 Tìm thấy {len(case_cards)} Case")

    for idx, card in enumerate(case_cards, start=1):
        try:
            # Case type text
            type_el = card.find_element(
                By.XPATH, ".//h3[normalize-space()='Case type']/../following-sibling::div/p"
            )
            case_type = type_el.text.strip()

            # Chỉ lấy Temporary residence permit
            if case_type != "Temporary residence permit":
                continue

            # Case number → href
            link_el = card.find_element(
                By.XPATH, ".//h3[normalize-space()='Case number']/../following-sibling::div/p/a"
            )
            href = link_el.get_attribute("href")

            if not href:
                logger.warning(f"⚠️ [{idx}] Không tìm thấy href cho case Temporary residence permit")
                continue

            if href in href_seen:
                logger.info(f"↺ [{idx}] Bỏ qua href trùng: {href}")
                continue

            href_seen.add(href)
            cases.append((case_type, href))

        except Exception as e:
            logger.warning(f"⚠️ [{idx}] Lỗi parse 1 case: {e}")

    return cases

# ========================================
# 2) XỬ LÝ 1 CASE: MỞ LỊCH HẸN & DUYỆT SLOT
# ========================================
def process_case_link(driver, case_url, max_days=10, round_count=1):
    driver.get(case_url)
    wait = WebDriverWait(driver, 25)
    random_sleep(0.5, 1.2)
    # Mở accordion đặt lịch
    _open_make_appointment_section(driver, wait, case_url)
    random_sleep(0.5, 1.2)

    # Chọn location + queue theo round_count
    _select_location(driver, wait, round_count=round_count)
    random_sleep(0.5, 1.2)
    _select_queue(driver, wait, round_count=round_count)
    random_sleep(0.5, 1.2)

    # DDợi calendar
    _wait_for_calendar_ready(driver, wait)
    random_sleep(0.5, 1.2)

    # Duyệt calendar
    done = _browse_calendar(driver, wait, max_months=6, max_days=max_days, round_count=round_count)

    # Nếu đã chọn được giờ (DONE) → kết thúc luôn, không qua vòng 2
    if done == "DONE":
        return

    # Nếu chỉ duyệt xong max_days ở vòng 1 mà chưa có giờ → chuyển qua vòng 2
    if round_count == 1 and done:
        logger.info("➡️ Chuyển sang Location + Queue vòng 2")
        process_case_link(driver, case_url, max_days=max_days, round_count=2)


    

# -----------------------
# 2.1 Mở accordion đặt lịch
# -----------------------
def _open_make_appointment_section(driver, wait, case_url):
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
    except TimeoutException:
        logger.warning("❌ Không có mục 'Make an appointment...' → quay lại home")
        driver.get(HOME_URL)

# -----------------------
# 2.2 Chọn Location
# -----------------------
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

# -----------------------
# 2.2 Chọn Queue
# -----------------------
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

# -----------------------
# 2.3 Chờ Calendar sẵn sàng
# -----------------------
def _wait_for_calendar_ready(driver, wait, expect_change=False, prev_label=None):
    """
    Đợi calendar 'ổn định':
      - (nếu expect_change) chờ nhãn tháng thay đổi sau khi bấm Next.
      - Đợi spinner xuất hiện (tối đa 8s) rồi ẩn (tối đa 30s).
      - Đợi có >= 1 ô ngày hiển thị.
      - Đợi danh sách ngày ổn định (2 lần đọc giống nhau).
    """
    # Nhãn tháng đổi?
    if expect_change and prev_label:
        try:
            wait.until(
                lambda d: d.find_element(By.CSS_SELECTOR, "button.mat-calendar-period-button span").text.strip()
                != prev_label
            )
        except Exception:
            logger.warning("⚠️ Đợi đổi tháng quá lâu, tiếp tục kiểm tra spinner")

    # Calendar container
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CALENDAR_ROOT)))
    logger.info("🔄 Calendar container đã xuất hiện")

    # Spinner xuất hiện rồi ẩn
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".reservation__calendar .spinner"))
        )
        logger.info("⏳ Spinner xuất hiện, chờ ẩn...")
        WebDriverWait(driver, 30).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".reservation__calendar .spinner"))
        )
    except TimeoutException:
        logger.warning("⚠️ Không thấy spinner (có thể load quá nhanh)")

    # Có ít nhất 1 ngày
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, DAY_CELL_SELECTOR)))

    # Danh sách ngày ổn định
    for _ in range(6):
        days1 = [d.text for d in driver.find_elements(By.CSS_SELECTOR, DAY_CELL_SELECTOR)]
        random_sleep(0.35, 0.6)
        days2 = [d.text for d in driver.find_elements(By.CSS_SELECTOR, DAY_CELL_SELECTOR)]
        if days1 and days1 == days2:
            logger.info("✅ Calendar đã sẵn sàng (ngày ổn định)")
            return
    logger.warning("⚠️ Calendar có vẻ chưa hoàn toàn ổn định, tiếp tục xử lý")


# -----------------------
# 2.4 Duyệt Calendar
# -----------------------
def _browse_calendar(driver, wait, max_months=6, max_days=10, round_count=1):
    day_clicked = 0
    months_checked = 0

    while months_checked < max_months and day_clicked < max_days:
        # Đảm bảo calendar sẵn sàng trước khi đọc
        _wait_for_calendar_ready(driver, wait)

        try:
            month_label = driver.find_element(By.CSS_SELECTOR, "button.mat-calendar-period-button span").text.strip()
        except Exception:
            month_label = "UNKNOWN"

        # Lấy các ô ngày có thể click
        day_els = driver.find_elements(By.CSS_SELECTOR, DAY_CELL_SELECTOR)
        clickable_days = []
        for d in day_els:
            try:
                # Bỏ ô rỗng
                if not d.text.strip():
                    continue
                # Đảm bảo TD không disabled (đã lọc ở CSS, nhưng kiểm tra thêm cho chắc)
                td = d.find_element(By.XPATH, "..")
                if "mat-calendar-body-disabled" in td.get_attribute("class"):
                    continue
                clickable_days.append(d)
            except Exception:
                continue

        if clickable_days:
            logger.info(f"✅ {month_label}: Tìm thấy {len(clickable_days)} ngày khả dụng")
            for d in clickable_days:
                if day_clicked >= max_days:
                    break
                try:
                    driver.execute_script("arguments[0].click();", d)
                    logger.info(f"👉 Click ngày: {d.text}")
                    random_sleep(1.2, 2.2)
                    if select_time_slot(driver):  # chỉ dừng khi confirm thành công
                        return "DONE"
                    day_clicked += 1
                except Exception as e:
                    logger.warning(f"⚠️ Không click được ngày {d.text}: {e}")
        else:
            logger.warning(f"⚠️ {month_label}: Không có ngày khả dụng")

        if day_clicked >= max_days:
            logger.info(f"⛔ Đã click đủ {max_days} ngày, dừng duyệt tháng")
            return True

        # Sang tháng kế
        try:
            prev_label = month_label
            next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mat-calendar-next-button")))
            driver.execute_script("arguments[0].click();", next_btn)
            months_checked += 1
            _wait_for_calendar_ready(driver, wait, expect_change=True, prev_label=prev_label)
        except Exception:
            logger.error("❌ Không thể sang tháng tiếp theo, dừng lại")
            break

# -----------------------
# 2.5 Chọn giờ + xác nhận
# -----------------------
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
                (By.CSS_SELECTOR, ".reservation__hours .tiles--hours button.tiles__link")
            )
        )
        logger.info(f"✅ Tìm thấy {len(hours)} giờ khả dụng")

        for h in hours:
            try:
                driver.execute_script("arguments[0].click();", h)
                logger.info(f"👉 Đã click giờ: {h.text.strip()}")
                random_sleep(1, 2)

                # chờ confirm dialog
                confirm = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".mat-dialog-actions button[color='primary']")
                    )
                )
                driver.execute_script("arguments[0].click();", confirm)
                logger.info("✅ Đã xác nhận giờ hẹn thành công")
                return True  # thành công thì stop

            except Exception as e:
                logger.warning(f"⚠️ Giờ {h.text.strip()} không đặt được: {e}")
                continue

    except Exception as e:
        logger.error(f"❌ Không tìm thấy giờ: {e}")

    return False


def notify_done():
    """Thông báo khi tất cả user đã hoàn thành"""
    logger.info("\n🎉🎉🎉 TẤT CẢ USER ĐÃ HOÀN THÀNH QUY TRÌNH 🎉🎉🎉\n")
