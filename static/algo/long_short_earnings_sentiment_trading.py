####################################################################
# Long short earnings sentiment trading
# Steven Hayes, 2017
#####################################################################
"""
This is a PEAD strategy based off Estimize's earnings estimates. Estimize
is a service that aggregate financial estimates from independent, buy-side,
sell-side analysts as well as students and professors. You can run this
algorithm yourself by geting the free sample version of Estimize's consensus
dataset and EventVestor's Earnings Calendar Dataset at:

- https://www.quantopian.com/data/eventvestor/earnings_calendar
- https://www.quantopian.com/data/estimize/revisions

Much of the variables are meant for you to be able to play around with them:
1. context.days_to_hold: defines the number of days you want to hold before exiting a position
2. context.min/max_surprise: defines the min/max % surprise you want before trading on a signal
"""

import numpy as np
from pytz import timezone       # Python only does once, makes this portable.  
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import CustomFactor, AverageDollarVolume

# Premium version avilable at
# https://www.quantopian.com/data/eventvestor/earnings_calendar
from quantopian.pipeline.data.estimize import (
    ConsensusEstimizeEPS,
    ConsensusWallstreetEPS,
    ConsensusEstimizeRevenue, 
    ConsensusWallstreetRevenue
)

# The sample and full version is found through the same namespace
# https://www.quantopian.com/data/eventvestor/earnings_calendar
# Sample date ranges: 01 Jan 2007 - 10 Feb 2014
from quantopian.pipeline.data.eventvestor import EarningsCalendar
from quantopian.pipeline.factors.eventvestor import (
    BusinessDaysUntilNextEarnings,
    BusinessDaysSincePreviousEarnings
)

from quantopian.pipeline.data.accern import alphaone as alphaone
# Premium version availabe at
# https://www.quantopian.com/data/accern/alphaone
# from quantopian.pipeline.data.accern import alphaone as alphaone

class PercentSurprise(CustomFactor):
    window_length = 1
    inputs = [ConsensusEstimizeEPS.previous_actual_value,
              ConsensusEstimizeEPS.previous_mean]

    def compute(self, today, assets, out, actual_eps, estimize_eps):
        out[:] = (actual_eps[-1] - estimize_eps[-1])/(estimize_eps[-1] + 0)

def make_pipeline(context):
    # Create our pipeline  
    pipe = Pipeline()  

    # Instantiating our factors  
    factor = PercentSurprise()

    # Screen out penny stocks and low liquidity securities.  
    dollar_volume = AverageDollarVolume(window_length=20)  
    is_liquid = dollar_volume > 10**7

    # Filter down to stocks in the top/bottom  
    longs = (factor >= context.min_surprise) & (factor <= context.max_surprise)

    # Set our pipeline screens  
    # Filter down stocks using sentiment  
    article_sentiment = alphaone.article_sentiment.latest
    top_universe = is_liquid & longs & article_sentiment.notnan() & (article_sentiment > .45)

    # Add longs to the pipeline  
    pipe.add(top_universe, "longs")
    pipe.add(BusinessDaysSincePreviousEarnings(), 'pe')
    
    return pipe  
        
def initialize(context):
    #: Set commissions and slippage to 0 to determine pure alpha
    set_commission(commission.PerShare(cost=0, min_trade_cost=0))
    set_slippage(slippage.FixedSlippage(spread=0))
    
    context.queue_list = []
    context.track_orders = 1    # toggle on|off
    
    context.orders = {}               # Move these to initialize() for better efficiency.  
    context.dates  = { 
            'active': 0,  
            'start' : [],           # Start dates, option  
            'stop'  : []            # Stop  dates, option  
        }  
    
    #: Set to Long Only
    set_long_only()

    #: Declaring the days to hold, change this to what you want)))
    context.days_to_hold = 5
    #: Declares which stocks we currently held and how many days we've held them dict[stock:days_held]
    context.stocks_held = {}

    #: Declares the minimum magnitude of percent surprise
    context.min_surprise = .00
    context.max_surprise = .06

    # Make our pipeline
    attach_pipeline(make_pipeline(context), 'estimize')

    
    # Log our positions at 10:00AM
    schedule_function(func=log_positions,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close())
    # Order our positions
    schedule_function(func=queues,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_open())
    '''
    # For every minute available (max is 6 hours and 30 minutes)
    total_minutes = 6*60 + 30

    for i in range(total_minutes):
    # Every 30 minutes run schedule
        if i % 30 == 0:
            schedule_function(check_positions_for_loss_or_profit,
                              date_rules.every_day(),
                              time_rules.market_open(minutes=i),
                              True)
    '''

