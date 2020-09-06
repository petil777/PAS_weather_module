import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from koenchanger import KoEnSoundChanger

# https://www.yr.no/?spr=eng

class YrAgency():
    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.target_file_name = None
        #Usually except district name.
        self.region_name = None
        self.real_query = None
        self.result_data =None
        self.koen_sound_converter = KoEnSoundChanger()
    def process_all(self, region):
        region = str.lower(region).strip()

        self.get_query(region)
        self.final_query()

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
        if region_ensound == None:
            print('No proper changed en sound')
            exit(0)
        

        query_url = 'https://www.yr.no/soek/soek.aspx?sted=' + region_ensound
        
        #First query for searching region 
        try:
            res = requests.get(query_url)
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
            region_title = tr.find('a')['title']
            web_api = tr.find('a')['href']
            #bundang-  bundang-gu
            if str.lower(region_title).startswith(region+'-' + district): 
                self.real_query = 'https://www.yr.no'+ web_api
    
    def final_query(self):
        self.real_query="https://www.yr.no/place/South_Korea/Gyeonggi/Bundang-gu/"
        if self.real_query is None:
            print('real query is not set. please check region name with district')
            return

        #Second query
        try:
            res = requests.get(self.real_query)
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            print('Norway weather reqeust failed at second query : ', err)
            exit(0)

        soup = BeautifulSoup(res.text, 'html.parser')
        #yr-table yr-table-overview2 yr-popup-area
        results = soup.find_all('table', {'class' : 'yr-table yr-table-overview2 yr-popup-area'})

        
        self.result_data = []

        ii =0 
        for result in results:
            ii+=1
            # Tomorrow, Monday 07/09/2020
            date = result.find('caption').text.strip()
            # winds = result.find_all('td', {'class' : 'txt-left'})    
            trs = result.find_all('tr')
            forecasts = []

            split_date = date.split('/')
            forecast_date = split_date[2]+'/'+split_date[1]+'/'+split_date[0].split(' ')[-1]
            phrases = []
            for idx, tr in enumerate(trs):
                if idx ==0 : continue # table header
                trlist = tr.find_all('td')[1]
                phrases.append(trlist['title'])
            

            self.result_data.append({
                'forecast_date':forecast_date,
                'phrase' : phrases
            })
        
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.target_file_name = self.file_dir + 'yrweather_' + str(dt) + '_' + str(self.region_name)
        with open(self.target_file_name, 'w') as fi:
            # To allow special character for temparature, ensure_ascii=false
            fi.write(json.dumps(self.result_data, indent=4, ensure_ascii=False))    