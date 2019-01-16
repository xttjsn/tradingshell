####################################################################
# Keller/Butler - Elastic Asset Allocation (EAA)
# Alex, 2015
#####################################################################
# Keller/Butler - Elastic Asset Allocation (EAA)
#
# Source:
#   Wouter J. Keller and Adam Butler
#   "From Flexible Asset Allocations (FAA) to Elastic Asset Allocation (EAA)"
#   December 30, 2014 (v0.90), revised January 16, 2015 (v0.92)
#
# Implementation:
#   Alex (https://www.quantopian.com/users/54190a3694339e5d3a0000af)
#   March 10, 2014 (v0.6)
#
# Additional links:
#   http://papers.ssrn.com/sol3/papers.cfm?abstract_id=2543979
#   http://indexswingtrader.blogspot.com/2015/01/a-primer-on-elastic-asset-allocation.html
#   https://quantstrattrader.wordpress.com/2015/01/03/for-a-new-year-a-new-asset-allocation-system-just-published-in-ssrn/
#
# Known issues:
#   Dividend adjustment requires len(assets) <= 5 (Quantopian Fetcher limit)
#   CAUTION: (slight) look-ahead bias with adjusted EOD price
#
# Version Log:
#   v0.6 - Dividend adjustment via Yahoo data (Thanks to F. Chandelier)
#          Truncating z-score at 0 rather than momentum
#          Add leverage logging
#   v0.5 - initial open-source release

import pandas as pd
import datetime as dt
import math

def initialize(context):
    #
    # Configuration
    #

    # Assets (N=7) from Paper (unadjusted):
    #   SP500, EAFE, EEM, US Tech, Japan Topix, and two bonds: US Gov10y, and US HighYield. Cash = SHY, Bill = SHY
    #context.use_adjusted = False
    #context.active = [sid(8554), sid(22972), sid(24705), sid(19658), sid(14520), sid(23870), sid(33655)]
    #context.cash = sid(23911)
    #context.bill = sid(23911)
    
    # Assets from Index Swing Trader Blog (unadjusted):
    #   $MDY, $IEV, $EEM, $QQQ, $XLV, $IEF and $TLT. Cash = $IEF, Bill = SHY
    #context.use_adjusted = False
    #context.active = [sid(12915), sid(21769), sid(24705), sid(19920), sid(19661), sid(23870), sid(23921)]
    #context.cash = sid(23870)
    #context.bill = sid(23911)
    
    # Custom assets (N=5) (adjusted yahoo data):
    #   VTI, EFA, ICF, TLT, IEF. Cash = IEF, Bill = IEF (!)
    context.use_adjusted = True
    context.active = [sid(22739), sid(22972), sid(22446), sid(23921), sid(23870)]
    context.cash = sid(23870)
    context.bill = sid(23870)
    
    context.leverage = 1.0
    
    # Weights:
    #   [wR, wC, wV, wS, eps]
    #   Golden Offensive EAA: wi ~ zi = (1-ci) * ri^2
    #context.score_weights = (2.0, 1.0, 0.0, 1.0, 1e-6)
    #   Golden Defensive EAA: wi ~ zi = squareroot( ri * (1-ci) )
    context.score_weights = (1.0, 1.0, 0.0, 0.5, 1e-6)
    #   Equal Weighted Return: wi ~ zi = ri ^ eps
    #context.score_weights = (1.0, 0.0, 0.0, 0.0, 1e-6)
    #   Equal Weighted Hedged: wi ~ zi = ( ri * (1-ci) )^eps
    #context.score_weights = (1.0, 1.0, 0.0, 0.0, 1e-6)
    #   Scoring Function Test:
    #context.score_weights = (1.0, 1.0, 1.0, 1.0, 0.0)

    context.assets = set(context.active + [context.cash, context.bill])
    context.alloc = pd.Series([0.0] * len(context.assets), index=context.assets)

    schedule_function(
        reallocate,
        date_rules.month_end(days_offset=0),
        time_rules.market_close(minutes=5)
    )
    
    schedule_function(
        rebalance,
        date_rules.month_end(days_offset=0),
        time_rules.market_close(minutes=5)
    )
    
    #
    # Yahoo fetcher
    # (inspired by F. Chandelier)
    # https://www.quantopian.com/posts/yahoo-and-fetch-comparing-q-and-y-for-12-mth-rolling-return
    #
    if context.use_adjusted:
        start_year = 2002
        end_year = dt.datetime.today().year + 1
        url_template = "http://real-chart.finance.yahoo.com/table.csv?s=%s&a=0&b=1&c=%d&d=0&e=1&f=%d&g=d&ignore=.csv"

        for sym in context.active:
            url = url_template % (sym.symbol, start_year, end_year)
            print "Fetching %s adjusted prices: %s" % (sym.symbol, url)

            fetch_csv(
                url,
                date_column='Date',
                date_format='%Y-%m-%d',
                symbol=sym,
                usecols=['Adj Close'],
                pre_func=fetch_pre,
                post_func=fetch_post
            )


