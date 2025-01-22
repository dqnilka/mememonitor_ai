import logging
import time
import pickle
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)

def collect_tweets(query, target_date, max_tweets):
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

        collected_count = 0
        while collected_count < max_tweets:
            tweet_elements = driver.find_elements(By.CSS_SELECTOR, 'article')
            logging.info(f"Найдено {len(tweet_elements)} твитов. Собрано: {collected_count}/{max_tweets}")

            for tweet_element in tweet_elements:
                try:
                    date = tweet_element.find_element(By.CSS_SELECTOR, 'time').get_attribute('datetime')
                    if date.split("T")[0] > target_date:
                        continue
                    elif date.split("T")[0] < target_date:
                        logging.info(f"Достигнуты твиты за более раннюю дату ({date.split('T')[0]}). Остановка.")
                        driver.quit()
                        save_to_csv(tweets_data, 'collected_tweets.csv')
                        return tweets_data

                    text = tweet_element.find_element(By.CSS_SELECTOR, 'div[lang]').text
                    user = tweet_element.find_element(By.CSS_SELECTOR, 'div[dir="ltr"] span').text
                    tweets_data.append({'tweet': text, 'user': user, 'date': date})
                    collected_count += 1

                    logging.info(f"Собраны данные для твита: {{'tweet': {text}, 'user': {user}, 'date': {date}}}")

                    if collected_count >= max_tweets:
                        break

                except Exception as e:
                    logging.error(f"Ошибка при обработке твита: {e}")
                    continue

            logging.info("Скроллим вниз...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

    finally:
        driver.quit()
        save_to_csv(tweets_data, 'collected_tweets.csv')
        logging.info("Закрытие веб-драйвера.")

    return tweets_data


def save_to_csv(data, file_path):
    if data:
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        logging.info(f"Сохранено {len(data)} твитов в файл {file_path}.")
    else:
        logging.info("Нет данных для сохранения.")
