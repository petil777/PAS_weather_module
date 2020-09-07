import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from koenchanger import KoEnSoundChanger

# https://www.yr.no/?spr=eng

class YrAgency():
    def __init__(self, file_dir, long_term=False):
        self.file_dir = file_dir
        self.long_term = long_term
        self.target_file_name = None
        #Usually except district name.
        self.region_name = None
        self.real_query = None
        self.result_data =None
        self.koen_sound_converter = KoEnSoundChanger()
    def process_all(self, region):
        region = str.lower(region).strip()
        self.get_query(region)
        if self.long_term:
            self.long_term_query()
        #Default
        else:
            self.daily_query()

    def file_write(self):
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.target_file_name = self.file_dir + 'yrweather_' + str(dt) + '_' + str(self.region_name)
        with open(self.target_file_name, 'w') as fi:
            # To allow special character for temparature, ensure_ascii=false
            fi.write(json.dumps(self.result_data, indent=4, ensure_ascii=False))  

    # region = bundang  gu(district)  (already english parsed)
    def get_query(self, region):
        district = ''
        if len(region) < 1: 
            print('region name not valid')
            exit(0)
        if region[-1] in  ['도' , '시' , '구' , '군']:
            district = region[-1]
            region = region[0:-1]

        self.region_name = region
        region_ensound = self.koen_sound_converter.ko_to_en_sound(self.region_name)
        district_ensound = self.koen_sound_converter.ko_to_en_sound(district)
        if region_ensound == None:
            print('No proper changed en sound')
            exit(0)

        query_url = 'https://www.yr.no/soek/soek.aspx?sted=' + region_ensound
        
        #First query for searching region 
        try:
            res = requests.get(query_url, params={'spr' : 'eng'})
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            print('Norway weather request failed : ', err)
            exit(0)

        soup = BeautifulSoup(res.text, 'html.parser')
        result_table = soup.find('table', {'class' : 'yr-table yr-table-search-results'})
        trs = result_table.find_all('tr')
        for idx, tr in enumerate(trs):
            if idx ==0 : continue # table header
            # <a href="/sted/Sør-Korea/Gyeonggi/Bundang-dong/" title="Bundang-dong">Bundang-dong</a>
            # change eng suppor url "https://www.yr.no/place/South_Korea/Gyeonggi/Bundang-gu/"
            region_title = tr.find('a')['title']
            web_api = tr.find('a')['href']
            #bundang-  bundang-gu  seoul
            # /place/South_Korea/Seoul/Seoul/ vs /place/South_Korea/Seoul/  .. have to select former!
            if str.lower(region_title).startswith(region_ensound): 
                self.real_query = 'https://www.yr.no'+ '/place/South_Korea/' + '/'.join(web_api.split('/')[3:])
                #Perfect match
                if str.lower(region_title) == region_ensound+'-' + district_ensound \
                    or (district_ensound=='' and str.lower(region_title) == region_ensound):
                    break
            
    def daily_query(self):
        if self.real_query is None:
            print('real query is not set. please check region name with district')
            return
        #Second query
        try:
            res = requests.get(self.real_query)
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            print('Norway weather request failed at second query : ', err)
            exit(0)

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

        for idx, date in enumerate(forecast_dates):
            self.result_data.append({'forecast_date': date, 'weather':weathers[idx], 'temp':temperatures[idx], 'precip' : precipitations[idx]})

        # self.file_write()
        print(json.dumps(self.result_data, indent=4, ensure_ascii=False))

    def long_term_query(self):
        if self.real_query is None:
            print('real query is not set. please check region name with district')
            return
        self.real_query += 'long.html'

        #Second query
        try:
            res = requests.get(self.real_query)
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            print('Norway weather request failed at second query : ', err)
            exit(0)


        self.result_data = []
        weathers = []
        forecast_dates = []
        temperatures = []
        precipitations = []

        soup = BeautifulSoup(res.text, 'html.parser')
        #yr-table yr-table-overview2 yr-popup-area
        result_table = soup.find('table', {'class' : 'yr-table yr-table-longterm yr-popup-area'})
        weather_cells = result_table.select('tbody > tr')[0].find_all('td')
        temp_cells = result_table.select('tbody > tr')[1].find_all('td')
        precip_cells = result_table.select('tbody > tr')[2].find_all('td')

        for wcell , tcell, pcell in zip(weather_cells, temp_cells, precip_cells):
            weathers.append(wcell['title'])
            temperatures.append(tcell.text)
            precipitations.append(pcell.text)

        result_table = soup.find('table', {'class' : 'yr-table yr-table-longterm-detailed yr-popup-area lp_longterm_detailed'})
        cells = result_table.select('th[scope=rowgroup]')
        for cell in cells:
            cell = cell.text.strip().split('/')
            date = cell[-1] + '/' + cell[-2] + '/' + cell[-3].split(' ')[-1]
            forecast_dates.append(date)

        for idx, date in enumerate(forecast_dates):
            self.result_data.append({'forecast_date' : date, 'weather' : weathers[idx], 'temp':temperatures[idx], 'precip' : precipitations[idx]})
        
        # self.file_write()
        # print(json.dumps(self.result_data, indent=4, ensure_ascii=False))
        print(json.dumps(self.result_data, ensure_ascii=False))