def before_trading_start(context, data):
    # Screen for securities that only have an earnings release
    # 1 business day previous and separate out the earnings surprises into
    # positive and negative 
    results = pipeline_output('estimize')
    results = results[results['pe'] == 1]
    assets_in_universe = results.index
    context.positive_surprise = assets_in_universe[results.longs]


def log_positions(context, data):
    #: Get all positions  
    if len(context.portfolio.positions) > 0:  
        all_positions = "Current positions for %s : " % (str(get_datetime()))  
        for pos in context.portfolio.positions:  
            if context.portfolio.positions[pos].amount != 0:  
                all_positions += "%s at %s shares, " % (pos.symbol, context.portfolio.positions[pos].amount)  
        log.info(all_positions)  

def trade(context, data):    # Process any queued orders
    if get_open_orders(): return    # Wait for fills

    c = context
    mult = .95        # Multiplier for weights in orders, cash vs
                       #  slippage, commissions, to avoid negative cash.
    log_changes = 1    # Whether to log weight|allocation changes.
    sells = 0          # Indicator, whether any sells happened.
    qlist = sorted(c.queue_list)[:]  # Make an independent copy to allow remove().

    for o in qlist:    # Each order queued, process any sells
        security  = o[1] ; weight = o[0]
        pf_value_now = c.portfolio.positions[security].amount * data.current(security, 'price')
        pf_ratio_now = pf_value_now / c.portfolio.portfolio_value
        if weight < pf_ratio_now:   # sell, is decrease in allocation
            if log_changes:
                log.info('   {} {} {} ==> {}'.format(
                    minut(), security.symbol, '%.3f' % pf_ratio_now, '%.3f' % weight))
            order_target_percent(security, mult * weight)    # Selling
            c.queue_list.remove(o)
            sells = 1  # let these settle before/if any buys

    if sells: return   # let any sells go thru before buys

    '''
    To do if Robinhood: Make sure T+3 is satisfied before buys here.
    Untested ...
    c = context
    date = get_datetime().date()
    if c.date_prv != date:
        c.day_count += 1
        c.date_prv = date
    if c.day_count <= 3:
        return
    else:
        c.day_count = 0
    '''

    for o in qlist:    # Should be all buys at this point
        security  = o[1] ; weight = o[0]
        pf_value_now = c.portfolio.positions[security].amount * data.current(security, 'price')
        pf_ratio_now = pf_value_now / c.portfolio.portfolio_value
        if weight > pf_ratio_now:   # buy, is increase in allocation
            if log_changes:
                log.info('   {} {} {} ==> {}'.format(
                    minut(), security.symbol, '%.3f' % pf_ratio_now, '%.3f' % weight))
            order_target_percent(security, mult * weight)    # Buying
            c.queue_list.remove(o)
        
 
