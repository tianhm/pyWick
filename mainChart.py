import urllib2
import time
import datetime
import pylab
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.finance import candlestick
import sys


##################################################################
#        Scrapes historical data from Yahoo Finance API
##################################################################
def pullData(stock, m, d, y):
	try:
		fileLine = 'Quotes/'+stock+'.txt'
		# API call URL
		urlToVisit = 'http://ichart.yahoo.com/table.csv?s='+stock+'&a='+str(m-1)+'&b='+str(d)+'&c='+str(y)
		sourceCode = urllib2.urlopen(urlToVisit).read()
		splitSource = sourceCode.split('\n')

		# CSV formatting
		for eachLine in splitSource:
			splitLine = eachLine.split(',')
			if 'Date' not in eachLine:
				saveFile = open(fileLine, 'a')
				lineToWrite = eachLine+'\n'
				saveFile.write(lineToWrite)

		# Debugging statements
		print 'Pulled', stock
		print 'sleeping'
		# Time b/w each pull
		time.sleep(1)

	except Exception, e:
		print 'main loop', str(e)

##################################################################
#                         Scraper Call
##################################################################
argIn = sys.argv[1]
pullData(argIn, 3, 18, 2014)

##################################################################
#                 RSI calculator (using numpy)
##################################################################
def rsiCalc(prices, n=14):
	deltas = np.diff(prices)
	seed = deltas[:n+1]
	up = seed[seed>=0].sum()/n
	down = -seed[seed<0].sum()/n
	rs = up/down
	rsi = np.zeros_like(prices)
	rsi[:n] = 100. - 100./(1.+rs)

	for i in range(n, len(prices)):
		delta = deltas[i-1]
		if delta > 0:
			upval = delta
			downval = 0
		else:
			upval = 0
			downval = -delta

		up = (up*(n-1)+upval)/n
		down = (down*(n-1) + downval)/n

		rs = up/down
		rsi[i] = 100. -100./(1.+rs)

	return rsi

##################################################################
#                 SMA calculator (using numpy)
##################################################################
def simpleMovingAvg(values, window):
	# sma formula
	weights = np.repeat(1.0, window)/window
	# smoother (convolve smooths)
	smas = np.convolve(values, weights, 'valid')
	return smas

##################################################################
#                 EMA calculator (using numpy)
##################################################################
def ema(values, window):
	weights = np.exp(np.linspace(-1.,0.,window))
	weights /= weights.sum()
	a = np.convolve(values, weights, mode='full')[:len(values)]
	a[:window] = a[window]
	return a

##################################################################
#                 MACD calculator (using numpy)
##################################################################
def macdCalc(x, slow=26, fast=12):
	'''
	macd line = 12ema - 26 ema
	signal = 9ema
	histogram = macd - signal
	'''
	emaslow = ema(x, slow)
	emafast = ema(x, fast)
	return emaslow, emafast, emafast-emaslow

