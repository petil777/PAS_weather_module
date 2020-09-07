import requests
import numpy as np
import json
import os
import argparse

from koenchanger import KoEnSoundChanger
from MeteorologicalAgency.accuweather import AccuWeatherAgency
from MeteorologicalAgency.koreaweather import KoreaAgency
from MeteorologicalAgency.norwayweather import YrAgency



if __name__ == '__main__':  
    parser = argparse.ArgumentParser()
    parser.add_argument('--not-use', action='append')
    parser.add_argument('--region', required=True)
    args = parser.parse_args()
    
    if args.not_use is None: args.not_use = []

    if 'yr' not in args.not_use:
        pass
        # yr = YrAgency('./weatherData/')
        # yr.process_all(args.region)
    if 'acc' not in args.not_use:
        acc = AccuWeatherAgency(file_dir='./weatherData/')
        acc.process_all(args.region)

    # kr = KoreaAgency()
    # kr.get_query()

    
