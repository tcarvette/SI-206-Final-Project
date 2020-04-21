from pytrends.request import TrendReq
import pytrends
import sqlite3

pytrends = TrendReq(hl="en-US", tz=360)

kw_list = ["kevin durant", "james harden", "lebron james", "justise winslow", "cody zeller"]
# ^ only 5 names at a time, will add 5 at a time to sql
pytrends.build_payload(kw_list, cat=1077, timeframe='today 5-y', geo='', gprop='')
a = pytrends.interest_over_time()
for i in kw_list:
    print(i + ": " + str(a[i].mean()))