def queues(context, data): # Was Order_Positions Before
    """
    Main ordering conditions to always order an equal percentage in each position
    so it does a rolling rebalance by looking at the stocks to order today and the stocks
    we currently hold in our portfolio.
    """
    if context.queue_list: return    # wait for orders to clear

    port = context.portfolio.positions
    #record(leverage=context.account.leverage)
    
    # Check our positions for loss or profit and exit if necessary
    check_positions_for_loss_or_profit(context, data)
    
    # Check if we've exited our positions and if we haven't, exit the remaining securities
    # that we have left
    sell_allocation = 0
    for security in port:  
        if data.can_trade(security):  
            if context.stocks_held.get(security) is not None:  
                context.stocks_held[security] += 1  
                if context.stocks_held[security] >= context.days_to_hold:  
                    context.queue_list.append((sell_allocation, security))   
                    del context.stocks_held[security]
            # If we've deleted it but it still hasn't been exited. Try exiting again  
          #  else:  
          #      log.info("Haven't yet exited %s, ordering again" % security.symbol)  
          #      order_target_percent(security, 0)  

    # Check our current positions
    current_positive_pos = [pos for pos in port if (port[pos].amount > 0 and pos in context.stocks_held)]
    positive_stocks = context.positive_surprise.tolist() + current_positive_pos
    
    # Rebalance our positive surprise securities (existing + new)                
    for security in positive_stocks:
        can_trade = context.stocks_held.get(security) <= context.days_to_hold or \
                    context.stocks_held.get(security) is None
        if data.can_trade(security) and can_trade:
            buy_allocation = 0.95 / len(positive_stocks)
            context.queue_list.append((buy_allocation, security))
            if context.stocks_held.get(security) is None:
                context.stocks_held[security] = 0
    

def check_positions_for_loss_or_profit(context, data):
    # Sell our positions on longs for profit or loss
    if context.queue_list: return    # wait for orders to clear
    sell_allocation = 0
    for security in context.portfolio.positions:
        is_stock_held = context.stocks_held.get(security) > 0
        if data.can_trade(security) and is_stock_held and not get_open_orders(security):
            current_position = context.portfolio.positions[security].amount  
            cost_basis = context.portfolio.positions[security].cost_basis  
            price = data.current(security, 'price')
            # On Long & Profit
            if price >= cost_basis * 1.04 and current_position > 0:  
                context.queue_list.append((sell_allocation, security))  
                log.info( str(security) + ' Sold Long for Profit')  
                del context.stocks_held[security]  
            # On Long & Loss
            if price <= cost_basis * 0.95 and current_position > 0:  
                context.queue_list.append((sell_allocation, security))
                log.info( str(security) + ' Sold Long for Loss')  
                del context.stocks_held[security]
    track_orders(context, data)

def handle_data(context, data):
    if get_open_orders():
        track_orders(context, data)    # for filled orders
        return
    if context.queue_list:
        trade(context, data)
    track_orders(context, data)        # for new orders and last-frame-filled's
    #check_positions_for_loss_or_profit(context, data)
    pvr(context, data)    
    
