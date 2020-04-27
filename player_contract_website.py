import re
import json
import sys
import os
import requests
import sqlite3
from bs4 import BeautifulSoup
import random
import csv
import pytrends
from pytrends.request import TrendReq
import  matplotlib
import matplotlib.pyplot as plt

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
        summ = 0
        count = 0
        salary = tr.findAll('td', class_ = "right")
        if len(salary) != 0:
            for item in salary[:6]:
                if len(item) > 0:
                    integer_num = item.text.replace("$", "").replace(",", "")
                else:
                    integer_num = 0
                summ += int(integer_num)
                if int(integer_num) > 0:
                    count += 1
            guaranteed_money = summ
            avg_salary = summ/count
            contract_list.append((avg_salary, guaranteed_money))
    
    return contract_list[:100]

def player_name_and_contract():
    i = 0
    player_lst = get_player_list()
    contract_lst = get_player_contract()
    lst_of_tups = []
    while i < 100:
        tup = (player_lst[i], contract_lst[i][0], contract_lst[i][1])
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
    dir_path = os.path.dirname(os.path.realpath(__file__))
    conn = sqlite3.connect(dir_path + "/main_database.db")
    cur = conn.cursor()
    
    relevant_data = cur.execute('SELECT * FROM PlayerSalary')
    player_lst = []
    for item in relevant_data:
        player_lst.append(item[0])
    count = 0
    data = player_name_and_contract()
    word = 'INSERT OR IGNORE INTO PlayerSalary (player_name, salary, guaranteed_money) VALUES (?, ?, ?)'
    for player in data:
        if count == 20:
            break
        if player[0] in player_lst:
            continue
        else:
            cur.execute(word, (player[0], player[1], player[2]))
            count += 1
    
    conn.commit()
    conn.close()

def fill_ppg_database():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    conn = sqlite3.connect(dir_path + "/main_database.db")
    cur = conn.cursor()

    relevant_data = cur.execute('SELECT * FROM PlayerPPG')
    player_lst = []
    subcount = 0
    for item in relevant_data:
        subcount += 1
        player_lst.append(item[0])

    count = 0
    holder = subcount
    data = player_ppg(holder, holder + 20)
    word = 'INSERT OR IGNORE INTO PlayerPPG (player_name, ppg) VALUES (?, ?)'
    for player in data:
        if count == 20:
            break
        if player[0] in player_lst:
            continue
        else:
            cur.execute(word, (player[0], player[1]))
            count += 1

    conn.commit()
    conn.close()

def fill_google_mentions_database():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    conn = sqlite3.connect(dir_path + "/main_database.db")
    cur = conn.cursor()
    
    relevant_data = cur.execute('SELECT * FROM PlayerMentions')
    player_lst = []
    for item in relevant_data:
        player_lst.append(item[0])
    count = 0
    data = player_trends(get_player_list())
    word = 'INSERT OR IGNORE INTO PlayerMentions (player_name, mentions) VALUES (?, ?)'
    for player in data:
        if count == 20:
            break
        if player[0] in player_lst:
            continue
        else:
            cur.execute(word, (player[0], player[1]))
            count += 1
        
    conn.commit()
    conn.close()

def reset_databases():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    conn = sqlite3.connect(dir_path + "/main_database.db")
    cur = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS PlayerSalary')
    cur.execute('CREATE TABLE IF NOT EXISTS PlayerSalary (player_name TEXT PRIMARY KEY, salary INTEGER, guaranteed_money INTEGER)')\

    cur.execute('DROP TABLE IF EXISTS PlayerPPG')
    cur.execute('CREATE TABLE IF NOT EXISTS PlayerPPG (player_name TEXT, ppg INTEGER)')

    cur.execute('DROP TABLE IF EXISTS PlayerMentions')
    cur.execute('CREATE TABLE IF NOT EXISTS PlayerMentions (player_name TEXT PRIMARY KEY, mentions INTEGER)')

    conn.commit()
    conn.close()

def write_calculations():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    conn = sqlite3.connect(dir_path + "/main_database.db")
    cur = conn.cursor()
    avg = cur.execute("SELECT AVG(salary) FROM PlayerSalary")
    avgsal = list(avg)[0][0]
    avg = cur.execute("SELECT AVG(mentions) FROM PlayerMentions")
    avgmentions = list(avg)[0][0]
    avg = cur.execute("SELECT AVG(ppg) FROM PlayerPPG")
    avgppg = list(avg)[0][0]


    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(dir_path + "/calc_file.csv", "w") as calc_file:
        calcwriter = csv.writer(calc_file)
        calcwriter.writerow(["Source", "Value"])
        calcwriter.writerow(["Average Salary", avgsal])
        calcwriter.writerow(["Average Mentions", avgmentions])
        calcwriter.writerow(["Average PPG", avgppg])

def visualize():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    conn = sqlite3.connect(dir_path + "/main_database.db")
    cur = conn.cursor()
    #salary
    salarylst0 = list(cur.execute("SELECT salary FROM PlayerSalary"))
    salarylst = []
    for i in salarylst0:
        salarylst.append(i[0])
    #ppg
    ppglst0 = list(cur.execute("SELECT ppg FROM PlayerPPG"))
    ppglst = []
    for i in ppglst0:
        ppglst.append(i[0])
    #mentions
    mentionslst0 = list(cur.execute("SELECT mentions FROM PlayerMentions"))
    mentionslst = []
    for i in mentionslst0:
        mentionslst.append(i[0])
    #PPGvsSALARY
    plt.scatter(ppglst, salarylst, s=30, c="orange")
    plt.title("Points per Game vs Salary among Top 100 Salaried NBA Players")
    plt.xlabel("NBA Points per Game")
    plt.ylabel("NBA Salary (in tens of millions of dollars)")
    plt.show()
    #PPGvsMENTIONS
    plt.scatter(ppglst, mentionslst, s=30, c="orange")
    plt.title("Points per Game vs Google Trends Mentions among Top 100 Salaried NBA Players")
    plt.xlabel("NBA Points per Game")
    plt.ylabel("Google Trends Mentions")
    plt.show()
    #PPG-HIST
    plt.hist(ppglst, color="orange")
    plt.title("Histogram of Average Points per Game among Top 100 Salaried NBA Players")
    plt.xlabel("NBA Points per Game")
    plt.ylabel("Frequency")
    plt.show()
    #SALARY-BXPLT
    plt.boxplot(salarylst)
    plt.title("Boxplot of Salaries of Top 100 Salaried NBA Players")
    plt.ylabel("NBA Salary (in tens of millions of dollars)")
    plt.xlabel("Top 100 Salaried Players in NBA")
    plt.grid()
    plt.show()
    #MENTIONS-BXPLT
    plt.boxplot(mentionslst)
    plt.title("Boxplot of Google Trends Mentions of Top 100 Salaried NBA Players")
    plt.ylabel("Google Trends Mentions")
    plt.xlabel("Top 100 Salaried Players in NBA")
    plt.grid()
    plt.show()


#reset_databases()
#fill_ppg_database()
#fill_salary_database()
#fill_google_mentions_database()
#write_calculations()
#visualize()