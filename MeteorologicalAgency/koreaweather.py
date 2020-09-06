import requests

headers ={
    'Connection': 'keep-alive',
    'Cookie': '_TRK_CR=https%3A%2F%2Fwww.google.com%2F; _TRK_UID=5640ba058088c6da931cbc696ff705a9:2; _TRK_SID=6700f05086348411eb620fca0a5f6bf0; localNumbers=; _LSL=1168066000; LDF=1168066000; _TRK_EX=27; JSESSIONID=5amS2VByPQwqwVHivms5nAGDu1tcofajqYDBZ1M9d8rmYQvHVVU4A0kaswFaFzOM.d2VhdGhlci13YXMwLTA1L3NlcnZlcjE=',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    
}
class KoreaAgency():
    def __init__(self):
        pass
    def get_query(self):
        #wideCode : 경기도/ 서울시  등 도나 특별시 단위
        #cityCode : 시 -> 구 |  도 -> 시/구  코드
        query_url = 'https://www.weather.go.kr/w/rest/zone/dong.do?type=WIDE&wideCode=&cityCode=&keyword=&keywordStart=&keywordEnd='

        #wideCode와 cityCode를 바탕으로 마지막으로 '동' 을 고르면 최종 코드 나옴
        final_url = 'https://www.weather.go.kr/w/wnuri-fct/weather/today-vshortmid.do?code=4113565700&unit=km%2Fh'
        res = requests.get('https://www.weather.go.kr/weather/forecast/timeseries.jsp', headers=headers,
                params={'_':1599368042768})