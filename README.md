### Weather Forecast crawler

- Crawl target site
  - https://www.yr.no/?spr=eng
  - https://www.accuweather.com/
  - https://www.weather.go.kr/w


### Current mechanism

- File store method. Have to change using DB.
- Temporarily, accuweather cralwer check files cache
- koEnChanger (based sound) used to convert korean sound to english
- Region names are stored without district name (Ex. 서울시 -> 서울  , 분당구 -> 분당)

### TODO
- new_event_loop with asyncio for multithreading when collecting data from meteorlogical agency
- korea weather agency is incomplete. 
