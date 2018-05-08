"""
LOCATION OF THE PYTHON-BINANCE GITHUB:
https://github.com/sammchardy/python-binance

LOCATION OF PYTHON-BINANCE DOCUMENTATION
https://python-binance.readthedocs.io/en/latest/
"""

from binance.client import Client
import time
import math
from threading import Timer

# ADD API KEYS
client = Client('XXXXXXXXXXXXX', 'XXXXXXXXXXXXX')

# OPENING TICKER PAIR LIST
file = open("mt_no_vib.txt", "r")
ETHmarkets = []
BTCmarkets = []
gettingEthMarkets = True
ETHmarkets = file.readline().split(" ")
ETHmarkets[len(ETHmarkets) - 1] = ETHmarkets[len(ETHmarkets) - 1][:-1]
file.readline()
BTCmarkets = file.readline().split(" ")


# ACCOUNT GLOBALS
accountBalance = {}

# TICKER GLOBALS
#ETHmarkets = ["BNBETH", "LUNETH", "VENETH", "CNDETH", "GVTETH"]
#BTCmarkets = ["BNBBTC", "LUNBTC", "VENBTC", "CNDBTC", "GVTBTC"]
fullTicker = ETHmarkets + BTCmarkets + ["ETHBNB"]		#***
minimums = {}
depths = {}
for n in fullTicker:
	depths[n] = 0

# FOR CONSISTENT USDT CONVERSION - NO MARKET MOVEMENT
#BTCtoUSDT = 0
USDTconversions = [0,0,0] #BTC, ETH, BNB
USDTtotal = 0
USDTstartingTotal = 0
balances = [0,0,0]


# EXECUTION GLOBALS
threshold = 1.01
tradeFee = 0.0005

# PERFORMANCE GLOBALS
profit = 0
numTradesFound = 0
numTradesUnderThreshold = 0
numTradesUnderVolume = 0
numTradesOverTime = 0
numOverAndEqualProfit = 0
numUnderProfit = 0


# OPENING FILE FOR WRITING DATA
fileDateAndTIme = time.strftime("%b-%d-%Y-%H-%M", time.localtime())
fileName = "data/arbitrage-" + fileDateAndTIme + ".txt"

# UPDATE ACCOUNT BALANCES
# FORMAT IS A BIT DIFFERENT THAN THE JAVASCRIPT VERSION - KEYS ARE CURRENCY, VALUES ARE DICTIONARIES OF LOCKED AND FREE QTY
# accountBalance = {COIN: {'locked': Z, 'free': Y}}
# I just didn't want to freak anyone out that our money is gone in case it ever gets locked some how in the future
# Needs USDTconversions
def updateBalance():
	balance = client.get_account()
	global accountBalance
	accountBalance = {}
	for n in balance['balances']:
		tot = float(n['free']) + float(n['locked'])
		if tot > 0:
			accountBalance[n['asset']] = {'free': float(n['free']), 'locked': float(n['locked'])}

	# Getting USDT values
	totalUSDT = 0
	for symbol in accountBalance:
		valInUSDT = 0
		if symbol == 'BTC':
			balances[0] = accountBalance[symbol]['free']
			valInUSDT = accountBalance[symbol]['free'] * USDTconversions[0]
		elif symbol == 'ETH':
			balances[1] = accountBalance[symbol]['free']
			valInUSDT = accountBalance[symbol]['free'] * USDTconversions[1]
		elif symbol == 'BNB':
			balances[2] = accountBalance[symbol]['free']
			valInUSDT = accountBalance[symbol]['free'] * USDTconversions[2]
		totalUSDT += valInUSDT

	global USDTtotal
	USDTtotal = totalUSDT


# Get the best bid and ask for the whole listing from Binance
# Pass a dictionary "currency_list" -> Extract the tickers we're interested in and update currency_list.
# NOTE: get_orderbook_ticker() returns a list of dictionaries. Each entry takes the form
# {'symbol': 'ETHBTC', 'bidQty': '0.06200000', 'askQty': '2.31700000', 'bidPrice': '0.10115400', 'askPrice': '0.10115800'}
# In our "depths" dictionary, each key is a ticker symbol and each value is the corresponding dictionary from get_order_book()
def getBidAsk(currency_list):
	order_book = client.get_orderbook_ticker()
	for n in order_book:
		#if n['symbol'] in currency_list:
		currency_list[n['symbol']] = n

