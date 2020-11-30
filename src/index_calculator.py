import sys
import json
import ccxt
import requests
import threading
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup


class Index:
	def __init__(self):
		self.index = '.BXBT'
		self.index_weighting_url = 'https://www.bitmex.com/app/indices'
		self.weighting = ''
		self.prices = {}
		self.index_value = 0

	def get_weighting(self):
		html = urllib.request.urlopen(self.index_weighting_url).read()
		soup = BeautifulSoup(html, 'html.parser')

		table = soup.find("table", {"class": "table-striped"})
		for td in table.findAll('td'):
			td.string = td.string.replace('%', '')
			td.string = td.string.replace('-', '0')
		self.weighting = pd.read_html(table.prettify(), index_col=0)[0]
		for col in self.weighting.columns:
			self.weighting[col] = self.weighting[col].div(100).round(4)
		self.weighting = self.weighting.loc[self.index]

		pd.to_numeric(self.weighting)
		return

	def get_index_value(self):
		threads = []
		for head in self.weighting.index:
			t = threading.Thread(target=self.get_price, args=(head,))
			t.start()
			threads.append(t)

		for t in threads:
			t.join()
		self.prices = pd.to_numeric(pd.Series(self.prices))
		self.index_value = 0
		for index in self.weighting.index:
			# print(index, self.weighting[index], self.prices[index])
			self.index_value += self.prices[index] * self.weighting[index]

	def get_price(self, head):
		if head == 'Binance US':
			response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
			price = json.loads(response.text)['price']
			# print("Binance US Price:", price)

		elif head == 'Bitstamp':
			response = requests.get('https://www.bitstamp.net/api/ticker/')
			price = json.loads(response.text)['last']
			# print("Bitstamp Price:", price)

		elif head == 'Bittrex':
			response = requests.get('https://api.bittrex.com/api/v1.1/public/getticker?market=USD-BTC')
			price = json.loads(response.text)['result']['Last']
			# print("Bittrex Price:", price)

		elif head == 'Coinbase':
			response = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot')
			price = json.loads(response.text)['data']['amount']
			# print("Coinbase Price:", price)

		elif head == 'Gemini':
			response = requests.get('https://api.gemini.com/v1/pubticker/btcusd')
			price = json.loads(response.text)['last']
			# print("Gemini Price:", price)

		elif head == 'Kraken':
			response = requests.get('https://api.kraken.com/0/public/Ticker?pair=BTCUSD')
			price = \
			[json.loads(response.text)['result'][pair]['c'] for pair in json.loads(response.text)['result']][0][0]
			# print("Kraken Price:", price)

		self.prices[head] = price
