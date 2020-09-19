import requests
from bs4 import BeautifulSoup
import json
import asyncio
from datetime import datetime
from koenchanger import KoEnSoundChanger
from myutil import json_print

# https://www.yr.no/?spr=eng
headers = {'Accept-Language':'en-US,en;q=0.8'}
class YrAgency():
    def __init__(self, file_dir, long_term=True):
        self.file_dir = file_dir
        self.long_term = long_term
        self.target_file_name = None
        self.exit_flag = False
        #Usually except district name.
        self.region_name = None
        self.real_query = None
        self.result_data =None
        self.koen_sound_converter = KoEnSoundChanger()
    async def process_all(self, region):
        region = str.lower(region).strip()
        # self.get_query(region)
        loop = asyncio.get_event_loop()
        # To ensure get query finish, used await. (requests will be fast)
        await loop.run_in_executor(None, self.get_query, region)
        if self.exit_flag == True:
            return False

        if self.long_term:
            await loop.run_in_executor(None, self.long_term_query)
        #Default
        else:
            await loop.run_in_executor(None,self.daily_query)

        if self.exit_flag == True:
            return False
        else:
            return True

    def file_write(self):
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.target_file_name = self.file_dir + 'yrweather_' + str(dt) + '_' + str(self.region_name)
        with open(self.target_file_name, 'w') as fi:
            # To allow special character for temparature, ensure_ascii=false
            fi.write(json.dumps(self.result_data, indent=4, ensure_ascii=False))  

    # region = bundang  gu(district)  (already english parsed)
    def get_query(self, region):

        self.region_name = region

        region_name = self.koen_sound_converter.ko_to_en_sound(region)
        region_ensound = self.koen_sound_converter.ko_to_en_sound(region[:-1])
        district_ensound = self.koen_sound_converter.ko_to_en_sound(region[-1])
        region_without_district_name = region_ensound

        if region_name == None:
            json_print('No proper changed en sound')
            self.exit_flag=True
            return

        region_query_url = 'https://www.yr.no/soek/soek.aspx?sted='
        
        def do_query(retry, region_query_url):
            if retry==False:
                query_url = region_query_url + region_name
            else:
                query_url = region_query_url + region_without_district_name
            #First query for searching region 
            # try:
            #     res = requests.get(query_url, headers=headers)
            #     res.raise_for_status()
            # except requests.exceptions.RequestException as err:
            #     json_print('Norway weather request failed : ')
            #     self.exit_flag=True
            #     return
            res = requests.get(query_url, headers=headers)
            if res.status_code != 200:
                json_print('yrWeather Server not responsded')
                self.exit_flag=True
                return
            try:
                soup = BeautifulSoup(res.text, 'html.parser')
                result_table = soup.find('table', {'class' : 'yr-table yr-table-search-results'})
                trs = result_table.find_all('tr')
                for idx, tr in enumerate(trs):
                    if idx ==0 : continue # table header
                    # change eng suppor url "https://www.yr.no/place/South_Korea/Gyeonggi/Bundang-gu/"
                    region_title = tr.find('a')['title']
                    web_api = tr.find('a')['href']
                    #bundang-  bundang-gu  seoul
                    if str.lower(region_title).startswith(region_without_district_name if retry else region_name): 
                        self.real_query = 'https://www.yr.no' + web_api
                        #Perfect match
                        if (str.lower(region_title) == region_name or \
                            str.lower(region_title) == region_ensound + '-' + district_ensound):
                            break
            except Exception as err:
                if retry==False: do_query(True, region_query_url)
                if self.real_query is not None : return
                json_print("Error occured while parsing get_query in norway agency : ")
                self.exit_flag=True
                return

        do_query(False, region_query_url)

    def daily_query(self):
        if self.real_query is None:
            json_print('real query is not set. please check region name with district')
            self.exit_flag=True
            return
        #Second query
        try:
            res = requests.get(self.real_query)
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            json_print('Norway weather request failed at second query : ')
            self.exit_flag=True
            return

        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            #yr-table yr-table-overview2 yr-popup-area
            results = soup.find_all('table', {'class' : 'yr-table yr-table-overview2 yr-popup-area'})

            
            self.result_data = []
            forecast_dates = []
            weathers = []
            temperatures = []
            precipitations = []

            for result in results:
                weather = []
                # Tomorrow, Monday 07/09/2020
                date = result.find('caption').text.strip()
                # winds = result.find_all('td', {'class' : 'txt-left'})    
                trs = result.find_all('tr')
            
                split_date = date.split('/')
                date = split_date[2]+'/'+split_date[1]+'/'+split_date[0].split(' ')[-1]
                forecast_dates.append(date)

                cells = result.select('tbody > tr')
                weather_cells =[]
                temp_cells = []
                precip_cells = []
                for cell in cells:
                    weather_cell = cell.find_all('td')[1]['title']
                    temp_cell = cell.find_all('td')[2].text
                    precip_cell = cell.find_all('td')[3].text

                    weather_cells.append(weather_cell)
                    temp_cells.append(temp_cell)
                    precip_cells.append(precip_cell)
                    
                weathers.append(weather_cells)
                temperatures.append(temp_cells)
                precipitations.append(precip_cells)
        
        except Exception as err:
            json_print("Error occured while parsing daily_query in norway weather")
            self.exit_flag=True
            return

        for idx, date in enumerate(forecast_dates):
            self.result_data.append({'forecast_date': date, 'weather':weathers[idx], 'temp':temperatures[idx], 'precip' : precipitations[idx]})

        # self.file_write()
        json_print(self.result_data)

    def long_term_query(self):
        if self.real_query is None:
            json_print('real query is not set. please check region name with district')
            self.exit_flag=True
            return
        self.real_query += 'long.html'

        #Second query
        try:
            res = requests.get(self.real_query)
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            json_print('Norway weather request failed at second query : ')
            self.exit_flag=True
            return


        self.result_data = []
        weathers = []
        forecast_dates = []
        temperatures = []
        precipitations = []

        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            #yr-table yr-table-overview2 yr-popup-area
            result_table = soup.find('table', {'class' : 'yr-table yr-table-longterm yr-popup-area'})
            weather_cells = result_table.select('tbody > tr')[0].find_all('td')
            temp_cells = result_table.select('tbody > tr')[1].find_all('td')
            precip_cells = result_table.select('tbody > tr')[2].find_all('td')
            date_cells = result_table.select('thead > tr')[0].find_all('th')


            for wcell , tcell, pcell, dcell in zip(weather_cells, temp_cells, precip_cells, date_cells):
                weathers.append(wcell['title'])
                temperatures.append(tcell.text)
                precipitations.append(pcell.text)
                forecast_dates.append(dcell.text)
        except Exception as err:
            json_print("Error occured while parsing long_term query in norway weahter")    
            self.exit_flag=True
            return
            
        for idx, date in enumerate(forecast_dates):
            self.result_data.append({'forecast_date' : date, 'weather' : weathers[idx], 'temp':temperatures[idx], 'precip' : precipitations[idx]})
        
        # self.file_write()
        # print(json.dumps(self.result_data, indent=4, ensure_ascii=False))
        json_print(self.result_data)