# LIMIT STEP SIZE (FLOORING APPROACH) - MAKE THE TRADE VOLUME A MULTIPLE OF THE MINIMUM STEP SIZE
def limitStepSizeFloor(symbol, vol):
	factor = 1/minimums[symbol]['stepSize']
	return math.floor(factor * vol) / factor

# RETURN TRUE IF THE VOLUME BEING TRADED IS LARGER THAN THE MIN QTY FOR THE COIN
def checkMinQty(symbol, volume):
	return volume > minimums[symbol]['minQty']

# GET MINIMUM TRADE INFO FOR TICKERS
def getMinimums():
	data = client.get_exchange_info()
	for dic in data['symbols']:
		if dic['symbol'] in fullTicker:
			filters = {'minQty': 1, 'stepSize': 1}
			for filtr in dic['filters']:
				if filtr['filterType'] == "LOT_SIZE":
					filters['minQty'] = float(filtr['minQty'])
					filters['stepSize'] = float(filtr['stepSize'])
					break
			minimums[dic['symbol']] = filters

# PRINT OUT TRADE FINDINGS - ON A 10 MINUTE CYCLE
def printUpdate():
	Timer(300, printUpdate).start() # time in seconds
	updateBalance()
	print("\nUPDATE - {}".format(time.strftime("%b %d %Y %H:%M:%S", time.localtime()) ) )
	print("- - - - - - - - - - - - - -  - - -  - - -  - - -")
	print("Trades Found: {}".format(numTradesFound))
	print("All Trades Under Volume: {}".format(numTradesUnderVolume))
	print("Trades Found But Under Threshold: {}".format(numTradesUnderThreshold))
	
	print("\nCompleted Trades Equal/Over Profit: {}".format(numOverAndEqualProfit))
	print("Completed Trades Under Profit: {}".format(numUnderProfit))
	
	# Writing to file
	f = open(fileName,"a")
	f.write("\nUPDATE - {}\n".format(time.strftime("%b %d %Y %H:%M:%S", time.localtime()) ) )
	f.write("- - - - - - - - - - - - - -  - - -  - - -  - - -\n")
	f.write("Trades Found: {}\n".format(numTradesFound))
	f.write("All Trades Under Volume: {}\n".format(numTradesUnderVolume))
	f.write("Trades Found But Under Threshold: {}\n".format(numTradesUnderThreshold))
	
	f.write("\nCompleted Trades Equal/Over Profit: {}\n".format(numOverAndEqualProfit))
	f.write("Completed Trades Under Profit: {}\n".format(numUnderProfit))
	
	
	print("\nBalances")
	f.write("\nBalances\n")
	
	for symbol in accountBalance:
		print("{}: {}".format(symbol, accountBalance[symbol]['free']))
		f.write("{}: {}\n".format(symbol, accountBalance[symbol]['free']))
		
	print("\nValues in USDT")
	f.write("\nValues in USDT\n")
	print("BTC in USDT: {}".format(balances[0] * USDTconversions[0]))
	f.write("BTC in USDT: {}\n".format(balances[0] * USDTconversions[0]))
	print("ETH in USDT: {}".format(balances[1] * USDTconversions[1]))
	f.write("ETH in USDT: {}\n".format(balances[1] * USDTconversions[1]))
	print("BNB in USDT: {}".format(balances[2] * USDTconversions[2]))
	f.write("BNB in USDT: {}\n".format(balances[2] * USDTconversions[2]))

	print("\nStarting USDT: {}".format(USDTstartingTotal))
	print("Total USDT: {}".format(USDTtotal))
	print("Percentage of starting total USDT: {}%".format(USDTtotal / USDTstartingTotal * 100) )
	print("- - - - - - - - - - - - - -  - - -  - - -  - - -")
	
	# Writing to file
	f.write("\nStarting USDT: {}\n".format(USDTstartingTotal))
	f.write("Total USDT: {}\n".format(USDTtotal))
	f.write("Percentage of starting total USDT: {}%\n".format(USDTtotal / USDTstartingTotal * 100) )
	f.write("- - - - - - - - - - - - - -  - - -  - - -  - - -\n")

	f.close()

