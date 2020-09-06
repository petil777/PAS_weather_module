import requests
from bs4 import BeautifulSoup
import json

headers = {
    'Cookie': '_ga=GA1.3.1718141664.1599360317; _gid=GA1.3.471759635.1599360317; ASP.NET_SessionId=2avcjbsosnorw1wvplxxxg0u; _gat=1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'Connection': 'keep-alive'
}
# http://roman.cs.pusan.ac.kr/
class KoEnSoundChanger():
    def __init__(self):
        pass

    def ko_to_en_sound(self, word):
        try:
            res = requests.get('http://roman.cs.pusan.ac.kr/result_all.aspx', headers=headers, params={'input':word})
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            print('ko en change request error : ', err)
            exit(0)
        soup = BeautifulSoup(res.text, 'html.parser')
        targets = soup.find_all('span', {'id': 'outputRMGoyu'})
        if len(targets) > 0:
            return targets[0].text
        return None