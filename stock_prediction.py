import finnhub
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plot

import base64
import io 

finnhub_client = finnhub.Client(api_key="c60v2d2ad3ifmvvnrg90")


def getDataFrame(stock, timeInterval, startTrackTime, endTrackTime, spanWanted1, spanWanted2): #wantedAverage was a parameter but left out 
#spanwanted is for the EMA's, always put 12 and 26 respectivley
#timeInterval should be set to 1
    # try-except
    # try if workrs fine
    # if not, flask a message
    # flash() from flask and do nothing
    # https://flask.palletsprojects.com/en/2.0.x/patterns/flashing/
    res = finnhub_client.stock_candles(stock, timeInterval, startTrackTime, endTrackTime)
    
    res['close'] = res.pop('c')
    res['high'] = res.pop('h')
    res['low'] = res.pop('l')
    res['open'] = res.pop('o')
    res['time'] = res.pop('t')
    res['status'] = res.pop('s')
    res['volume'] = res.pop('v')

    times = res['time']

    for i in range(len(times)):
        times[i] = datetime.utcfromtimestamp(times[i]).strftime('%Y-%m-%d %H:%M:%S')

    resDF = pd.DataFrame(res)

    resDF['EMA ' + str(spanWanted1)] = resDF['close'].ewm(span=spanWanted1, adjust=False).mean()

    resDF['EMA ' + str(spanWanted2)] = resDF['close'].ewm(span=spanWanted2, adjust=False).mean()

    resDF['macd'] = resDF['EMA ' + str(spanWanted1)] - resDF['EMA ' + str(spanWanted2)]
    
    resDF['macdsignal'] = resDF.macd.ewm(span=9, adjust=False).mean()

    #creating trading signal

    resDF['trading_signal'] = np.nan

    # Buy signals
    resDF.loc[resDF['macd'] > resDF['macdsignal'], 'trading_signal'] = 1

    # Sell signals
    resDF.loc[resDF['macd'] < resDF['macdsignal'], 'trading_signal'] = -1

    # Fill the missing values with last valid observation
    resDF = resDF.fillna(method = 'ffill')

    # resDF.tail()
    # print(resDF.close)

    # Calculate minute-by-minute returns of stock
    resDF['returns'] = resDF.close.pct_change()

    # Calculate minute-by-minute strategy returns
    resDF['strategy_returns'] = resDF.returns * resDF.trading_signal.shift(1)

    # Calculate cumulative strategy returns
    cumulative_strategy_returns = (resDF.strategy_returns + 1).cumprod()


    # Calculate minute-by-minute strategy returns
    resDF['strategy_returns'] = resDF.returns * resDF.trading_signal.shift(1)

    # Calculate cumulative strategy returns
    cumulative_strategy_returns = (resDF.strategy_returns + 1).cumprod()

    resDF['cumulative_strategy_returns'] = cumulative_strategy_returns

      # Total number of trading days
    mins = len(cumulative_strategy_returns)

    # Calculate compounded daily growth rate
    daily_returns = (cumulative_strategy_returns.iloc[-1]**(450/mins) - 1)*100 #450 is minutes in a trading day

    print('The CAGR is %.2f%%' % daily_returns)

    return resDF

# tsla1 = getDataFrame('TSLA', '1', 1633338300, 1635526500, 12, 26)
# print(tsla1)


def aPlot(dataFrame):

# resDF[['macd','macdsignal']][-100:].plot(figsize=(15,7))
    # dataFrame[['macd','macdsignal']][-100:].plot(figsize=(15,7))

    # plot.ylabel('Price')
    # plot.title('MACD and MACD Signal Line')
    # plot.show()
    

    # Plot cumulative strategy returns
    dataFrame['cumulative_strategy_returns'].plot(figsize=(15,7))
    plot.ylabel('Cumulative Returns')
    plot.title('Cumulative Returns of MACD Strategy of Stock')

    pic_IObytes = io.BytesIO()
    plot.savefig(pic_IObytes,  format='png')
    pic_IObytes.seek(0)
    pic_hash = base64.b64encode(pic_IObytes.read()).decode('utf-8')
    plot.close()
    # use plt.savefig with io
    # stack overflow examples
    # return output of base64.b64encode()
    # pic_hash = 
    # pic_hash = "data:image/png;base64,{0}".format(pic_hash)
    return pic_hash
    # return dataFrame

    #plot.show()
#print(aPlot(tsla1))

from flask import Flask, request, render_template

app = Flask(__name__)

# params - text from button
# return a matplotlib plot
# which will be shown..
# uses Teshi's code until CAGP is calcualted..
#https://www.tutorialspoint.com/how-to-show-matplotlib-in-flask


@app.route('/', methods=['GET'])
def my_form():
    #print('here!!!')
    return render_template('main.html')


@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['random_names']
    processed_text = text.upper()
    # TODO: fix the time to use current time and 1 year before current time
    try:
      stock_data = getDataFrame(processed_text, 'D', 1633338300, 1635526500, 12, 26)
    
      img_string = aPlot(stock_data)
    # img_string = 'data:image/png;base64,' + img_string
    # print(img_string)
      return render_template('plot.html', stock_name=processed_text, img_data=img_string)
    except:
      return render_template('error.html', stock_name=processed_text)

app.run(host='0.0.0.0', debug=False)







