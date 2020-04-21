import re
import json
import sys
import requests
import sqlite3
from bs4 import BeautifulSoup
import random
from pytrends.request import TrendReq
import pytrends

def get_player_list():
    count = 0
    base_url = "https://www.basketball-reference.com/contracts/players.html"
    r = requests.get(base_url)
    soup = BeautifulSoup(r.text, "lxml")

    player_list = []
    main = soup.findAll('tbody')
    for tr in main:
        names = tr.findAll('a')
        for a in names:
            if count % 2 == 0:
                player_list.append(a.text)
            count += 1

    return player_list[:100]

def player_trends(list_of_players):
    pytrends = TrendReq(hl="en-US", tz=360)
    mean_list = []
    list_player_list = []
    play_list = get_player_list()
    for i in range(0,100,5):
        x=i
        list_player_list.append(play_list[x:x+5])
    for i in list_player_list:
        kw_list = i
        pytrends.build_payload(kw_list, cat=1077, timeframe='today 5-y', geo='', gprop='')
        a = pytrends.interest_over_time()
        for i in kw_list:
            mean_list.append(a[i].mean())
    tup_list = zip(play_list, mean_list)
    return list(tup_list)

print(player_trends(get_player_list))



print(get_player_list())