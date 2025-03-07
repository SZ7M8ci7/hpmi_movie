from collections import Counter, defaultdict
import re
import time
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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

def count_distinct(data):
    entries = re.split(r'(\d{4}\.\d{2}\.\d{2})', data)[1:]
    past_data_str = ""
    battle_results_distinct = defaultdict(int)
    for i in range(0, len(entries), 2):
        date = entries[i].strip()
        match_data = entries[i + 1].strip()
        # Splitting match data based on teams (assuming teams have non-numeric names)
        match_entries = re.findall(r'([^\d%]+)([\d%]+)', match_data)

        for team, scores in match_entries:
            scores = [str(x.strip('%')) for x in scores.split('%') if x]
            if past_data_str == "".join([date, team.strip()] + scores):
                continue
            past_data_str = "".join([date, team.strip()] + scores)
            battle_results_distinct[team.strip()] += 1
    print(battle_results_distinct)
    return battle_results_distinct

def get_victory_count(url):
    
    options = Options()
    options.headless = True  # ヘッドレスモードで実行

    options.add_argument('--headless')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    # URLにアクセス
    driver.get('https://hypnosismic-movie.com' + url)
    time.sleep(3)
    html_data = driver.page_source
    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(html_data, 'html.parser')
    # 劇場名を取得
    theater_name = soup.find('p', class_='theater--name').get_text(strip=True)
    # すべての要素を取得
    elements = driver.find_elements("css selector", "*")

    # 疑似要素 `::before` の content を取得
    content_list = []
    for element in elements:
        content = driver.execute_script(
            "return window.getComputedStyle(arguments[0], '::before').content;", element
        )
        if content and content != 'none':  # 無効なものは除外
            content = content.strip('"')  # 余分な `" "` を削除

            # Unicode 制御文字の正規表現
            control_chars_pattern = re.compile(r'[\u200b-\u200f\u2060-\u206f]')

            # 制御文字を削除
            content = control_chars_pattern.sub('', content)
            content_list.append(content)

    # 出現回数をカウント
    content_counts = Counter(content_list)
    
    driver.quit()
    return theater_name,content_counts
    
def get_theater_list():
    shinjuku_9 = {'/voting-status/cinema/#N9C6B00698036': '/voting-status/cinema/#N9C6B006CB0AB'}
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

output_file = "battle_results.csv"
with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    for region, prefectures in regions_links.items():
        for prefecture, links in prefectures.items():
            for link in links:
                time.sleep(1)
                theater_name,battle_results = get_victory_count(link)
                writer.writerow([japan_prefectures[region], japan_prefectures[prefecture], theater_name] + [battle_results.get(division, 0) for division in divisions] + [link])
                