import time
import random
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from tqdm import tqdm

# ログの設定
logging.basicConfig(
    filename='instagram_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 設定ファイルの読み込み
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("config.json ファイルが見つかりません。")
    exit(1)

# 設定の取得
username = config['username']
password = config['password']
hashtag = config['hashtag']
chrome_driver_path = config['chrome_driver_path']
max_likes = config['max_likes']


def random_wait(min_time: float = 2, max_time: float = 5) -> float:
    return random.uniform(min_time, max_time)


def wait_and_click(
    driver: webdriver.Chrome,
    selector: str,
    by: By = By.CSS_SELECTOR,
    timeout: int = 10
) -> None:
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(random_wait(0.5, 1.5))
        element.click()
        time.sleep(random_wait())
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)
    except Exception as e:
        logging.error(f"エレメントのクリックに失敗しました: {selector}, エラー: {e}")
        raise


# WebDriverの設定
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

try:
    # ログイン処理
    driver.get('https://www.instagram.com/accounts/login/')
    time.sleep(random_wait(3, 6))

    user_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'username'))
    )
    pass_input = driver.find_element(By.NAME, 'password')
    user_input.send_keys(username)
    pass_input.send_keys(password)
    pass_input.send_keys(Keys.RETURN)

    # ログイン後の待機とダイアログの処理
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[contains(text(), '後で')]"
            ))
        )
        wait_and_click(driver, "//button[contains(text(), '後で')]", By.XPATH)
        logging.info("ログイン情報保存ダイアログで「後で」を選択しました")
    except TimeoutException:
        logging.info("ログイン情報保存ダイアログが表示されませんでした")

    # 検索ボタンをクリック
    try:
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "a[role='link'][tabindex='0'] svg[aria-label='検索']"
            ))
        )
        driver.execute_script("arguments[0].click();", search_button)
        logging.info("検索ボタンをクリックしました")
        time.sleep(random_wait(2, 4))
    except Exception as e:
        logging.error(f"検索ボタンのクリックに失敗しました: {e}")
        print(f"検索ボタンのクリックに失敗しました: {e}")
        raise  # エラーを発生させてスクリプトを終了

    # 検索入力フィールドを探して入力
    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'input[aria-label="検索入力"]'
            ))
        )
        search_input.send_keys(f'#{hashtag}')
        time.sleep(random_wait(1, 3))
        search_input.send_keys(Keys.RETURN)
        time.sleep(random_wait(2, 4))
    except Exception as e:
        logging.error(f"検索入力に失敗しました: {e}")
        print(f"検索入力に失敗しました: {e}")
        raise  # エラーを発生させてスクリプトを終了

    # 検索結果の待機
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
        )
        logging.info(f"ハッシュタグ '#{hashtag}' の検索結果を表示")
        print(f"ハッシュタグ '#{hashtag}' の検索結果を表示")
    except Exception as e:
        logging.error(f"検索結果の表示に失敗しました: {e}")
        print(f"検索結果の表示に失敗しました: {e}")
        raise  # エラーを発生させてスクリプトを終了

    # 最初の投稿をクリック
    try:
        first_post = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'article a'))
        )
        driver.execute_script("arguments[0].click();", first_post)
        logging.info("最初の投稿をクリックしました")
        time.sleep(random_wait(2, 4))
    except Exception as e:
        logging.error(f"最初の投稿のクリックに失敗しました: {e}")
        print(f"最初の投稿のクリックに失敗しました: {e}")
        raise  # エラーを発生させてスクリプトを終了

    # 投稿を順番にいいね
    for i in tqdm(range(max_likes), desc="いいね処理"):
        try:
            # いいねボタンを探してクリック
            like_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//svg[@aria-label='いいね' or @aria-label='いいね!']"
                ))
            )
            if 'いいね済み' not in like_button.get_attribute('aria-label'):
                like_button.click()
                logging.info(f"投稿 {i+1} にいいねしました")
            else:
                logging.info(f"投稿 {i+1} は既にいいね済みです")

            time.sleep(random_wait(3, 7))

            # 次の投稿へ
            wait_and_click(driver, 'svg[aria-label="次へ"]')

        except (
            TimeoutException,
            NoSuchElementException,
            StaleElementReferenceException
        ) as e:
            logging.error(f"投稿 {i+1} の処理中にエラーが発生しました: {e}")
            print(f"投稿 {i+1} の処理中にエラーが発生しました: {e}")
            # エラーが発生した場合、次の投稿に移動を試みる
            try:
                wait_and_click(driver, 'svg[aria-label="次へ"]')
            except Exception:
                logging.error("次の投稿への移動に失敗しました。スクリプトを終了します。")
                break
            continue

    logging.info("処理が完了しました")
    print("処理が完了しました")

except Exception as e:
    logging.error(f"エラーが発生しました: {e}")
    print(f"エラーが発生しました: {e}")

finally:
    # スクリプト終了時にブラウザを閉じるかどうかを選択
    close_browser = input("ブラウザを閉じますか？ (y/n): ").lower().strip()
    if close_browser == 'y':
        driver.quit()
        print("ブラウザを閉じました")
    else:
        print("ブラウザは開いたままです。手動で閉じてください。")