import re
import json
import sys
import requests
import sqlite3
from bs4 import BeautifulSoup
import random
import pytrends
from pytrends.request import TrendReq

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

def get_player_contract():
    base_url = "https://www.basketball-reference.com/contracts/players.html"
    r = requests.get(base_url)
    soup = BeautifulSoup(r.text, "lxml")

    contract_list = []
    main = soup.findAll('tr')
    for tr in main:
        sum = 0
        count = 0
        salary = tr.findAll('td', class_ = "right")
        if len(salary) != 0:
            for item in salary[:6]:
                if len(item) > 0:
                    integer_num = item.text.replace("$", "").replace(",", "")
                else:
                    integer_num = 0
                sum += int(integer_num)
                if int(integer_num) > 0:
                    count += 1
            avg_salary = sum/count
            contract_list.append(avg_salary)
    
    return contract_list[:100]

def player_name_and_contract():
    i = 0
    player_lst = get_player_list()
    contract_lst = get_player_contract()
    lst_of_tups = []
    while i < 100:
        tup = (player_lst[i], contract_lst[i])
        lst_of_tups.append(tup)
        i += 1
    return lst_of_tups

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

def player_ppg(start_num, end_num):
    player_lst = get_player_list()
    ppg_lst = []

    for player in player_lst[start_num:end_num]:
        query = player.replace("č", "c").replace("ć", "c").replace("ū", "u").replace("ö", "o").replace("ņ", "n").replace("ģ", "g").replace(".", "")
        url = "https://www.balldontlie.io/api/v1/players?search=" + query
        r = requests.get(url)
        
        data_content = r.json()
        player_id = data_content["data"][-1]["id"]
        
        new_url = "https://www.balldontlie.io/api/v1/season_averages?player_ids[]=" + str(player_id)
        r_r = requests.get(new_url)
        
        player_stats = r_r.json()
        if len(player_stats["data"]) != 0:
            player_ppg = player_stats["data"][0]["pts"]
        else:
            url_2018 = "https://www.balldontlie.io/api/v1/season_averages?season=2018&player_ids[]=" + str(player_id)
            r_r_r = requests.get(url_2018)

            player_stats = r_r_r.json()
            player_ppg = player_stats["data"][0]["pts"]

        tup = (player, player_ppg)
        ppg_lst.append(tup)

    return ppg_lst

def fill_salary_database():
    conn = sqlite3.connect('/Users/tylercarvette/Desktop/salary.db')
    cur = conn.cursor()


    cur.execute('DROP TABLE IF EXISTS PlayerSalary')
    cur.execute('CREATE TABLE IF NOT EXISTS PlayerSalary (player_name TEXT, salary INTEGER)')

  
    word = 'INSERT INTO PlayerSalary (player_name, salary) VALUES (?, ?)'
    cur.executemany(word, player_name_and_contract())

    
    conn.commit()

def fill_ppg_database():
    conn = sqlite3.connect('/Users/tylercarvette/Desktop/ppg.db')
    cur = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS PlayerPPG')
    cur.execute('CREATE TABLE IF NOT EXISTS PlayerPPG (player_name TEXT, ppg INTEGER)')
    x = 0
    y = 1
    for i in range(100):
        word = 'INSERT INTO PlayerPPG (player_name, ppg) VALUES (?, ?)'
        cur.executemany(word, player_ppg(x, y))
        x += 1
        y += 1

        conn.commit()

def fill_google_mentions_database():
    conn = sqlite3.connect('/Users/tylercarvette/Desktop/google_mentions.db')
    cur = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS PlayerMentions')
    cur.execute('CREATE TABLE IF NOT EXISTS PlayerMentions (player_name TEXT, mentions INTEGER)')
    
    word = 'INSERT INTO PlayerMentions (player_name, mentions) VALUES (?, ?)'
    cur.executemany(word, player_trends(get_player_list()))
        
    conn.commit()

#print(player_name_and_contract())
#print(player_trends(get_player_list))
#print(player_ppg(0, 20))
#fill_salary_database()
#fill_ppg_database()
#fill_google_mentions_database()