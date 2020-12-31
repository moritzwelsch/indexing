import sys
import json
import time
import binance
import datetime
from binance.client import Client

html_file = '/var/www/html/index.html'

# API Settings
api_key = 'WdoRwblecwrql65DBuBAbPD05PKq0hYNQqREBJsI9j44FYzjTdBIjPrbCNEMP5bK'
api_secret = '6JmhkmSQVD2DJlb54KBjMjNtz9AwU9DJ7Rjav2IvHYyMzWMNce5L0fxYnwsZpe7G'
api = Client(api_key, api_secret)

result = api.futures_account_balance()
print(result)
if result:
	print(result[0]['asset'], result[0]['balance'])
	now = datetime.datetime.now()

	with open(html_file, 'w+') as f:
		f.write("<h1>Asset: " + str(result[0]['asset']) + " Balance: " + str(result[0]['balance']) + "Aktualisiert: " + str(now) + "</h1>")

sys.exit()
