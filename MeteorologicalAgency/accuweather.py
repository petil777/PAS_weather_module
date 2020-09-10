import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import glob
import asyncio
from myutil import json_print
from koenchanger import KoEnSoundChanger

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
    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.exit_flag = False
        self.region_name = None
        self.target_file_name = None
        self.new_href_link = None
        self.result_data = None

    def file_write(self):
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.target_file_name = self.file_dir + 'accuweather_' + str(dt) + '_' + str(self.region_name)
        with open(self.target_file_name, 'w') as fi:
            # To allow special character for temparature, ensure_ascii=false
            fi.write(json.dumps(self.result_data, indent=4, ensure_ascii=False))

    # def find_file(self, region):
    #     target_files = glob.glob(self.file_dir + 'accuweather_*')
    #     for files in target_files:
    #         target_date = files.split('_')[1]
    #         target_region = files.split('_')[2]
    #         if bool(re.search(region, target_region)) is not True:
    #             continue
            
    #         dif = datetime.now() - datetime.strptime(target_date, '%Y-%m-%d %H:%M:%S') 
    #         days, seconds = dif.days, dif.seconds
    #         hours = days*24 + seconds/3600
    #         if hours <= self.hours_min:
    #             self.target_file_name = files
                
            
    async def process_all(self, region):
        region= str.lower(region).strip()


        # if self.target_file_name is not None:
        #     with open(self.target_file_name, 'r') as fr:
        #         data = fr.read()
        #         self.result_data = json.loads(data)

        #This may be finishied in no time
        region = KoEnSoundChanger().ko_to_en_sound(region) 

        # To ensure former query finished, used await. (requests will be fast)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.region_search, region)
        if self.exit_flag == True: return False
        await loop.run_in_executor(None, self.redirection_for_region_engname)
        if self.exit_flag == True: return False
        await loop.run_in_executor(None, self.get_daily_weather)

        if self.exit_flag == True: return False
        else : return True

    def region_search(self, region):
        query_url = 'https://www.accuweather.com/en/search-locations?query='
        query_url += region
        # Don't know why but this query should be changed with User-Agent different with real browser agent
        ### Search region by input
        res = requests.get(query_url, headers={'User-Agent' : 'my agent'})
        if res.status_code != 200:
            json_print('AccuWeather Server not responsded')
            self.exit_flag=True
            return
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
        </a>
        </div>]
    """
        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            res_div = soup.find_all("div", {'class' : 'search-results'})

            href_link = None
            region_code = None
            for res in res_div:
                res_a = res.find_all("a")
                if len(res_a) == 0 : continue
                for target_a in res_a:
                    p = re.compile(region)
                    matched_words = p.findall(str.lower(target_a.text.strip()))
                    
                    if len(matched_words) > 0:
                        self.region_name = matched_words[0]
                        # /web-api/three-day-redirect?key=1-2330398_30_al&target=
                        href_link = target_a['href']
                        # 1-2330398_30_al
                        region_code = href_link.split('key=')[1].split('&')[0]
                        self.new_href_link = 'https://accuweather.com' + href_link
                    break
                if region_code is not None:break
        except Exception as err:
            json_print("Error occured while parsing region code in accuweather")
            self.exit_flag = True
            return

        if self.new_href_link is None:
            json_print("href link is None")
            self.exit_flag=True
            return
        
    def redirection_for_region_engname(self):
        res = requests.get(self.new_href_link, headers=headers)
        if res.status_code != 200:
            json_print('AccuWeather Server not responsded')
            self.exit_flag=True
            return
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
        if daily_result.status_code != 200:
            json_print('AccuWeather Server not responsded')
            self.exit_flag=True
            return

        try:
            soup = BeautifulSoup(daily_result.text, 'html.parser')
            daily_forecasts = soup.find_all('a', {'class' : 'daily-forecast-card'})

            self.result_data = []
            forecast_dates = []
            weathers = []
            temperatures = []
            precipitations = []
            for daily in daily_forecasts:
                date = daily.select(".info > .date ")[0].text.strip() # Fri\n9/18
                temp = daily.select(".info > .temp")[0].text.strip() # 25°\n/17°
                weather = daily.select(".phrase")[0].text.strip()
                precip = daily.select(".precip")[0].text.strip()
                forecast_dates.append(date)
                temperatures.append(temp)
                precipitations.append(precip)
                weathers.append(weather)
                # {'temp': '23°\n/20°', 'precip': '73%', 'forecast_date': 'Mon\n9/7', 'phrase': 'Wind and rain from typhoon'}
        except Exception as err:
            json_print('Error occured while parsing get_daily_weather in accuweather')
            self.exit_flag=True
            return

        for idx, date in enumerate(forecast_dates):
            self.result_data.append({'forecast_date':date, 'weather' : weathers[idx], 'temp':temperatures[idx], 'precip':precipitations[idx]})

        # self.file_write()
        # print(json.dumps(self.result_data, indent=4, ensure_ascii=False))
        json_print(self.result_data)