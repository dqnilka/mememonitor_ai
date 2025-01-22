import logging
import time
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)

def collect_tweets(query, target_date, tweet_count):
    driver_path = 'chromedriver.exe'
    service = Service(executable_path=driver_path)
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    tweets_data = []
    try:
        logging.info("Открытие главной страницы Twitter...")
        driver.get("https://x.com")
        time.sleep(3)

        logging.info("Загрузка cookies...")
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(3)

        logging.info("Поиск твитов...")
        search_url = f"https://x.com/search?q={query}"
        driver.get(search_url)
        time.sleep(3)

        logging.info("Переключение на вкладку 'Latest'...")
        latest_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Latest']"))
        )
        latest_tab.click()
        time.sleep(3)

        while len(tweets_data) < tweet_count:
            tweet_elements = driver.find_elements(By.CSS_SELECTOR, 'article')
            logging.info(f"Найдено {len(tweet_elements)} твитов.")

            for tweet_element in tweet_elements:
                if len(tweets_data) >= tweet_count:
                    break
                try:
                    date = tweet_element.find_element(By.CSS_SELECTOR, 'time').get_attribute('datetime')
                    if date.split("T")[0] > target_date:
                        continue
                    elif date.split("T")[0] < target_date:
                        return tweets_data

                    text = tweet_element.find_element(By.CSS_SELECTOR, 'div[lang]').text
                    user = tweet_element.find_element(By.CSS_SELECTOR, 'div[dir="ltr"] span').text
                    tweets_data.append({'tweet': text, 'user': user, 'date': date})
                    logging.info(f"Собраны данные для твита: {{'tweet': {text}, 'user': {user}, 'date': {date}}}")
                except Exception as e:
                    logging.error(f"Ошибка при обработке твита: {e}")
                    continue

            logging.info("Скроллим вниз...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

    finally:
        driver.quit()
        logging.info(f"Закрытие веб-драйвера. Собрано твитов: {len(tweets_data)}")
        return tweets_data
