####################################################################
# SPY & SH, minute data
# Grant Kiehne, 2013
#####################################################################
from scipy import stats
import numpy as np
from pytz import timezone
import pandas as pd

threshold = 1.5 # z-score difference threshold

window = 16*390 # window length in minutes
window_roll = 30 # window length for rolling stats

def initialize(context):
    
    context.stocks = [sid(8554),sid(32268)] # SPY & SH
    # context.stocks = [sid(19920),sid(32265)] # QQQ & PSQ
    
    context.prices = np.zeros([window,len(context.stocks)])
    context.volumes = np.zeros([window,len(context.stocks)])
    
    context.tic_count = 0
    
    context.previous_datetime = None
    context.new_day = None
    context.order_submitted = False
    
    print 'threshold = ' + str(threshold)
    
def handle_data(context, data):
    
    current_datetime = get_datetime().astimezone(timezone('US/Eastern'))
    
    if context.tic_count < window:
        for i, stock in enumerate(context.stocks):
            context.prices[context.tic_count,i] = data[stock].price
            context.volumes[context.tic_count,i] = data[stock].volume
    else:
        context.prices = np.roll(context.prices,-1,axis=0)
        context.volumes = np.roll(context.volumes,-1,axis=0)
        for i, stock in enumerate(context.stocks):
            context.prices[-1,i] = data[stock].price
            context.volumes[-1,i] = data[stock].volume  
    
    context.tic_count += 1
    
    if context.tic_count < window:
        context.previous_datetime = current_datetime
        return
    
    # skip tic if any orders are open or any stocks did not trade  
    for stock in context.stocks:  
        if bool(get_open_orders(stock)) or data[stock].datetime < get_datetime():  
            return
        
    # detect new trading day
    if current_datetime.day != context.previous_datetime.day:
        context.new_day = True
        context.previous_datetime = current_datetime
    
    # limit trading to once per day and within specified time window
    if not context.new_day:
        return
    elif not intradingwindow_check(context):
        return
    
    # if all conditions met, execute trading logic
    
    p = pd.rolling_mean(context.prices,window_roll)[window_roll-1:]
    # p = context.prices[window_roll-1:]
    v = pd.rolling_sum(context.volumes,window_roll)[window_roll-1:]
    
    dv = np.multiply(p,v) # compute dollar volumes
    
    # normalize dollar volume with z-score
    dv_z = stats.zscore(dv, axis=0, ddof=1)
    
    # compute z-score difference
    end = dv_z.shape[0]-1
    delta_z = dv_z[end,1] - dv_z[end,0]
    
    record(delta_z = delta_z)

    # plot capital invested (e.g. how much capital is invested)
    capital = capital_invested(context, data)
    record(capital_invested = capital)

    # plot cash
    cash = context.portfolio.cash
    record(cash = cash)
    
    # plot positions value
    positions_value = context.portfolio.positions_value
    record(positions_value = positions_value)
       
    # trade using z-score difference indicator (set global threshold above)
    for i, stock in enumerate(context.stocks):
        
        position = context.portfolio.positions[stock].amount     # current number of shares
        # shares = cash/data[stock].price/len(context.stocks)/.5   # desired position (using margin)
        shares = cash/data[stock].price/len(context.stocks)  # desired position (no margin)
        long_short = (-1)**i
        
        if delta_z > threshold:
            order(stock,(long_short*shares)-position)
            context.new_day = False
            
        elif delta_z < -threshold:       
            order(stock,(-long_short*shares)-position)
            context.new_day = False
       
def capital_invested(context, data):

    # get a sum total of capital spent or borrowed for all current positions
    capital = 0.0  # initialize to zero

    # check every stock in current positions (also works with set_universe)
    for stock in context.portfolio.positions:
        
        # get amount of shares in current position for this stock
        amount = context.portfolio.positions[stock].amount
        
        # get the cost basis of the shares (how much we spent on average per share)
        cost_basis = context.portfolio.positions[stock].cost_basis

        # check if position is a short trade (negative amount)
        amount = max(amount, -amount) # change amount to a positive number
                
        # add dollar amount to the 'spent' total
        capital += amount * cost_basis
    
    # return amount of capital tied up in positions
    return capital

def intradingwindow_check(context):
    # Converts all time-zones into US EST to avoid confusion
    loc_dt = get_datetime().astimezone(timezone('US/Eastern'))
    # if loc_dt.hour > 10 and loc_dt.hour < 15:
    if loc_dt.hour == 12 and loc_dt.minute == 0:
        return True
    else:
        return False
