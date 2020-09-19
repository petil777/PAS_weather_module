import requests
import numpy as np
import json
import os
import argparse
import asyncio

from koenchanger import KoEnSoundChanger
from MeteorologicalAgency.accuweather import AccuWeatherAgency
from MeteorologicalAgency.koreaweather import KoreaAgency
from MeteorologicalAgency.norwayweather import YrAgency
from MeteorologicalAgency.darkskyweather import DarkSkyAgency

async def havingparam(pp):
    await asyncio.sleep(1)
    print('this is : ', pp)

if __name__ == '__main__':  
    parser = argparse.ArgumentParser()
    parser.add_argument('--not-use', action='append')
    parser.add_argument('--region', required=True)
    args = parser.parse_args()
    
    if args.not_use is None: args.not_use = []

    loop = asyncio.get_event_loop()
    if 'acc' not in args.not_use:
        # pass
        acc = AccuWeatherAgency(file_dir='./weatherData/')
        loop.run_until_complete(acc.process_all(args.region))
    if 'yr' not in args.not_use:
        # pass
        yr = YrAgency('./weatherData/')
        # yr.process_all(args.region)
        loop.run_until_complete(yr.process_all(args.region))
    if 'dk' not in args.not_use:
        dk = DarkSkyAgency()
        loop.run_until_complete(dk.process_all(args.region))
    loop.close()
    # kr = KoreaAgency()
    # kr.get_query()

    
