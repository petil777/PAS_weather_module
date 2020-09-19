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


class AccuWeatherAgency():
    """
        Link : https://www.accuweather.com/
        Mechanism [process_all]
        1. [KoEnSoundChanger] check region input and convert to english sound if it's not english
        2. [region_search] : call region_search function 
        3. [get_daily_query_url] : get redirection api in html code for redirection with region_code inserted in site
        4. [get_daily_weather] : get weather
    """
    def __init__(self, file_dir=None):
        """

        Parameters
        ----------
        file_dir : str (default None)
            file directory to store data if necessary
        
        Other Parameters
        ----------
        exit_flag : bool
            Flag to stop anywhere.
        region_name : str
            Can be english or korean both. (ex. 분당구, bundanggu)
            But can't having district name. (ex. 서울시 강남구 x.  서울시 o, 강남 o , 성남 o, 분당 o )
            If have more than one district, select the first one by site (ex. 분당 -> 분당구  insted of 분당동)
        target_file_name: str
            filename to store
        new_href_link : str
            Redirection link for get_daily_query_url function
        result_data : Array
            Format Example: [{"forecast_date": "Sat\n9/19", "weather": "Mostly sunny", "temp": "26°\n/15°", "precip": "0%"}, {...},...]
        """
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
                
            
    async def process_all(self, region):
        region= str.lower(region).strip()

        #This may be finishied in no time
        region_name = KoEnSoundChanger().ko_to_en_sound(region) 
        region_without_district_name = KoEnSoundChanger().ko_to_en_sound(region[:-1])
        # To ensure former query finished, used await. (requests will be fast)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.region_search, region_name, region_without_district_name)
        if self.exit_flag == True: return False
        await loop.run_in_executor(None, self.get_daily_query_url)
        if self.exit_flag == True: return False
        await loop.run_in_executor(None, self.get_daily_weather)

        if self.exit_flag == True: return False
        else : return True

    def region_search(self, region, region_without_district):
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

        Parameters
        ----------
        region : str
            Suppose region has no district. seoul. gangnam). Try First with this
        region_without_district : str
            Suppose region has district name (seoulsi, gangnamgu)
        """
        
        region_query_url = 'https://www.accuweather.com/en/search-locations?query='

        def do_query(retry, region_query_url):
            if retry==False:
                query_url = region_query_url + region
            else:
                query_url = region_query_url + region_without_district
            # Don't know why but this query should be changed with User-Agent different with real browser agent
            ### Search region by input
            res = requests.get(query_url, headers={'User-Agent' : 'my agent'})
            if res.status_code != 200:
                json_print('AccuWeather Server not responsded')
                self.exit_flag=True
                return

            try:
                soup = BeautifulSoup(res.text, 'html.parser')
                res_div = soup.find_all("div", {'class' : 'search-results'})

                href_link = None
                region_code = None
                for res in res_div:
                    res_a = res.find_all("a")
                    if len(res_a) == 0 : continue
                    for target_a in res_a:
                        p = re.compile(region_without_district if retry else region)
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
                if retry==False : do_query(True, region_query_url)
                json_print("Error occured while parsing region code in accuweather")
                self.exit_flag = True
                return

        do_query(False, region_query_url)
        #retry with no error
        if self.new_href_link is None : do_query(True, region_query_url)

        if self.new_href_link is None:
            json_print("href link is None")
            self.exit_flag=True
            return
        
    def get_daily_query_url(self):
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