from bs4 import BeautifulSoup
import requests
import re
import json
import sys
import os
import sqlite3

def player_ppg():
    url = "https://www.balldontlie.io/api/v1/players"
    r = requests.get(url)
    return r.json()

player_ppg()