##################################################################
#       Grapher, params (Name of stock, SMA1 day, SMA2 day)
##################################################################
def graphData(stock, SMA1, SMA2):
	try:
		# -------Process Stock Data--------
		stockFile = 'Quotes/'+stock+'.txt'
		date, openp, highp, lowp, closep, volume, adjClose = np.loadtxt(stockFile, delimiter=',', unpack = True,
			converters={0: mdates.strpdate2num('%Y-%m-%d')})

		x = 0
		y = len(date)
		candleArr = []
		# Data into candlestick parameter format
		while x<y:
			appendLine = date[x], openp[x], closep[x], highp[x], lowp[x], volume[x]
			candleArr.append(appendLine)
			x+=1


		# simplemovingavg
		av1 = simpleMovingAvg(closep, SMA1)
		av2 = simpleMovingAvg(closep, SMA2)

		startingPoint = len(date[SMA2-1:])

		# legend label stuffs
		label1 = str(SMA1)+' SMA'
		label2 = str(SMA2)+' SMA'

		fig = plt.figure(facecolor='#07000d')

		#--------RSI GRAPH--------
		ax0 = plt.subplot2grid((6,4), (0,0), rowspan=1, colspan=4, axisbg='#07000d')
		ax0.spines['bottom'].set_color('#5998ff')
		ax0.spines['left'].set_color('#5998ff')
		ax0.spines['top'].set_color('#5998ff')
		ax0.spines['right'].set_color('#5998ff')
		ax0.grid(True, color='w')
		ax0.set_ylim(0, 100)
		ax0.yaxis.set_major_locator(mticker.MaxNLocator(3))
		plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(3,prune='lower'))
		rsi = rsiCalc(closep, 14)
		ax0.plot(date[:startingPoint], rsi[:startingPoint], '#00ffe8', linewidth=1.5)
		ax0.axhline(y=70, color='w')
		ax0.axhline(y=30, color='w')
		ax0.set_yticks([30,70])
		plt.tight_layout()

		plt.ylabel('RSI', color='w')
		for label in ax0.yaxis.get_ticklabels():
			label.set_color("w")

		# -------PRICE GRAPH-------
		ax1 = plt.subplot2grid((6,4), (1,0), sharex=ax0, rowspan=3, colspan=4, axisbg='#07000d')

		# Candlestick plot details
		candlestick(ax1, candleArr[:startingPoint], width=1, colorup='#9eff15', colordown='#ff1717')

		# plot the SMA on axis 1
		ax1.plot(date[:startingPoint], av1[:startingPoint], '#5998ff', label= label1, linewidth=1.2)
		ax1.plot(date[:startingPoint],av2[:startingPoint], '#e1edf9', label= label2, linewidth=1.2)

		# Mostly styling
		plt.ylabel('Price and Volume')
		ax1.grid(True, color='w')
		ax1.yaxis.label.set_color('w')
		ax1.spines['bottom'].set_color('#5998ff')
		ax1.spines['left'].set_color('#5998ff')
		ax1.spines['top'].set_color('#5998ff')
		ax1.spines['right'].set_color('#5998ff')
		ax1.tick_params(axis='y', colors='w')

		# Legend stuffs
		leg = plt.legend(loc=2, ncol=2, prop={'size': 10}, fancybox=True)
		leg.get_frame().set_alpha(0.4)
		textEd = pylab.gca().get_legend().get_texts()
		pylab.setp(textEd[0:5], color='w')

		# -------VOLUME GRAPH--------

		ax1v = ax1.twinx()
		ax1v.plot(date[:startingPoint], volume[:startingPoint], '#00ffe8', linewidth=.8)
		ax1v.fill_between(date[:startingPoint], 0, volume[:startingPoint], facecolor='#00ffe8', alpha=.5)

		# Mostly styling
		ax1v.axes.yaxis.set_ticklabels([])
		ax1v.grid(False)
		ax1v.yaxis.label.set_color('w')
		ax1v.xaxis.label.set_color('w')
		ax1v.spines['bottom'].set_color('#5998ff')
		ax1v.spines['left'].set_color('#5998ff')
		ax1v.spines['top'].set_color('#5998ff')
		ax1v.spines['right'].set_color('#5998ff')
		ax1v.set_ylim(0, 5*volume.max())

		ax1.xaxis.set_major_locator(mticker.MaxNLocator(8))
		ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

		# Rotate xaxis labels on volume graph and delete xaxis labels on price graph
		for label in ax1.xaxis.get_ticklabels():
			label.set_rotation(75)
			label.set_color('w')

		################################################################
		# for label in ax2.xaxis.get_ticklabels():
		# 	label.set_rotation(75)
		# 	label.set_color("w")
		################################################################


		# -------MACD GRAPH--------
		ax2 = plt.subplot2grid((6,4), (4,0), sharex=ax0, rowspan=1, colspan=4, axisbg='#07000d')

		# actual plotting
		# nema is the ema that macd is compared to (for crossovers)
		nema = 9

		emaslow, emafast, macd = macdCalc(closep)
		ema9 = ema(macd, nema)
		ax2.plot(date[:startingPoint], macd[:startingPoint], '#5998ff', label= 'MACD', linewidth=1.2)
		ax2.plot(date[:startingPoint], ema9[:startingPoint], '#ffffff', label= '9 day ema', linewidth=1.2)
		ax2.fill_between(date[:startingPoint], macd[:startingPoint]-ema9[:startingPoint], 0, alpha = 0.5, facecolor='#00ffe8', edgecolor='#00ffe8')

		plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(3, prune='upper'))

		# # Styling and bookeeping
		# MAKES TICKS INVISIBLE: ax2.axes.yaxis.set_ticklabels([])
		ax2.grid(True, color='w')
		ax2.yaxis.label.set_color('w')
		ax2.xaxis.label.set_color('w')
		ax2.spines['bottom'].set_color('#5998ff')
		ax2.spines['left'].set_color('#5998ff')
		ax2.spines['top'].set_color('#5998ff')
		ax2.spines['right'].set_color('#5998ff')
		ax2.tick_params(axis='y', colors='w')
		plt.ylabel('MACD')

		ax2.xaxis.set_major_locator(mticker.MaxNLocator(8))
		ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

		# Rotate xaxis labels on volume graph and delete xaxis labels on price graph
		for label in ax1.xaxis.get_ticklabels():
			label.set_visible(False)
		for label in ax2.xaxis.get_ticklabels():
			label.set_rotation(75)
			label.set_color('w')
		for label in ax2.yaxis.get_ticklabels():
			label.set_color('w')



		plt.subplots_adjust(left=0.08, bottom=.07, right=0.95, top=0.93, wspace=.20, hspace=0.00)

		plt.suptitle(stock, color='w')

		plt.show()

	except Exception, e:
		print 'failed main loop', str(e)

#INSERT LOGIC TO DO PULLS VIA  pullData(stock, month, day, year) function
#########################################################################

# Call the graph function on run
graphData(argIn, 12, 26)
