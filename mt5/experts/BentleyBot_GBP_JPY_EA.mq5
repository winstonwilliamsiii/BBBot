//+------------------------------------------------------------------+
//| Bentley Bot - GBP/JPY Forex EA                                   |
//| Version: 1.0.0                                                   |
//| Purpose: Automated trading for GBP/JPY pair                      |
//| Strategy: EMA Crossover + RSI Confirmation                       |
//+------------------------------------------------------------------+

#property copyright "Bentley Bot"
#property link "https://github.com/winstonwilliamsiii/BBBot"
#property version "1.00"
#property strict

#include <Trade\Trade.mqh>
#include "..\\libraries\\BentleyBot.mqh"
#include "..\\indicators\\CustomIndicators.mqh"

//--- Input Parameters
input string  Symbol_Pair             = "GBPJPY";           // Trading pair
input ENUM_TIMEFRAMES  TimeFrame       = PERIOD_H1;         // Timeframe
input bool    Enable_Long_Strategy     = true;              // Enable long trades
input bool    Enable_Short_Strategy    = false;             // Enable short trades
input double  Risk_Percent             = 2.0;               // Risk per trade (%)
input int     StopLoss_Pips            = 50;                // Stop loss distance (pips)
input int     TakeProfit_Pips          = 100;               // Take profit distance (pips)
input int     Max_Trades               = 3;                 // Max simultaneous trades
input bool    Use_Time_Filter          = true;              // Filter by trading hours
input int     Start_Hour               = 12;                // Start trading hour (UTC)
input int     End_Hour                 = 16;                // End trading hour (UTC)
input bool    Use_RSI_Filter           = true;              // Use RSI confirmation
input int     RSI_Overbought           = 70;                // RSI overbought level
input int     RSI_Oversold             = 30;                // RSI oversold level

//--- Global Variables
CTrade                   trade;                              // Trade object
BentleyBot               bot;                                // Bot utilities
CCustomIndicators        indicators;                         // Indicator calculations
int                      ema20_handle;                       // EMA 20 handle
int                      ema50_handle;                       // EMA 50 handle
int                      rsi_handle;                         // RSI handle
double                   bid, ask;                           // Current prices

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   //--- Validate inputs
   if(StopLoss_Pips <= 0 || TakeProfit_Pips <= 0)
     {
      Print("ERROR: Invalid SL/TP values");
      return(INIT_PARAMETERS_INCORRECT);
     }

   if(Max_Trades <= 0 || Risk_Percent <= 0 || Risk_Percent > 10)
     {
      Print("ERROR: Invalid risk parameters");
      return(INIT_PARAMETERS_INCORRECT);
     }

   //--- Initialize trade object
   if(!trade.SetExpertMagicNumber(123456))
     {
      Print("ERROR: Failed to set magic number");
      return(INIT_FAILED);
     }

   //--- Create indicators
   ema20_handle = iMA(Symbol(), TimeFrame, 20, 0, MODE_EMA, PRICE_CLOSE);
   ema50_handle = iMA(Symbol(), TimeFrame, 50, 0, MODE_EMA, PRICE_CLOSE);
   rsi_handle = iRSI(Symbol(), TimeFrame, 14, PRICE_CLOSE);

   if(ema20_handle == INVALID_HANDLE || 
      ema50_handle == INVALID_HANDLE || 
      rsi_handle == INVALID_HANDLE)
     {
      Print("ERROR: Failed to create indicators");
      return(INIT_FAILED);
     }

   Print("EA Initialized Successfully - ", Symbol_Pair, " TF: ", Period());
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   //--- Prevent action on first tick
   if(Bars(Symbol(), TimeFrame) < 50)
     {
      return;
     }

   //--- Get current prices
   bid = SymbolInfoDouble(Symbol_Pair, SYMBOL_BID);
   ask = SymbolInfoDouble(Symbol_Pair, SYMBOL_ASK);

   if(bid == 0 || ask == 0)
     {
      Print("ERROR: Invalid price data");
      return;
     }

   //--- Check time filter
   if(Use_Time_Filter && !bot.IsWithinTradingHours(Start_Hour, End_Hour))
     {
      return;
     }

   //--- Check max trades limit
   if(CountOpenTrades() >= Max_Trades)
     {
      return;
     }

   //--- Get indicator values
   double ema20 = GetIndicatorValue(ema20_handle, 0);
   double ema50 = GetIndicatorValue(ema50_handle, 0);
   double rsi = GetIndicatorValue(rsi_handle, 0);

   if(ema20 == 0 || ema50 == 0 || rsi == 0)
     {
      return;
     }

   //--- Long Strategy: EMA20 > EMA50 + RSI Confirmation
   if(Enable_Long_Strategy && ema20 > ema50)
     {
      if(!Use_RSI_Filter || rsi < RSI_Overbought)
        {
         if(rsi > 50)  // Additional confirmation
           {
            ExecuteLongTrade(ask);
           }
        }
     }

   //--- Short Strategy: EMA20 < EMA50 + RSI Rejection at Resistance
   if(Enable_Short_Strategy && ema20 < ema50)
     {
      if(!Use_RSI_Filter || rsi > RSI_Overbought)
        {
         if(bot.CheckResistanceRejection(Symbol_Pair, TimeFrame))
           {
            ExecuteShortTrade(bid);
           }
        }
     }

   //--- Manage open trades
   ManageOpenTrades();
  }

