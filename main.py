import requests
import numpy as np
import json
import os
from koenchanger import KoEnSoundChanger

from MeteorologicalAgency.accuweather import AccuWeatherAgency
from MeteorologicalAgency.koreaweather import KoreaAgency
from MeteorologicalAgency.norwayweather import YrAgency

if __name__ == '__main__':  
    yr = YrAgency('./weatherData/')
    yr.process_all('분당')

    # kr = KoreaAgency()
    # kr.get_query()

    # acc = AccuWeatherAgency(file_dir='./weatherData/', must_query=False, hours_min=3)
    # acc.process_all('분당')
    