def track_orders(context, data):  # Log orders created, filled, unfilled or canceled.  
    '''      https://www.quantopian.com/posts/track-orders  
    Status:  
       0 - Unfilled  
       1 - Filled (can be partial)  
       2 - Canceled  
    '''  
    c = context  
    log_cash = 1    # Show cash values in logging window or not.  
    log_ids  = 1    # Include order id's in logging window or not.

    ''' Start and stop date options ...  
    To not overwhelm the logging window, start/stop dates can be entered  
      either below or in initialize() if you move to there for better efficiency.  
    Example:  
        c.dates  = {  
            'active': 0,  
            'start' : ['2007-05-07', '2010-04-26'],  
            'stop'  : ['2008-02-13', '2010-11-15']  
        }  
    '''  
    '''
    if 'orders' not in c:  
        c.orders = {}               # Move these to initialize() for better efficiency.  
        c.dates  = { 
            'active': 0,  
            'start' : [],           # Start dates, option  
            'stop'  : []            # Stop  dates, option  
        }  
    '''

    # If the dates 'start' or 'stop' lists have something in them, sets them.  
    if c.dates['start'] or c.dates['stop']:  
        date = str(get_datetime().date())
        if   date in c.dates['start']:    # See if there's a match to start  
            c.dates['active'] = 1  
        elif date in c.dates['stop']:     #   ... or to stop  
            c.dates['active'] = 0  
    else:  
        c.dates['active'] = 1  # Set to active b/c no conditions

    if c.dates['active'] == 0:  
        return                 # Skip if off

    def _minute():   # To preface each line with the minute of the day.  
        if get_environment('data_frequency') == 'minute':  
            bar_dt = get_datetime().astimezone(timezone('US/Eastern'))  
            minute = (bar_dt.hour * 60) + bar_dt.minute - 570  # (-570 = 9:31a)  
            return str(minute).rjust(3)  
        return ''    # Daily mode, just leave it out.

    def _orders(to_log):    # So all logging comes from the same line number,  
        log.info(to_log)    #   for vertical alignment in the logging window.

    ordrs = c.orders.copy()    # Independent copy to allow deletes  
    for id in ordrs:  
        o    = get_order(id)  
        sec  = o.sid ; sym = sec.symbol  
        oid  = o.id if log_ids else ''  
        cash = 'cash {}'.format(int(c.portfolio.cash)) if log_cash else ''  
        prc  = '%.2f' % data.current(sec, 'price')
        if o.filled:        # Filled at least some  
            trade  = 'Bot' if o.amount > 0 else 'Sold'  
            filled = '{}'.format(o.amount)  
            if o.filled == o.amount:    # complete  
                if 0 < c.orders[o.id] < o.amount:  
                    filled  = 'all/{}'.format(o.amount)  
                del c.orders[o.id]  
            else:  
                done_prv       = c.orders[o.id]       # previously filled ttl  
                filled_this    = o.filled - done_prv  # filled this time, can be 0  
                c.orders[o.id] = o.filled             # save for increments math  
                filled         = '{}/{}'.format(filled_this, o.amount)  
            _orders(' {}      {} {} {} at {}   {} {}'.format(_minute(),  
                trade, filled, sym, prc, cash, oid))  
        else:  
            canceled = 'canceled' if o.status == 2 else ''  
            _orders(' {}         {} {} unfilled {} {}'.format(_minute(),  
                    o.sid.symbol, o.amount, canceled, oid))  
            if canceled: del c.orders[o.id]

    for oo_list in get_open_orders().values(): # Open orders list  
        for o in oo_list:  
            sec  = o.sid ; sym = sec.symbol  
            oid  = o.id if log_ids else ''  
            cash = 'cash {}'.format(int(c.portfolio.cash)) if log_cash else ''  
            prc  = '%.2f' % data.current(sec, 'price')
            if o.status == 2:                  # Canceled  
                _orders(' {}    Canceled {} {} order   {} {}'.format(_minute(),  
                        trade, o.amount, sym, prc, cash, oid))  
                del c.orders[o.id]  
            elif o.id not in c.orders:         # New  
                c.orders[o.id] = 0  
                trade = 'Buy' if o.amount > 0 else 'Sell'  
                if o.limit:                    # Limit order  
                    _orders(' {}   {} {} {} now {} limit {}   {} {}'.format(_minute(),  
                        trade, o.amount, sym, prc, o.limit, cash, oid))  
                elif o.stop:                   # Stop order  
                    _orders(' {}   {} {} {} now {} stop {}   {} {}'.format(_minute(),  
                        trade, o.amount, sym, prc, o.stop, cash, oid))  
                else:                          # Market order  
                    _orders(' {}   {} {} {} at {}   {} {}'.format(_minute(),  
                        trade, o.amount, sym, prc, cash, oid))  
                
