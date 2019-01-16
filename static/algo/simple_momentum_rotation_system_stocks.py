####################################################################
# A Simple Momentum Rotation System for Stocks
# Anthony FJ Garner, 2015
#####################################################################
from quantopian.algorithm import attach_pipeline, pipeline_output  
from quantopian.pipeline import Pipeline  
from quantopian.pipeline import CustomFactor  
from quantopian.pipeline.data.builtin import USEquityPricing  
from quantopian.pipeline.data import morningstar 
import numpy as np
from collections import defaultdict
      
class momentum_factor_1(CustomFactor):    
   inputs = [USEquityPricing.close]   
   window_length = 20  
     
   def compute(self, today, assets, out, close):      
     out[:] = close[-1]/close[0]      
   
class momentum_factor_2(CustomFactor):    
   inputs = [USEquityPricing.close]   
   window_length = 60  
     
   def compute(self, today, assets, out, close):      
     out[:] = close[-1]/close[0]   
   
class momentum_factor_3(CustomFactor):    
   inputs = [USEquityPricing.close]   
   window_length = 125  
     
   def compute(self, today, assets, out, close):      
     out[:] = close[-1]/close[0]  
   
class momentum_factor_4(CustomFactor):    
   inputs = [USEquityPricing.close]   
   window_length = 252  
     
   def compute(self, today, assets, out, close):      
     out[:] = close[-1]/close[0]  
   
class market_cap(CustomFactor):    
   inputs = [USEquityPricing.close, morningstar.valuation.shares_outstanding]   
   window_length = 1  
     
   def compute(self, today, assets, out, close, shares):      
     out[:] = close[-1] * shares[-1]        
        
class efficiency_ratio(CustomFactor):    
   inputs = [USEquityPricing.close, USEquityPricing.high, USEquityPricing.low]   
   window_length = 252
     
   def compute(self, today, assets, out, close, high, low):
       lb = self.window_length
       e_r = np.zeros(len(assets), dtype=np.float64)
       a=np.array(([high[1:(lb):1]-low[1:(lb):1],abs(high[1:(lb):1]-close[0:(lb-1):1]),abs(low[1:(lb):1]-close[0:(lb-1):1])]))      
       b=a.T.max(axis=1)
       c=b.sum(axis=1)
       e_r=abs(close[-1]-close[0]) /c  
       out[:] = e_r
        
def initialize(context):  
    set_commission(commission.PerShare(cost=0.005, min_trade_cost=1.00))
    schedule_function(func=rebalance, date_rule=date_rules.month_start(days_offset=5), time_rule=time_rules.market_open(), half_days=True)  
    schedule_function(close_orders,date_rule=date_rules.week_end(),time_rule=time_rules.market_close()) 
    set_do_not_order_list(security_lists.leveraged_etf_list)
    context.acc_leverage = 1.00 
    context.holdings =10
    context.profit_taking_factor = 0.01
    context.profit_target={}
    context.profit_taken={}
    context.entry_date={}
    context.stop_pct = 0.75
    context.stop_price = defaultdict(lambda:0)
       
    pipe = Pipeline()  
    attach_pipeline(pipe, 'ranked_stocks')  
     
    factor1 = momentum_factor_1()  
    pipe.add(factor1, 'factor_1')   
    factor2 = momentum_factor_2()  
    pipe.add(factor2, 'factor_2')  
    factor3 = momentum_factor_3()  
    pipe.add(factor3, 'factor_3')  
    factor4 = momentum_factor_4()  
    pipe.add(factor4, 'factor_4') 
    factor5=efficiency_ratio()
    pipe.add(factor5, 'factor_5')
        
        
    mkt_screen = market_cap()    
    stocks = mkt_screen.top(3000) 
    factor_5_filter = factor5 > 0.031
    total_filter = (stocks& factor_5_filter)
    pipe.set_screen(total_filter)  
     
        
    factor1_rank = factor1.rank(mask=total_filter, ascending=False)  
    pipe.add(factor1_rank, 'f1_rank')  
    factor2_rank = factor2.rank(mask=total_filter, ascending=False)  
    pipe.add(factor2_rank, 'f2_rank')  
    factor3_rank = factor3.rank(mask=total_filter, ascending=False)   
    pipe.add(factor3_rank, 'f3_rank')  
    factor4_rank = factor4.rank(mask=total_filter, ascending=False)  
    pipe.add(factor4_rank, 'f4_rank')  
   
    combo_raw = (factor1_rank+factor2_rank+factor3_rank+factor4_rank)/4  
    pipe.add(combo_raw, 'combo_raw')   
    pipe.add(combo_raw.rank(mask=total_filter), 'combo_rank')       
         
def before_trading_start(context, data):  
    context.output = pipeline_output('ranked_stocks')  
   
    ranked_stocks = context.output.fillna(0)  
    ranked_stocks = context.output[context.output.factor_1 > 0]  
    ranked_stocks = context.output[context.output.factor_2 > 0]  
    ranked_stocks = context.output[context.output.factor_3 > 0]  
    ranked_stocks = context.output[context.output.factor_4 > 0] 
    ranked_stocks = context.output[context.output.factor_5 > 0] 
        
    context.stock_list = ranked_stocks.sort(['combo_rank'], ascending=True).iloc[:context.holdings]  
     
    update_universe(context.stock_list.index)   
            
def handle_data(context, data):   
    for stock in context.portfolio.positions:       
           price = data[stock].price
           context.stop_price[stock] = max(context.stop_price[stock], context.stop_pct * price)
    for stock in context.portfolio.positions:
       if data[stock].price < context.stop_price[stock]:
           order_target(stock, 0)
           context.stop_price[stock] = 0
        
    current_date = get_datetime()
    record(leverage=context.account.leverage, positions=len(context.portfolio.positions))    
    for stock in context.portfolio.positions:  
       if (stock.end_date - current_date).days < 2:  
        order_target_percent(stock, 0.0)       
        print "Long List"  
        log.info("\n" + str(context.stock_list.sort(['combo_rank'], ascending=True).head(context.holdings)))
       
       if data[stock].close_price > context.profit_target[stock]:
        context.profit_target[stock] = data[stock].close_price*1.25
        profit_taking_amount = context.portfolio.positions[stock].amount * context.profit_taking_factor
        order_target(stock, profit_taking_amount) 
           
def rebalance(context,data):    
   weight = context.acc_leverage / len(context.stock_list)    
   for stock in context.stock_list.index:  
     if stock in data: 
      if context.stock_list.factor_1[stock]>1: 
        if (stock.end_date - get_datetime()).days > 35: 
            if stock not in security_lists.leveraged_etf_list:
              order_target_percent(stock, weight)  
              context.profit_target[stock] = data[stock].close_price*1.25
     
   for stock in context.portfolio.positions.iterkeys():  
     if stock not in context.stock_list.index or context.stock_list.factor_1[stock]<=1:  
       order_target(stock, 0)  
         
def close_orders(context, data):  
    orders = get_open_orders()  
    if orders:   
     for o in orders:  
       cancel_order(o)                  

     
    
