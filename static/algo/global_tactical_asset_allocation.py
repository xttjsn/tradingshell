####################################################################
# Zero Commission Algorithm Trading - Robinhood & Quantopian
# Seong Lee, 2016
#####################################################################
"""
This is a simple tactical asset allocation model that uses
simple timing rules to prevent extreme drawdowns and
volatility. 

It is based off of Mebane Faber's "Global Tactical Asset
Allocation" (GTAA). GTAA consists of five global asset
classes:  US stocks, foreign stocks, bonds, real estate
and commodities...it is either long the asset class or in cash 
with its allocation of the funds. 

The basics of the strategy go like this:
(1) Look at a 200 day trailing window (SA - Slow Average) versus
    a 20 day trailing window (FA - Fast Average).
    - We do this in `calculate_exposure`
(2) If the FA is greater than the SA, go long about 20% of your
    portfolio in that security
    - We do this in `open_new_positions`
(3) If the FA is less than the SA, have 0% of your portfolio in
    that security
    - We do this in `close_positions`

Check out Mr. Faber's website: http://www.cambriainvestments.com
for more information. The updated whitepaper can also be found:
- http://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461

Specifically for Robinhood users we have a few measures in place:
(1) This algorithm will not trade if you have unsettled funds.
    That can be found that in `do_unsettled_funds_exist`
(2) This algorithm will calculate order amounts only based on
    the amount of cash (settled_cash) and the positions you
    have in the securities listed under `context.assets`.
    This means you're existing positions will not be touched
    and all order calculations are based off (cash + value in
    context.asset securities).
    That can be found in `order_for_robinhood`
(3) If you currently hold positions in any security found in
    context.assets. We will not be entering into a trade on the
    first day.
(4) This algorithm is set in a "set it and forget it" style. 
    Because it will not place any trades while you have unsettled
    funds, we encourage you to be selective when trading in your
    Robinhood account outside of this algorithm as to avoid
    unwanted behavior.
For more information, please visit:
- www.quantopian.com/help#overview-livetrading
"""

# The initialize function is the place to set your tradable
# universe and define any parameters. 
def initialize(context):
    # Robinhood only allows long positions, use this trading
    # guard in case
    set_long_only()
    
    # Since we are trading with Robinhood we can set this to $0!
    set_commission(commission.PerTrade(cost=0))
    
    # Define our five global assets.
    context.assets = [sid(8554),  # S&P 500 (SPY)
                      sid(22972), # Foreign developed (EFA)
                      sid(23870), # 7-10 year Treasury bond (IEF)
                      sid(28054), # Commodities (DBC)
                      sid(26669)] # Real Estate Invesment Trusts (VNQ)
              
    # We will weight each asset equally and leave a 5% cash
    # reserve.
    context.weight = 0.95 / len(context.assets)
    
    # Define our lookback period for the moving average rule.
    context.lookback = 200
    context.fast_lookback = 20
    
    # Initialize two collections of stocks that we want to buy
    # and sell. 
    context.reduce_exposure = []
    context.increase_exposure = []
    
    # This code is here so we enter into trades on the very
    # first day that this live algorithm gets deployed
    context.first_trade = True
    
    # Schedule function allows us to set when we want to 
    # execute our functions. In this case, we want it to 
    # check every day if it's the first trade date (when
    # you first launch the algo) and do it 60 minutes 
    # after market open. at 10:31 AM. 
    schedule_function(first_trade, date_rules.every_day(),
                      time_rules.market_open(minutes=60))
        
    # Schedule our functions so that we sell our old stocks,
    # settle the cash, and then buy our new stocks.
    schedule_function(calculate_exposure,
                      date_rules.month_end(days_offset=4),
                      time_rules.market_open())
    schedule_function(close_positions,
                      date_rules.month_end(days_offset=4),
                      time_rules.market_open(minutes=60))
    schedule_function(open_new_positions,
                      date_rules.month_end(),
                      time_rules.market_open(minutes=60))

def do_unsettled_funds_exist(context):
    """
    For Robinhood users. In order to prevent you from attempting
    to trade on unsettled cash (settlement dates are T+3) from
    sale of proceeds. You can use this snippet of code which
    checks for whether or not you currently have unsettled funds
    """
    if context.portfolio.cash != context.account.settled_cash:
        return True

def get_percent_held(context, security, portfolio_value):
    """
    This calculates the percentage of each security that we currently
    hold in the portfolio.
    """
    if security in context.portfolio.positions:
        position = context.portfolio.positions[security]
        value_held = position.last_sale_price * position.amount
        percent_held = value_held/float(portfolio_value)
        return percent_held
    else:
        # If we don't hold any positions, return 0%
        return 0.0

