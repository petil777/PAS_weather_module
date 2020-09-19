import requests
from bs4 import BeautifulSoup
import json
from myutil import json_print

headers = {
    'Cookie': '_ga=GA1.3.1718141664.1599360317; _gid=GA1.3.471759635.1599360317; ASP.NET_SessionId=2avcjbsosnorw1wvplxxxg0u; _gat=1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'Connection': 'keep-alive'
}
# http://roman.cs.pusan.ac.kr/
class KoEnSoundChanger():
    def __init__(self):
        pass

    @staticmethod
    def _isEnglish(word):
        try:
            word.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True

    def ko_to_en_sound(self, word):
        if word == '' : return ''
        if KoEnSoundChanger._isEnglish(word): return word
        try:
            res = requests.get('http://roman.cs.pusan.ac.kr/result_all.aspx', headers=headers, params={'input':word})
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            json_print("Ko En chagne request server error")
            # print('ko en change request error : ', err)
            exit(0)
            
        soup = BeautifulSoup(res.text, 'html.parser')
        targets = soup.find_all('span', {'id': 'outputRMGoyu'})
        if len(targets) > 0:
            return str.lower(targets[0].text)
        return None