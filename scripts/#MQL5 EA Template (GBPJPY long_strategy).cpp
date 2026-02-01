#MQL5 EA Template (GBPJPY long_strategy)

//+------------------------------------------------------------------+
//| Expert Advisor: GBPJPY_LongBot                                   |
//| Purpose: Trend-following long strategy for GBP/JPY               |
//| Author: Winston (Scaffolded by Copilot)                          |
//+------------------------------------------------------------------+
#property strict

// Input parameters
input int FastEMA = 20;
input int SlowEMA = 50;
input int RSIPeriod = 14;
input double RSIThreshold = 55.0;
input double LotSize = 0.1;
input double StopLossPips = 50;
input double TakeProfitPips = 100;

// Function to calculate EMA
double EMA(int period, int shift) {
   return iMA(Symbol(), PERIOD_M15, period, 0, MODE_EMA, PRICE_CLOSE, shift);
}

// Function to calculate RSI
double RSI(int period, int shift) {
   return iRSI(Symbol(), PERIOD_M15, period, PRICE_CLOSE, shift);
}

//+------------------------------------------------------------------+
//| Expert initialization                                            |
//+------------------------------------------------------------------+
int OnInit() {
   Print("GBPJPY_LongBot initialized.");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
   datetime currentTime = TimeCurrent();
   int hour = TimeHour(currentTime);

   // Trade only during London/New York overlap (12:00–16:00 GMT)
   if(hour >= 12 && hour <= 16) {
      double fastEMA = EMA(FastEMA, 0);
      double slowEMA = EMA(SlowEMA, 0);
      double rsiValue = RSI(RSIPeriod, 0);

      // Check for bullish conditions
      if(fastEMA > slowEMA && rsiValue > RSIThreshold) {
         // Calculate price levels
         double ask = NormalizeDouble(Ask, _Digits);
         double sl = NormalizeDouble(ask - StopLossPips * _Point, _Digits);
         double tp = NormalizeDouble(ask + TakeProfitPips * _Point, _Digits);

         // Check if no open positions
         if(PositionsTotal() == 0) {
            // Place buy order
            MqlTradeRequest request;
            MqlTradeResult result;
            ZeroMemory(request);
            ZeroMemory(result);

            request.action = TRADE_ACTION_DEAL;
            request.symbol = Symbol();
            request.volume = LotSize;
            request.type = ORDER_TYPE_BUY;
            request.price = ask;
            request.sl = sl;
            request.tp = tp;
            request.deviation = 10;
            request.magic = 123456;

            if(!OrderSend(request, result)) {
               Print("OrderSend failed: ", result.retcode);
            } else {
               Print("Buy order placed at ", ask, " SL: ", sl, " TP: ", tp);
            }
         }
      }
   }
}