def order_for_robinhood(context, security, weight, 
                        order_style=None):
    """
    This is a custom order method for this particular algorithm and
    places orders based on:
    (1) How much of each position in context.assets we currently hold
    (2) How much cash we currently hold

    This means that if you have existing positions (e.g. AAPL),
    your positions in that security will not be taken into
    account when calculating order amounts.

    The portfolio value that we'll be ordering on is labeled 
    `valid_portfolio_value`.
    
    If you'd like to use a Stop/Limit/Stop-Limit Order please follow the
    following format:
    STOP - order_style = StopOrder(stop_price)
    LIMIT - order_style = LimitOrder(limit_price)
    STOPLIMIT - order_style = StopLimitOrder(limit_price=x, stop_price=y)
    """
    # We use .95 as the cash because all market orders are converted into 
    # limit orders with a 5% buffer. So any market order placed through
    # Robinhood is submitted as a limit order with (last_traded_price * 1.05)
    valid_portfolio_value = context.portfolio.cash * .95

    for s in context.assets:
        # Calculate dollar amount of each position in context.assets
        # that we currently hold
        if s in context.portfolio.positions:
            position = context.portfolio.positions[s]
            valid_portfolio_value += position.last_sale_price * \
                position.amount
 
    # Calculate the percent of each security that we want to hold
    percent_to_order = weight - get_percent_held(context,
                                                 security,
                                                 valid_portfolio_value)
    
    # If within 1% of target weight, ignore.
    if abs(percent_to_order) < .01:
        return

    # Calculate the dollar value to order for this security
    value_to_order = percent_to_order * valid_portfolio_value
    if order_style:
        return order_value(security, value_to_order, style=order_style)
    else:
        return order_value(security, value_to_order)

def check_if_etf_positions_are_held(context):
    # If you currently hold positions in any of the securites
    # found in context.assets, we will not be trading on
    # the first day
    for stock in context.assets:
        if stock in context.portfolio.positions:
            return True
    return False

def first_trade(context, data):
    # If it's the very first day of this algorithm, equally
    # weight our portfolio in our ETFs. If unsettled cash
    # currently 
    if context.first_trade and not \
      do_unsettled_funds_exist(context):
        # If we already hold assets from context.assets
        # on the first trade date, assume that we've already
        # traded and don't try and make a trade
        if check_if_etf_positions_are_held(context):
            log.info("Already hold context.asset positions. Skipping"
                     " first trade.")
        else:
            log.info("First day of trading, going long on our assets")
            for security in context.assets:
                if security in data:
                    o_id = order_for_robinhood(context, security,
                                               context.weight,
                                               LimitOrder(data[security].price))
                    if o_id:
                        log.info("Ordering %s shares of %s" %
                                 (get_order(o_id).amount,
                                  security.symbol))
        context.first_trade = False

# Calculate the new exposures for each asset.
def calculate_exposure(context, data):    
    # Let's create two collections of assets: stocks that we
    # need to sell, 
    # and stocks that we need to buy.
    context.reduce_exposure = []
    context.increase_exposure = []
    
    # If cash is not settled. Set the reduce and increase
    # exposure lists to empty lists so we don't trade.
    if do_unsettled_funds_exist(context):
        log.info("Cash not settled")
        return
    
    # Get price history for calculating the moving average.
    prices = history(context.lookback, "1d", "price")
    
    # Loop through our assets and compute each ones new
    # exposure.    
    log.info("Calculating exposure for assets")
    for security in context.assets:        
        
        # Here we check whether or not the latest month's
        # price is greater or less than the entire lookback
        # period
        latest_months_price = prices[security][
            -context.fast_lookback:].mean()
        moving_average_rule = prices[security].mean()
        
        # If latest month's price is greater than the
        # lookback, add the security to the increase_exposure
        # list
        if latest_months_price > moving_average_rule and \
          context.portfolio.positions[security].amount == 0:
            log.info("Adding security %s to the "
                     "increase_exposure list with latest month's"
                     " price at %s and lookback at %s" %
                     (security.symbol, latest_months_price,
                      moving_average_rule))
            context.increase_exposure.append(security)
        # If latest month's price is less than the lookback,
        # add the security to the reduce_exposure list
        elif latest_months_price < moving_average_rule and \
          context.portfolio.positions[security].amount > 0:
            context.reduce_exposure.append(security)
            log.info("Adding security %s to the "
                     "reduce_exposure list with latest month's"
                     " price at %s and lookback at %s" %
                     (security.symbol, latest_months_price,
                      moving_average_rule))
            
    
# Closes current positions. We need to have a separate
# function for this so that cash has time to settle before
# we add new positions.
def close_positions(context, data):
    log.info("Attempting to reduce exposure in %s positions"
             % len(context.reduce_exposure))
    for security in context.reduce_exposure:
        if security in data:
            o_id = order_for_robinhood(context, security, 0.0,
                                       LimitOrder(data[security].price))
            log.info("Ordering %s shares of %s" %
                     (get_order(o_id).amount, security.symbol))
    
    
# Opens new positions. Again this is a separate function
# so that we only buy when we have the available cash.
def open_new_positions(context, data):
    if len(context.increase_exposure) > 0:
        log.info("Attempting to increase exposure in %s "
                 "positions" % len(context.increase_exposure))
    else:
        log.info("No securities matched our exposure positions,"
                 "not trading for this time.")
    for security in context.increase_exposure:
        if security in data:
            o_id = order_for_robinhood(context,
                                       security,
                                       context.weight,
                                       LimitOrder(data[security].price))
            log.info("Ordering %s shares of %s" %
                     (get_order(o_id).amount, security.symbol))

# The handle_data function is run every bar. In this case we'll 
# use this function to plot our leverage over time.
def handle_data(context, data):
    record(leverage=context.account.leverage)
