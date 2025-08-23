import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import random_sleep
from config import LOGIN_URL
from logger import setup_logger

logger = setup_logger()

def login(username, password, driver):
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 15)

    user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="email"]')))
    random_sleep(1.05, 2)
    pass_input = driver.find_element(By.CSS_SELECTOR, 'input[formcontrolname="password"]')
    user_input.clear()
    pass_input.clear()

    for ch in username:
        user_input.send_keys(ch)
        random_sleep(0.05, 0.1)
    
    user_input.send_keys(Keys.TAB)
    random_sleep(0.05, 1)

    for ch in password:
        pass_input.send_keys(ch)
        random_sleep(0.05, 0.1)
    pass_input.send_keys(Keys.TAB)

    sign_in_button = driver.find_element(By.CSS_SELECTOR, 'button.btn.btn--submit')
    random_sleep(0.1, 2)
    driver.execute_script("arguments[0].click();", sign_in_button)

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[routerlink="/home/cases-choose"]')))
        logger.info("✅ Login thành công")
        return True
    except:
        logger.error("❌ Login thất bại")
        return False