# EVALUATE PROFITABILITY OF TRADE
def evaluateTrade(COIN_ETH, COIN_BTC):
	# Forward Trade Direction: BTC -> COIN -> ETH -> BTC
	tradeInfo = {'percentage': 0}
	
	# Check that tickers are in our depth dictionary
	if COIN_ETH not in depths or COIN_BTC not in depths or 'ETHBTC' not in depths:
		return tradeInfo
	
	# And check that the dictionary is populated
	if depths[COIN_ETH] == 0 or depths[COIN_BTC] == 0 or depths['ETHBTC'] == 0:
		return tradeInfo

	# Get current info required for trade
	COIN_BTC_ask = float(depths[COIN_BTC]['askPrice'])
	COIN_BTC_ask_qty = float(depths[COIN_BTC]['askQty'])
	COIN_BTC_bid = float(depths[COIN_BTC]['bidPrice'])
	COIN_BTC_bid_qty = float(depths[COIN_BTC]['bidQty'])

	COIN_ETH_ask = float(depths[COIN_ETH]['askPrice'])
	COIN_ETH_ask_qty = float(depths[COIN_ETH]['askQty'])
	COIN_ETH_bid = float(depths[COIN_ETH]['bidPrice'])
	COIN_ETH_bid_qty = float(depths[COIN_ETH]['bidQty'])

	ETH_BTC_ask = float(depths['ETHBTC']['askPrice'])
	ETH_BTC_ask_qty = float(depths['ETHBTC']['askQty'])
	ETH_BTC_bid = float(depths['ETHBTC']['bidPrice'])
	ETH_BTC_bid_qty = float(depths['ETHBTC']['bidQty'])

	# Calculate Trade Direction
	forwardPercentage = (1 - tradeFee) / COIN_BTC_ask * (1 - tradeFee) * COIN_ETH_bid * (1 - tradeFee) * ETH_BTC_bid
	backwardPercentage = (1 - tradeFee) / ETH_BTC_ask * (1 - tradeFee) / COIN_ETH_ask * (1 - tradeFee) * COIN_BTC_bid

	# CALCULATE COIN VOLUME
	safetyThreshold = 0.99 #Reducing by a slight amount to avoid losing max size trades in wildly changing markets

	if forwardPercentage > backwardPercentage:
		percentage = forwardPercentage
		COINvolume = min(ETH_BTC_bid_qty / COIN_ETH_ask, COIN_BTC_ask_qty, COIN_ETH_bid_qty)
		forward = True
	else:
		percentage = backwardPercentage
		COINvolume = min(ETH_BTC_ask_qty / COIN_ETH_ask, COIN_ETH_ask_qty, COIN_BTC_bid_qty)
		forward = False

	# LIMIT COIN VOLUME TO OUR AVAILABLE BALANCE (NOTE: The '\' char is Python's line continuation)
	# Don't need to min it with "accountBalance[COIN]['free'] * safetyThreshold" if we're not doing simultaneous
	COINvolume = min(COINvolume, accountBalance['BTC']['free'] * safetyThreshold / COIN_BTC_ask)


	COINvolume = limitStepSizeFloor(COIN_BTC, COINvolume)
	COINvolume = limitStepSizeFloor(COIN_ETH, COINvolume)
	ETHvolume = COINvolume * COIN_ETH_ask
	ETHvolume = limitStepSizeFloor('ETHBTC', ETHvolume)


	COINvolume = ETHvolume / COIN_ETH_ask
	COINvolume = limitStepSizeFloor(COIN_BTC, COINvolume)
	COINvolume = limitStepSizeFloor(COIN_ETH, COINvolume)
	

	tradeInfo = {'COIN_ETH': COIN_ETH,
		 'COIN_BTC': COIN_BTC,
		 'percentage': percentage,
		 'ETHvolume': ETHvolume,
		 'COINvolume': COINvolume,
		 'forwardTradePath': forward,
		 'ask_prices': [COIN_BTC_ask, COIN_ETH_ask, ETH_BTC_ask],
		 'bid_prices': [COIN_BTC_bid, COIN_ETH_bid, ETH_BTC_bid]}
	return tradeInfo


