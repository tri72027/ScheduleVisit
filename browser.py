import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from config import USE_INCOGNITO  # <-- sửa lại chỗ này

def init_driver():
    options = uc.ChromeOptions()
    if USE_INCOGNITO:
        options.add_argument("--incognito")

    driver = uc.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """},
    )
    return driver
