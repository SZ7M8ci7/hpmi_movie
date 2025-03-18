from collections import Counter, defaultdict
import io
import re
import time
from bs4 import BeautifulSoup
import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import cv2
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont
from PIL import Image, ImageOps
import base64
import chromedriver_binary
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://hypnosismic-movie.com',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}
regions = {
    "hokkaido": ["hokkaido"],
    "tohoku": ["aomori", "miyagi", "fukushima"],
    "kanto": ["tokyo", "kanagawa", "saitama", "chiba", "ibaraki", "tochigi", "gunma", "yamanashi"],
    "chubu": ["niigata", "nagano", "toyama", "aichi", "gifu", "shizuoka"],
    "kinki": ["osaka", "hyogo", "kyoto", "nara"],
    "chugokushikoku": ["okayama", "hiroshima", "ehime", "kochi"],
    "kyushuokinawa": ["fukuoka", "kumamoto", "okinawa"]
}
divisions = ["Buster Bros!!!","MAD TRIGGER CREW","Fling Posse","麻天狼","どついたれ本舗","Bad Ass Temple","言の葉党"]
# 英語表記と日本語表記の対応辞書
japan_prefectures = {
    "aichi": "愛知",
    "aomori": "青森",
    "chiba": "千葉",
    "chubu": "中部",
    "chugokushikoku": "中国四国",
    "ehime": "愛媛",
    "fukuoka": "福岡",
    "fukushima": "福島",
    "gifu": "岐阜",
    "gunma": "群馬",
    "hiroshima": "広島",
    "hokkaido": "北海道",
    "hyogo": "兵庫",
    "ibaraki": "茨城",
    "kanagawa": "神奈川",
    "kanto": "関東",
    "kinki": "近畿",
    "kochi": "高知",
    "kumamoto": "熊本",
    "kyoto": "京都",
    "kyushuokinawa": "九州・沖縄",
    "miyagi": "宮城",
    "nagano": "長野",
    "nara": "奈良",
    "niigata": "新潟",
    "okayama": "岡山",
    "okinawa": "沖縄",
    "osaka": "大阪",
    "saitama": "埼玉",
    "shizuoka": "静岡",
    "tochigi": "栃木",
    "tohoku": "東北",
    "tokyo": "東京",
    "toyama": "富山",
    "yamanashi": "山梨"
}
# 7種類のテンプレート画像のパスを設定
template_paths = [
    'chuou1.png'
    ,'chuou2.png'
    ,'ikebukuro1.png'
    ,'ikebukuro2.png'
    ,'nagoya1.png'
    ,'nagoya2.png'
    ,'osaka1.png'
    ,'osaka2.png'
    ,'shibuya1.png'
    ,'shibuya2.png'
    ,'shinjuku1.png'
    ,'shinjuku2.png'
    ,'yokohama1.png'
    ,'yokohama2.png'
]


def preprocess_image(image_cv):
    """透明背景に白文字の画像を適切に前処理する"""
    if image_cv is None:
        return None

    # 画像がすでにグレースケール（1チャンネル）の場合、変換不要
    if len(image_cv.shape) == 2:
        gray = image_cv
    elif image_cv.shape[-1] == 4:  # RGBA画像（透明チャンネル付き）
        alpha_channel = image_cv[:, :, 3]  # アルファチャンネル（透明度）
        gray = cv2.bitwise_not(alpha_channel)  # 透明部分を黒、文字部分を白に変換
    else:  # 通常の3チャンネル（RGB）の場合
        gray = cv2.cvtColor(image_cv, cv2.COLOR_RGB2GRAY)

    gray = cv2.GaussianBlur(gray, (1, 1), 0)  # ノイズ除去
    return gray