# END TRADING HELPER FUNCTION - ADD TO THIS AS NEEDED
def endTrading(tradeInfo, responses, times):
	global numOverAndEqualProfit
	global numUnderProfit
	actualTradePercentage = 0
	filledAvgPrices = []
	
	# Getting avg prices from the responses
	for response in responses:
		avgPrice = 0
		totalQty = 0
		for fill in response['fills']:
			avgPrice += float(fill['price']) * float(fill['qty'])
			totalQty += float(fill['qty'])
		avgPrice /= totalQty
		filledAvgPrices.append(avgPrice)
		
	# DOCUMENT THE TRADE
	print("\nTRADING - {}".format(time.strftime("%b %d %Y %H:%M:%S", time.localtime()) ) )
	print("- - - - - - - - - - - - - -  - - -  - - -  - - -")
	if tradeInfo['forwardTradePath']:
		print("BUYING: {} in {} sec \t Status: {} \t OrderID: {}".format(tradeInfo['COIN_BTC'], times[1] - times[0], responses[0]['status'], responses[0]['orderId']))
		#print("Response: {}".format(responses[0]))
		print("SELLING: {} in {} sec \t Status: {} \t OrderID: {}".format(tradeInfo['COIN_ETH'], times[2] - times[1], responses[1]['status'], responses[1]['orderId']))
		#print("Response: {}".format(responses[1]))
		print("SELLING: ETHBTC in {} sec \t Status: {} \t OrderID: {}".format(times[3] - times[2], responses[2]['status'], responses[2]['orderId']))
		#print("Response: {}".format(responses[2]))
		print("Total forwards execution time: {}".format(times[3] - times[0]))
		print("- - - - - - - - - - - - - -  - - -  - - -  - - -")
		
		print("\nTrading BTC -> {} -> ETH -> BTC".format(tradeInfo['COIN_BTC'][:-3]))
		actualTradePercentage = (1 - tradeFee) / filledAvgPrices[0] * (1 - tradeFee) * filledAvgPrices[1] * (1 - tradeFee) * filledAvgPrices[2]
	else:
		print("BUYING: ETHBTC in {} sec \t Status: {} \t OrderID: {}".format(times[1] - times[0], responses[0]['status'], responses[0]['orderId']))
		#print("Response: {}".format(responses[0]))
		print("BUYING: {} in {} sec \t Status: {} \t OrderID: {}".format(tradeInfo['COIN_ETH'], times[2] - times[1], responses[1]['status'], responses[1]['orderId']))
		#print("Response: {}".format(responses[1]))
		print("SELLING: {} in {} sec \t Status: {} \t OrderID: {}".format(tradeInfo['COIN_BTC'], times[3] - times[2], responses[2]['status'], responses[2]['orderId']))
		#print("Response: {}".format(responses[2]))
		print("Total backwards execution time: {}".format(times[3] - times[0]))
		print("- - - - - - - - - - - - - -  - - -  - - -  - - -")
		
		print("\nTrading BTC -> ETH -> {} -> BTC".format(tradeInfo['COIN_BTC'][:-3]))
		actualTradePercentage = (1 - tradeFee) / filledAvgPrices[0] * (1 - tradeFee) / filledAvgPrices[1] * (1 - tradeFee) * filledAvgPrices[2]


	profitDiff = actualTradePercentage - tradeInfo['percentage']
	if profitDiff < 0:
		numUnderProfit += 1
	else:
		numOverAndEqualProfit +=1

	print("Expected profit %: {}".format(tradeInfo['percentage']))
	print("Actual profit %: {}".format(actualTradePercentage))
	print("Profit % difference: {}".format(profitDiff))
	print("Volumes: ETH: {} \t {}: {}".format(tradeInfo['ETHvolume'], tradeInfo['COIN_BTC'][:-3], tradeInfo['COINvolume']))

	# Writing balances
	updateBalance()
	print("\nBalances")

	for symbol in accountBalance:
		print("{}: {}".format(symbol, accountBalance[symbol]['free']))
		
	print("Values in USDT")
	print("BTC in USDT: {}".format(balances[0] * USDTconversions[0]))
	print("ETH in USDT: {}".format(balances[1] * USDTconversions[1]))
	print("BNB in USDT: {}".format(balances[2] * USDTconversions[2]))

	print("\nStarting USDT: {}".format(USDTstartingTotal))
	print("\nTotal USDT: {}".format(USDTtotal))
	print("Percentage of starting total USDT: {}%".format(USDTtotal / USDTstartingTotal * 100) )
	print("- - - - - - - - - - - - - -  - - -  - - -  - - -")