def handle_data(context, data):
    record(leverage = context.portfolio.positions_value / context.portfolio.portfolio_value)

def rebalance(context, data):
    for s in context.alloc.index:
        if s in data:
            order_target_percent(s, context.alloc[s] * context.leverage)

def reallocate(context, data):
    h = make_history(context, data).ix[-280:]
    hm = h.resample('M', how='last')[context.active]
    hb = h.resample('M', how='last')[context.bill]
    ret = hm.pct_change().ix[-12:]
    
    N = len(context.active)
    
    non_cash_assets = list(context.active)
    non_cash_assets.remove(context.cash)
    
    print "***************************************************************"
    
    #
    # Scoring
    #
    # excess return momentum
    mom = (hm.ix[-1] / hm.ix[-2]  - hb.ix[-1] / hb.ix[-2] + \
           hm.ix[-1] / hm.ix[-4]  - hb.ix[-1] / hb.ix[-4] + \
           hm.ix[-1] / hm.ix[-7]  - hb.ix[-1] / hb.ix[-7] + \
           hm.ix[-1] / hm.ix[-13] - hb.ix[-1] / hb.ix[-13]) / 22
    
    # nominal return correlation to equi-weight portfolio
    ew_index = ret.mean(axis=1)
    corr = pd.Series([0.0] * N, index=context.active)
    for s in corr.index:
      corr[s] = ret[s].corr(ew_index)
    
    # nominal return volatility
    vol = ret.std()
    
    #
    # Generalized Momentum
    #
    # wi ~ zi = ( ri^wR * (1-ci)^wC / vi^wV )^wS
    
    wR  = context.score_weights[0]
    wC  = context.score_weights[1]
    wV  = context.score_weights[2]
    wS  = context.score_weights[3]
    eps = context.score_weights[4]
    
    z = ((mom ** wR) * ((1 - corr) ** wC) / (vol ** wV)) ** (wS + eps)
    z[mom < 0.] = 0.0
    
    #
    # Crash Protection
    #
    
    num_neg = z[z <= 0].count()
    cpf = float(num_neg) / N
    print "cpf = %f" % cpf
    
    #
    # Security selection
    #
    # TopN = Min( 1 + roundup( sqrt( N ), rounddown( N / 2 ) )
    top_n = min(math.ceil(N ** 0.5) + 1, N / 2)
    
    #
    # Allocation
    #
    top_z = z.order().index[-top_n:]
    print "top_z = %s" % [i.symbol for i in top_z]
    
    w_z = ((1 - cpf) * z[top_z] / z[top_z].sum(axis=1)).dropna()
    w = pd.Series([0.0] * len(context.assets), index=context.assets)
    for s in w_z.index:
        w[s] = w_z[s]
    w[context.cash] += cpf
    print "Allocation:\n%s" % w
    
    context.alloc = w
    
#
# Quantopian/Yahoo history switch
#
def make_history(context, data):
    if context.use_adjusted:
        df = pd.DataFrame(index=data[context.active[0]]['aclose_hist'].index, columns=context.active)
        for s in context.active:
            df[s] = data[s]['aclose_hist']
        return df
    else:
        return history(300, '1d', 'price')

def fetch_pre(df):
    df = df.rename(columns={'Adj Close': 'aclose'})
    df['aclose_hist'] = pd.Series([[]] * len(df.index), index=df.index)
    return df
    
def fetch_post(df):
    #
    # Workaround for history() not providing access to external fields
    # Populate data[] with past 300 adjusted close prices
    #
    for i in xrange(0, len(df.index)):
        df['aclose_hist'].ix[-i-1] = df['aclose'][-i-300:][:300]
    return df
