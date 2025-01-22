from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import pickle

def twitter_login():
    driver_path = "chromedriver.exe"  
    auth_token = "0d03ffb70d0fc39ffd7d0bc8c23e44b29fe5c59c"  

    service = Service(executable_path=driver_path)
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://x.com")
        time.sleep(3)

        driver.add_cookie({"name": "auth_token", "value": auth_token, "domain": ".x.com"})
        driver.refresh()
        time.sleep(5)

        with open("cookies.pkl", "wb") as file:
            pickle.dump(driver.get_cookies(), file)
        print("Cookies сохранены.")
    finally:
        driver.quit()
