import requests
from bs4 import BeautifulSoup
import re
import json
import asyncio
from datetime import datetime, timedelta
from myutil import json_print
from koenchanger import KoEnSoundChanger

class DarkSkyAgency():
    """
        Link : https://darksky.net/
            Get its data from NOAA(미국 해양 대기청)
        Mechanism [process_all]
        ------------------------------
        1.  [KoEnSoundChanger] : check region input and convert to english sound if it's not english
            Have to erase district in this agency for compatible with other agency (도로명주소...)
        2. [get_geoinfo] : get latitude, longitude of input
        3. [get_daily_weather] : get daily weather for geoinfo.
    """
    def __init__(self):
        self.geo_info = None
        self.exit_flag = False
        self.result_data = None
    async def process_all(self, region):
        #Have to erase district so try 2 times
        region_name = KoEnSoundChanger().ko_to_en_sound(region)
        region_without_district_name = KoEnSoundChanger().ko_to_en_sound(region[:-1])
        self.get_geoinfo(region_name, region_without_district_name)
        self.get_daily_weather()
        if self.exit_flag == False:
            json_print(self.result_data)

    def get_geoinfo(self, region_name, region_without_district_name):
        """Get geoinfo

        Args:
            region_name (str): region name in english
            region_without_district_name (str):  region name without last word.(before converting to eng. Or originally it was englisth too.)
        """
        geo_query_url = 'https://darksky.net/geo?q='
        
        def do_query(retry, geo_query_url):
            if retry==False:
                query_url = geo_query_url + region_name
            else:
                query_url = geo_query_url + region_without_district_name
            res = requests.get(query_url)
            if res.status_code==200:
                self.geo_info = json.loads(res.text)

        do_query(False, geo_query_url)
        if self.geo_info is None:
            do_query(True, geo_query_url)

    def get_daily_weather(self):
        if self.geo_info is None:
            json_print("No geo info found for region")
            self.exit_flag=True
            return
        query_url = 'https://darksky.net/forecast/' + str(self.geo_info['latitude'])+','+str(self.geo_info['longitude']) + '/si12/ko'
        try:
            res = requests.get(query_url)
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            json_print('Darksky weather request failed : ', err)
            self.exit_flag=True
            return

        try:
            self.result_data = []
            soup = BeautifulSoup(res.text, 'html.parser')
            day_details = soup.find_all('div', {'class' : "dayDetails"})

            cur_day = datetime.now()
            for day_detail in day_details:
                weather = day_detail.find('div', {'class' : 'summary'}).text
                
                high_temp_info = day_detail.find('span', {'class' : 'highTemp swip'})
                low_temp_info = day_detail.find('span', {'class' : 'lowTemp swap'})

                high_temp = high_temp_info.select('.temp')[0].text.strip()
                low_temp = low_temp_info.select('.temp')[0].text.strip()
                temp = str(high_temp) + '/n' + str(low_temp)

                precip_info = day_detail.find('div', {'class' : 'precipAccum swap'})
                precip_num = precip_info.select('.num.swip')[0].text.strip()
                precip_unit = precip_info.select('.unit.swap')[0].text.strip()
                precip = str(precip_num) + str(precip_unit)

                forecast_date = str(cur_day.year) + '/' + str(cur_day.month) + '/' + str(cur_day.day)
                self.result_data.append({'forecast_date' : forecast_date, 'weather' : weather,\
                     'temp' : temp, 'precip' : precip})

                cur_day += timedelta(days=1)

        except Exception as err:
            json_print("darksky error while parsing", err)
            self.exit_flag = True
            return