"""
 EXECUTE TRADE
 SYNTAX FOR EXECUTING A TEST ORDER:
 order = client.create_test_order(
     symbol='BNBBTC',
	  side=SIDE_BUY,
     type=ORDER_TYPE_MARKET,
     quantity=100,)
"""
def trade(tradeInfo):
	# FORWARDS DIRECTION
	responses = []
	times = []
	times.append(time.time())
	if tradeInfo['forwardTradePath']:
		times.append(time.time())
		response = client.order_market_buy(symbol=tradeInfo['COIN_BTC'], quantity=tradeInfo['COINvolume'], newOrderRespType='FULL')
		responses.append(response)
		times.append(time.time())

		response = client.order_market_sell(symbol=tradeInfo['COIN_ETH'], quantity=tradeInfo['COINvolume'], newOrderRespType='FULL')
		responses.append(response)
		times.append(time.time())
		
		response = client.order_market_sell(symbol="ETHBTC", quantity=tradeInfo['ETHvolume'], newOrderRespType='FULL')
		responses.append(response)
		times.append(time.time())

	# BACKWARDS DIRECTION
	else:
		response = client.order_market_buy(symbol="ETHBTC", quantity=tradeInfo['ETHvolume'], newOrderRespType='FULL')
		responses.append(response)
		times.append(time.time())

		response = client.order_market_buy(symbol=tradeInfo['COIN_ETH'], quantity=tradeInfo['COINvolume'], newOrderRespType='FULL')
		responses.append(response)
		times.append(time.time())

		response = client.order_market_sell(symbol=tradeInfo['COIN_BTC'], quantity=tradeInfo['COINvolume'], newOrderRespType='FULL')
		responses.append(response)
		times.append(time.time())

	# Writes info and updates balances
	endTrading(tradeInfo, responses, times)

# --- ARBITRAGE ---
def arbitrage():
	global numTradesFound
	global numTradesUnderThreshold
	global numTradesUnderVolume
	# Evaluate trades for each COINBTC-COINETH PAIR
	bestTrade = {'percentage': 0}

	for i in range(len(ETHmarkets)):
		newTrade = evaluateTrade(ETHmarkets[i], BTCmarkets[i])
		#print("New trade: {} ".format(newTrade['percentage']))
		if newTrade['percentage'] > bestTrade['percentage']:
		
			if checkMinQty(newTrade['COIN_BTC'], newTrade['COINvolume']) and checkMinQty(newTrade['COIN_ETH'],newTrade['COINvolume']) and checkMinQty('ETHBTC', newTrade['ETHvolume']):
				bestTrade = newTrade


	# Check if the best trade we found is over the percent threshold
#	print("best trade: ", bestTrade)
	if bestTrade['percentage'] == 0:
		numTradesUnderVolume += 1
	elif bestTrade['percentage'] > threshold:
		numTradesFound += 1
		trade(bestTrade)

	elif bestTrade['percentage'] > 1:
		numTradesUnderThreshold += 1


# GETS INFO AND STARTS PRINTUPDATE CYCLE
def initializePrintUpdate():
	global USDTconversions
	global USDTtotal
	global USDTstartingTotal
	# Getting starting USDT conversions value for consistent printUpdate
	order_book = client.get_orderbook_ticker()
	for n in order_book:
		if n['symbol'] == 'BTCUSDT':
			USDTconversions[0] = float(n['askPrice'])
		elif n['symbol'] == 'ETHUSDT':
			USDTconversions[1] = float(n['askPrice'])
		elif n['symbol'] == 'BNBUSDT':
			USDTconversions[2] = float(n['askPrice'])

	# Updates USDTtotal
	updateBalance()

	# getting starting total btc balance for printUpdate
	USDTstartingTotal = USDTtotal

	printUpdate()


# --- PROGRAM EXECUTION ---
initializePrintUpdate()
getMinimums()
while 1:
	getBidAsk(depths)
	arbitrage()
	time.sleep(2)