def pvr(context, data):  
    ''' Custom chart and/or log of profit_vs_risk returns and related information  
    '''  
    # # # # # # # # # #  Options  # # # # # # # # # #  
    record_max_lvrg = 1         # Maximum leverage encountered  
    record_leverage = 0         # Leverage (context.account.leverage)  
    record_q_return = 0         # Quantopian returns (percentage)  
    record_pvr      = 1         # Profit vs Risk returns (percentage)  
    record_pnl      = 1         # Profit-n-Loss  
    record_shorting = 0         # Total value of any shorts  
    record_overshrt = 0         # Shorts beyond longs+cash  
    record_risk     = 0         # Risked, max cash spent or shorts beyond longs+cash  
    record_risk_hi  = 1         # Highest risk overall  
    record_cash     = 0         # Cash available  
    record_cash_low = 1         # Any new lowest cash level  
    logging         = 1         # Also to logging window conditionally (1) or not (0)  
    log_method      = 'risk_hi' # 'daily' or 'risk_hi'

    from pytz import timezone   # Python will only do once, makes this portable.  
                                #   Move to top of algo for better efficiency.  
    c = context  # Brevity is the soul of wit -- Shakespeare [for efficiency, readability]  
    if 'pvr' not in c:  
        date_strt = get_environment('start').date()  
        date_end  = get_environment('end').date()  
        cash_low  = c.portfolio.starting_cash  
        mode      = get_environment('data_frequency')  
        c.pvr = {  
            'max_lvrg': 0,  
            'risk_hi' : 0,  
            'days'    : 0.0,  
            'date_prv': '',  
            'cash_low': cash_low,  
            'date_end': date_end,  
            'mode'    : mode,  
            'run_str' : '{} to {}  {}  {}'.format(date_strt,date_end,int(cash_low),mode)  
        }  
        log.info(c.pvr['run_str'])  
    pvr_rtrn     = 0            # Profit vs Risk returns based on maximum spent  
    profit_loss  = 0            # Profit-n-loss  
    shorts       = 0            # Shorts value  
    longs        = 0            # Longs  value  
    overshorts   = 0            # Shorts value beyond longs plus cash  
    new_risk_hi  = 0  
    new_cash_low = 0                           # To trigger logging in cash_low case  
    lvrg         = c.account.leverage          # Standard leverage, in-house  
    date         = get_datetime().date()       # To trigger logging in daily case  
    cash         = c.portfolio.cash  
    start        = c.portfolio.starting_cash  
    cash_dip     = int(max(0, start - cash))  
    q_rtrn       = 100 * (c.portfolio.portfolio_value - start) / start

    if int(cash) < c.pvr['cash_low']:                # New cash low  
        new_cash_low = 1  
        c.pvr['cash_low']   = int(cash)  
        if record_cash_low:  
            record(CashLow = int(c.pvr['cash_low'])) # Lowest cash level hit

    if record_max_lvrg:  
        if c.account.leverage > c.pvr['max_lvrg']:  
            c.pvr['max_lvrg'] = c.account.leverage  
            record(MaxLv = c.pvr['max_lvrg'])        # Maximum leverage

    if record_pnl:  
        profit_loss = c.portfolio.pnl  
        record(PnL = profit_loss)                    # "Profit and Loss" in dollars

    for p in c.portfolio.positions:
        if data.can_trade(p):
            shrs = c.portfolio.positions[p].amount 
            if shrs < 0:  
                shorts += int(abs(shrs * data.current(p, 'price')))
            if shrs > 0:  
                longs  += int(shrs * data.current(p, 'price'))

    if shorts > longs + cash: overshorts = shorts             # Shorts when too high  
    if record_shorting: record(Shorts  = shorts)              # Shorts value as a positve  
    if record_overshrt: record(OvrShrt = overshorts)          # Shorts value as a positve  
    if record_cash:     record(Cash = int(c.portfolio.cash))  # Cash  
    if record_leverage: record(Lvrg = c.account.leverage)     # Leverage

    risk = int(max(cash_dip, shorts))  
    if record_risk: record(Risk = risk)       # Amount in play, maximum of shorts or cash used

    if risk > c.pvr['risk_hi']:  
        c.pvr['risk_hi'] = risk  
        new_risk_hi = 1

        if record_risk_hi:  
            record(RiskHi = c.pvr['risk_hi']) # Highest risk overall

    if record_pvr:      # Profit_vs_Risk returns based on max amount actually spent (risk high)  
        if c.pvr['risk_hi'] != 0:     # Avoid zero-divide  
            pvr_rtrn = 100 * (c.portfolio.portfolio_value - start) / c.pvr['risk_hi']  
            record(PvR = pvr_rtrn)            # Profit_vs_Risk returns

    if record_q_return:  
        record(QRet = q_rtrn)                 # Quantopian returns to compare to pvr returns curve

    def _minute():   # To preface each line with minute of the day.  
        if get_environment('data_frequency') == 'minute':  
            bar_dt = get_datetime().astimezone(timezone('US/Eastern'))  
            minute = (bar_dt.hour * 60) + bar_dt.minute - 570  # (-570 = 9:31a)  
            return str(minute).rjust(3)  
        return ''    # Daily mode, just leave it out.

    def _pvr_():  
            log.info('PvR {} %/day     {}'.format(  
                '%.4f' % (pvr_rtrn / c.pvr['days']), c.pvr['run_str']))  
            log.info('  Profited {} on {} activated/transacted for PvR of {}%'.format(  
                '%.0f' % (c.portfolio.portfolio_value - start), '%.0f' % c.pvr['risk_hi'],  
                '%.1f' % pvr_rtrn))  
            log.info('  QRet {} PvR {} CshLw {} MxLv {} RskHi {} Shrts {}'.format(  
                '%.2f' % q_rtrn, '%.2f' % pvr_rtrn, '%.0f' % c.pvr['cash_low'],  
                '%.2f' % c.pvr['max_lvrg'], '%.0f' % c.pvr['risk_hi'], '%.0f' % shorts))

    if logging:  
        if log_method == 'risk_hi' and new_risk_hi \
          or log_method == 'daily' and c.pvr['date_prv'] != date \
          or new_cash_low:  
            qret    = ' QRet '   + '%.1f' % q_rtrn  
            lv      = ' Lv '     + '%.1f' % lvrg              if record_leverage else ''  
            pvr     = ' PvR '    + '%.1f' % pvr_rtrn          if record_pvr      else ''  
            pnl     = ' PnL '    + '%.0f' % profit_loss       if record_pnl      else ''  
            csh     = ' Cash '   + '%.0f' % cash              if record_cash     else ''  
            shrt    = ' Shrt '   + '%.0f' % shorts            if record_shorting else ''  
            ovrshrt = ' Shrt '   + '%.0f' % overshorts        if record_overshrt else ''  
            risk    = ' Risk '   + '%.0f' % risk              if record_risk     else ''  
            mxlv    = ' MaxLv '  + '%.2f' % c.pvr['max_lvrg'] if record_max_lvrg else ''  
            csh_lw  = ' CshLw '  + '%.0f' % c.pvr['cash_low'] if record_cash_low else ''  
            rsk_hi  = ' RskHi '  + '%.0f' % c.pvr['risk_hi']  if record_risk_hi  else ''  
            log.info('{}{}{}{}{}{}{}{}{}{}{}{}'.format(_minute(),  
               lv, mxlv, qret, pvr, pnl, csh, csh_lw, shrt, ovrshrt, risk, rsk_hi))  
    if c.pvr['date_prv'] != date: c.pvr['days'] += 1.0  
    if c.pvr['days'] % 130 == 0 and _minute() == '100': _pvr_()  
    c.pvr['date_prv'] = date  
    if c.pvr['date_end'] == date:  
        # Summary on last minute of last day.  
        # If using schedule_function(), backtest last day/time may need to match for this to execute.  
        if 'pvr_summary_done' not in c: c.pvr_summary_done = 0  
        log_summary = 0  
        if c.pvr['mode'] == 'daily' and get_datetime().date() == c.pvr['date_end']:  
            log_summary = 1  
        elif c.pvr['mode'] == 'minute' and get_datetime() == get_environment('end'):  
            log_summary = 1  
        if log_summary and not c.pvr_summary_done:  
            _pvr_()  
            c.pvr_summary_done = 1
def minut():   # To preface each line with the minute of the day.
               # Added to be used in trade()
    if get_environment('data_frequency') == 'minute':
        bar_dt = get_datetime().astimezone(timezone('US/Eastern'))
        minute = (bar_dt.hour * 60) + bar_dt.minute - 570  # (-570 = 9:31a)
        return str(minute).rjust(3)
    return ''    # Daily mode, just leave it out.
