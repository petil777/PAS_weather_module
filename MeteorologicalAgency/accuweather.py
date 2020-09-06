import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import glob

headers = {
    'Connection': 'keep-alive',
    'User-Agent': 'my agent',
    'Accept': '*/*',
    'Origin': 'null',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://www.accuweather.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}


# https://www.accuweather.com/
class AccuWeatherAgency():
    """
    File Format : accuweather_2020-09-05 20:03:57_분당
    """
    def __init__(self, file_dir, must_query=False, hours_min=3):
        self.file_dir = file_dir
        self.must_query = must_query
        self.hours_min = hours_min
        self.region_name = None
        self.target_file_name = None
        self.result_data = None
    def find_file(self, region):
        
        target_files = glob.glob(self.file_dir + 'accuweather_*')
        for files in target_files:
            target_date = files.split('_')[1]
            target_region = files.split('_')[2]
            if bool(re.search(region, target_region)) is not True:
                continue
            
            dif = datetime.now() - datetime.strptime(target_date, '%Y-%m-%d %H:%M:%S') 

            days, seconds = dif.days, dif.seconds
            hours = days*24 + seconds/3600
            if hours <= self.hours_min:
                self.target_file_name = files
                
            
    def process_all(self, region):
        region= str.lower(region).strip()
        
        if self.must_query == False:
            self.find_file(region)

        #if self.target_file_name --> get file name success. So don't query
        print('Found target File : ', self.target_file_name)
        if self.target_file_name is not None:
            with open(self.target_file_name, 'r') as fr:
                data = fr.read()
                self.result_data = json.loads(data)
        else: 
            self.region_search(region)
            self.redirection_for_region_engname()
            self.get_daily_weather()

    def region_search(self, region):
        query_url = 'https://www.accuweather.com/ko/search-locations?query='
        query_url += region
        # Don't know why but this query should be changed with User-Agent different with real browser agent
        ### Search region by input
        res = requests.get(query_url, headers={'User-Agent' : 'my agent'})
        if res.status_code != 200:
            print('AccuWeather Server not responsded')
            exit(0)
            """
    res_div Format
    -------------------------------------------------------------------
            [<div class="search-results">
        </div>, <div class="search-results">
        <a href="/web-api/three-day-redirect?key=1-2330398_30_al&amp;target=">
                        분당구,  경기도, KR
                        
                            <span>(1-2330398_30_AL)</span>
        </a>
        <a href="/web-api/three-day-redirect?key=1-1318085_30_al&amp;target=">
                        분당동,  경기도, KR
                        
                            <span>(1-1318085_30_AL)</span>
        </a>
        <a href="/web-api/three-day-redirect?key=2330398&amp;target=">
                        분당구,  경기도, KR
                        
                            <span>(2330398)</span>
        </a>
        <a href="/web-api/three-day-redirect?key=1318085&amp;target=">
                        분당동,  경기도, KR
                        
                            <span>(1318085)</span>
        </a>
        </div>]
    """
        soup = BeautifulSoup(res.text, 'html.parser')
        res_div = soup.find_all("div", {'class' : 'search-results'})

        href_link = None
        region_code = None
        for res in res_div:
            res_a = res.find_all("a")
            if len(res_a) == 0 : continue
            for target_a in res_a:
                p = re.compile(region)
                matched_words = p.findall(target_a.text.strip())
                # if(bool(re.search(region, target_a.text.strip()))):
                if len(matched_words) > 0:
                    self.region_name = matched_words[0]
                    # /web-api/three-day-redirect?key=1-2330398_30_al&target=
                    href_link = target_a['href']
                    # 1-2330398_30_al
                    region_code = href_link.split('key=')[1].split('&')[0]
                    self.new_href_link = 'https://accuweather.com' + href_link
                break
            if region_code is not None:break
        
        if self.new_href_link is None:
            print("href link is None")
            exit(0)
        
    def redirection_for_region_engname(self):
        res = requests.get(self.new_href_link, headers=headers)
        if res.status_code != 200:
            print('AccuWeather Server not responsded')
            exit(0)
        # check with soup.get_text
        """
            [daily_tag] format
            ----------------------------------------------------------------------
            <a class="subnav-item" data-gaid="daily" href="/ko/kr/bundang-gu/1-2330398_30_al/daily-weather-forecast/1-2330398_30_al">
            <span>일별</span>
            </a>
        """
        soup = BeautifulSoup(res.text, 'html.parser')
        daily_tag = soup.find('a', {'data-gaid' : "daily"})
        # To use English version
        replace_tag = daily_tag['href'].replace('ko', 'en')

        self.daily_query_url = 'https://accuweather.com' + replace_tag

    def get_daily_weather(self):
        daily_result = requests.get(self.daily_query_url, headers=headers)
        soup = BeautifulSoup(daily_result.text, 'html.parser')

        daily_forecasts = soup.find_all('a', {'class' : 'daily-forecast-card'})

        daily_list = []
        for daily in daily_forecasts:
            forecast_date = daily.select(".info > .date ")[0].text.strip()
            temp = daily.select(".info > .temp")[0].text.strip()
            phrase = daily.select(".phrase")[0].text.strip()
            precip = daily.select(".precip")[0].text.strip()
            # {'temp': '23°\n/20°', 'precip': '73%', 'forecast_date': 'Mon\n9/7', 'phrase': 'Wind and rain from typhoon'}
            daily_list.append({'forecast_date':forecast_date, 'temp':temp, 'phrase':phrase, 'precip':precip})
    
        self.result_data = daily_list
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.target_file_name = self.file_dir + 'accuweather_' + str(dt) + '_' + str(self.region_name)
        with open(self.target_file_name, 'w') as fi:
            # To allow special character for temparature, ensure_ascii=false
            fi.write(json.dumps(daily_list, indent=4, ensure_ascii=False))
            