//+------------------------------------------------------------------+
//| Execute Long Trade                                               |
//+------------------------------------------------------------------+
void ExecuteLongTrade(double entry_price)
  {
   double sl = entry_price - (StopLoss_Pips * Point());
   double tp = entry_price + (TakeProfit_Pips * Point());
   double lot_size = CalculateLotSize(entry_price, sl);

   if(lot_size <= 0)
     {
      Print("ERROR: Invalid lot size");
      return;
     }

   //--- Send buy order
   if(trade.Buy(lot_size, Symbol_Pair, entry_price, sl, tp, "BentleyBot Long"))
     {
      Print("BUY Order Placed: ", entry_price, " SL: ", sl, " TP: ", tp);
     }
   else
     {
      Print("ERROR: Failed to place BUY order - ", trade.ResultRetcode());
     }
  }

//+------------------------------------------------------------------+
//| Execute Short Trade                                              |
//+------------------------------------------------------------------+
void ExecuteShortTrade(double entry_price)
  {
   double sl = entry_price + (StopLoss_Pips * Point());
   double tp = entry_price - (TakeProfit_Pips * Point());
   double lot_size = CalculateLotSize(entry_price, sl);

   if(lot_size <= 0)
     {
      Print("ERROR: Invalid lot size");
      return;
     }

   //--- Send sell order
   if(trade.Sell(lot_size, Symbol_Pair, entry_price, sl, tp, "BentleyBot Short"))
     {
      Print("SELL Order Placed: ", entry_price, " SL: ", sl, " TP: ", tp);
     }
   else
     {
      Print("ERROR: Failed to place SELL order - ", trade.ResultRetcode());
     }
  }

//+------------------------------------------------------------------+
//| Calculate Lot Size based on Risk                                 |
//+------------------------------------------------------------------+
double CalculateLotSize(double entry, double stop_loss)
  {
   double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = account_balance * (Risk_Percent / 100);
   double pip_value = SymbolInfoDouble(Symbol_Pair, SYMBOL_TRADE_TICK_VALUE);
   double distance_pips = MathAbs(entry - stop_loss) / Point();

   if(distance_pips <= 0)
     {
      return 0;
     }

   double lot_size = risk_amount / (distance_pips * pip_value);
   double min_lot = SymbolInfoDouble(Symbol_Pair, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(Symbol_Pair, SYMBOL_VOLUME_MAX);

   lot_size = MathMax(min_lot, MathMin(lot_size, max_lot));

   return lot_size;
  }

//+------------------------------------------------------------------+
//| Count Open Trades                                                |
//+------------------------------------------------------------------+
int CountOpenTrades()
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(PositionGetSymbol(i) == Symbol_Pair)
        {
         count++;
        }
     }
   return count;
  }

//+------------------------------------------------------------------+
//| Get Indicator Value                                              |
//+------------------------------------------------------------------+
double GetIndicatorValue(int handle, int buffer)
  {
   double value[];
   if(CopyBuffer(handle, buffer, 0, 1, value) == 1)
     {
      return value[0];
     }
   return 0;
  }

//+------------------------------------------------------------------+
//| Manage Open Trades                                               |
//+------------------------------------------------------------------+
void ManageOpenTrades()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(PositionGetSymbol(i) == Symbol_Pair && 
         PositionGetInteger(POSITION_MAGIC) == trade.RequestMagic())
        {
         long pos_type = PositionGetInteger(POSITION_TYPE);
         double pos_open = PositionGetDouble(POSITION_PRICE_OPEN);
         double pos_sl = PositionGetDouble(POSITION_SL);
         double pos_tp = PositionGetDouble(POSITION_TP);

         //--- Trailing stop implementation can go here
         //--- Example: Move SL to breakeven if price moves favorably
        }
     }
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   //--- Release indicator handles
   if(ema20_handle != INVALID_HANDLE)
     {
      IndicatorRelease(ema20_handle);
     }
   if(ema50_handle != INVALID_HANDLE)
     {
      IndicatorRelease(ema50_handle);
     }
   if(rsi_handle != INVALID_HANDLE)
     {
      IndicatorRelease(rsi_handle);
     }

   Print("EA Deinitialized");
  }