countaaa = 0
# テンプレート画像の読み込み（拡張子を除いた名前をキーにする）
templates = {path.rsplit(".", 1)[0]: preprocess_image(cv2.imread(path, -1)) for path in template_paths}
def match_canvas_with_templates(driver, templates):
    """ キャンバスの画像を取得し、テンプレートとマッチングして結果を辞書で返す """
    canvas_elements = driver.find_elements(By.TAG_NAME, "canvas")

    matched_counts = Counter()
    matched_images = []

    # 保存用フォルダを準備
    if not os.path.exists("matched_results"):
        os.makedirs("matched_results")
    if not os.path.exists("matched_raw"):
        os.makedirs("matched_raw")

    for index, canvas in enumerate(canvas_elements):
        try:
            width = int(canvas.get_attribute("width"))
            height = int(canvas.get_attribute("height"))

            if width == 170 and height >= 14:
                driver.execute_script("arguments[0].scrollIntoView();", canvas)
                time.sleep(0.1)  # スクロール後のレンダリング待機

                # JavaScriptで canvas の内容を取得
                data_url = driver.execute_script(
                    "return arguments[0].toDataURL('image/png').substring(22);", canvas
                )
                image_data = base64.b64decode(data_url)
                image = Image.open(io.BytesIO(image_data))

                # 生の画像を保存 (ここで追加した処理)
                # raw_image_path = f"matched_raw/raw_image_{index+1}.png"
                # image.save(raw_image_path)
                # print(f"[INFO] Raw image saved as {raw_image_path}")

                # 透過背景があるかチェック
                if image.mode == "RGBA":
                    alpha = image.getchannel("A")  # アルファチャンネルを取得
                    gray = ImageOps.invert(alpha)  # 透明部分を黒、文字部分を白に変換
                else:
                    gray = image.convert("L")  # 通常のグレースケール変換

                # OpenCVの形式に変換
                image_cv = np.array(gray)
                image_cv = preprocess_image(image_cv)

                # 最も類似度が高いテンプレートを見つける
                best_match_name = None
                best_match_score = -1  # 初期値を小さくしておく

                for template_name, template in templates.items():
                    if template is None:
                        continue
                    global countaaa

                    res = cv2.matchTemplate(image_cv, template, cv2.TM_CCOEFF_NORMED)
                    max_score = np.max(res)  # 最大の類似度を取得
                    if max_score > best_match_score:
                        best_match_score = max_score
                        best_match_name = template_name
                if best_match_score < 0.6:
                    countaaa+=1
                    cv2.imwrite(f"temp/image_cv{countaaa}.png", image_cv)
                    print(best_match_name, best_match_score, countaaa)
                # 最も類似したテンプレートのみカウント
                if best_match_name:
                    matched_counts[best_match_name] += 1

                    # 画像にラベルを追加
                    draw = ImageDraw.Draw(image)
                    font = ImageFont.load_default()  # デフォルトフォント
                    draw.text((5, 0), f"{best_match_name} ({best_match_score:.2f})", fill=(255, 0, 0), font=font)

                    matched_images.append(image)

        except Exception as e:
            print(f"[ERROR] Failed to process canvas: {e}")

    # # 一覧画像の作成
    # if matched_images:
    #     width, height = matched_images[0].size
    #     total_height = height * len(matched_images)
    #     combined_image = Image.new("RGB", (width, total_height))

    #     y_offset = 0
    #     for img in matched_images:
    #         combined_image.paste(img, (0, y_offset))
    #         y_offset += height

    #     combined_image.save("matched_results/matched_overview.png")
    #     print("[INFO] Matched result overview saved as matched_results/matched_overview.png")

    return dict(matched_counts)
MAX_RETRIES = 3
def get_victory_count(url):
    options = Options()
    options.headless = True
    options.add_argument('--headless')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get('https://hypnosismic-movie.com' + url)
    time.sleep(2)
    html_data = driver.page_source

    soup = BeautifulSoup(html_data, 'html.parser')
    theater_name = soup.find('p', class_='theater--name').get_text(strip=True)

    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            past_results_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='PAST RESULTS']"))
            )
            past_results_button.click()
            time.sleep(3)
            break  # 成功したらループを抜ける
        except:
            retry_count += 1
            print(f"[WARNING] PAST RESULTS ボタンが見つかりませんでした。リトライ回数: {retry_count}")
            time.sleep(2)

    if retry_count == MAX_RETRIES:
        print("[ERROR] 最大リトライ回数に達しました。処理を終了します。")
        driver.quit()
        return {}

    result = match_canvas_with_templates(driver, templates)

    driver.quit()
    print(theater_name, result)
    tmp = {division:0 for division in divisions}
    for key, val in result.items():
        if 'ikebukuro' in key:
            tmp['Buster Bros!!!'] += val
        if 'yokohama' in key:
            tmp['MAD TRIGGER CREW'] += val
        if 'shibuya' in key:
            tmp['Fling Posse'] += val
        if 'shinjuku' in key:
            tmp['麻天狼'] += val
        if 'osaka' in key:
            tmp['どついたれ本舗'] += val
        if 'nagoya' in key:
            tmp['Bad Ass Temple'] += val
        if 'chuou' in key:
            tmp['言の葉党'] += val

    
    return theater_name, tmp

def get_theater_list():
    shinjuku_9 = {}
    response = requests.get('https://hypnosismic-movie.com/voting-status/')
    response.encoding = 'utf-8'  # 文字エンコーディングを指定
    html_data = response.text
    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(html_data, 'html.parser')
    regions_links = {}
    for region, prefectures in regions.items():
        theater_links = {}
        for prefecture in prefectures:
            ul_tag = soup.find('ul', class_='theater--' + prefecture)
            if ul_tag:
                links = [shinjuku_9.get(a['href'], a['href']) for a in ul_tag.find_all('a', href=True)]
                theater_links[prefecture] = links
        regions_links[region] = theater_links
    return regions_links
regions_links = get_theater_list()
import csv
output_file = "battle_results_temp.csv"
with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    for region, prefectures in regions_links.items():
        for prefecture, links in prefectures.items():
            for link in links:
                time.sleep(1)
                theater_name,battle_results = get_victory_count(link)
                writer.writerow([japan_prefectures[region], japan_prefectures[prefecture], theater_name] + [battle_results.get(division, 0) for division in divisions] + [link])

