//+------------------------------------------------------------------+
//| Bentley Bot - XAU/USD (Gold) EA                                  |
//| Version: 1.0.0                                                   |
//| Purpose: Automated trading for Gold (XAU/USD)                    |
//| Strategy: Volatility-based entries with trend confirmation       |
//+------------------------------------------------------------------+

#property copyright "Bentley Bot"
#property link "https://github.com/winstonwilliamsiii/BBBot"
#property version "1.00"
#property strict

#include <Trade\Trade.mqh>
#include "..\\libraries\\BentleyBot.mqh"
#include "..\\indicators\\CustomIndicators.mqh"

//--- Input Parameters
input string  Symbol_Pair             = "XAUUSD";           // Trading pair (Gold)
input ENUM_TIMEFRAMES  TimeFrame       = PERIOD_H1;         // Timeframe
input bool    Enable_Long_Strategy     = true;              // Enable long trades
input bool    Enable_Short_Strategy    = true;              // Enable short trades
input double  Risk_Percent             = 2.0;               // Risk per trade (%)
input int     StopLoss_Pips            = 100;               // Stop loss distance (pips)
input int     TakeProfit_Pips          = 200;               // Take profit distance (pips)
input int     Max_Trades               = 2;                 // Max simultaneous trades
input bool    Use_ATR_Filter           = true;              // Use ATR for volatility
input int     ATR_Period               = 14;                // ATR period
input double  ATR_Multiplier           = 1.5;               // ATR multiplier for stops

//--- Global Variables
CTrade                   trade;                              // Trade object
BentleyBot               bot;                                // Bot utilities
CCustomIndicators        indicators;                         // Indicator calculations
int                      atr_handle;                         // ATR handle
int                      bbands_handle;                      // Bollinger Bands handle
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
   if(!trade.SetExpertMagicNumber(789456))
     {
      Print("ERROR: Failed to set magic number");
      return(INIT_FAILED);
     }

   //--- Create indicators
   atr_handle = iATR(Symbol(), TimeFrame, ATR_Period);
   bbands_handle = iBands(Symbol(), TimeFrame, 20, 2, 0, PRICE_CLOSE);

   if(atr_handle == INVALID_HANDLE || bbands_handle == INVALID_HANDLE)
     {
      Print("ERROR: Failed to create indicators");
      return(INIT_FAILED);
     }

   Print("Gold EA Initialized Successfully - XAU/USD TF: ", Period());
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

   //--- Check max trades limit
   if(CountOpenTrades() >= Max_Trades)
     {
      return;
     }

   //--- Get ATR for dynamic stops
   double atr = GetIndicatorValue(atr_handle, 0);
   if(atr <= 0)
     {
      return;
     }

   //--- Get Bollinger Bands values
   double bb_upper = GetIndicatorValue(bbands_handle, 1);
   double bb_lower = GetIndicatorValue(bbands_handle, 2);
   double bb_middle = GetIndicatorValue(bbands_handle, 0);

   if(bb_upper == 0 || bb_lower == 0 || bb_middle == 0)
     {
      return;
     }

   //--- Long Strategy: Price bounce from lower band
   if(Enable_Long_Strategy && bid <= bb_lower)
     {
      double volatility = atr * ATR_Multiplier;
      double sl = bid - volatility;
      double tp = bid + (volatility * 2);

      ExecuteLongTrade(ask, sl, tp);
     }

   //--- Short Strategy: Price rejection from upper band
   if(Enable_Short_Strategy && bid >= bb_upper)
     {
      double volatility = atr * ATR_Multiplier;
      double sl = bid + volatility;
      double tp = bid - (volatility * 2);

      ExecuteShortTrade(bid, sl, tp);
     }

   //--- Manage open trades
   ManageOpenTrades();
  }

//+------------------------------------------------------------------+
//| Execute Long Trade                                               |
//+------------------------------------------------------------------+
void ExecuteLongTrade(double entry_price, double sl, double tp)
  {
   double lot_size = CalculateLotSize(entry_price, sl);

   if(lot_size <= 0)
     {
      Print("ERROR: Invalid lot size");
      return;
     }

   //--- Send buy order
   if(trade.Buy(lot_size, Symbol_Pair, entry_price, sl, tp, "BentleyBot Gold Long"))
     {
      Print("GOLD BUY Order Placed: ", entry_price, " SL: ", sl, " TP: ", tp);
     }
   else
     {
      Print("ERROR: Failed to place BUY order - ", trade.ResultRetcode());
     }
  }

//+------------------------------------------------------------------+
//| Execute Short Trade                                              |
//+------------------------------------------------------------------+
void ExecuteShortTrade(double entry_price, double sl, double tp)
  {
   double lot_size = CalculateLotSize(entry_price, sl);

   if(lot_size <= 0)
     {
      Print("ERROR: Invalid lot size");
      return;
     }

   //--- Send sell order
   if(trade.Sell(lot_size, Symbol_Pair, entry_price, sl, tp, "BentleyBot Gold Short"))
     {
      Print("GOLD SELL Order Placed: ", entry_price, " SL: ", sl, " TP: ", tp);
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

         //--- Volatility-based trailing stop
         double atr = GetIndicatorValue(atr_handle, 0);
         if(atr > 0)
           {
            double new_sl = (pos_type == POSITION_TYPE_BUY) ? 
                           pos_open + (atr * 0.5) : 
                           pos_open - (atr * 0.5);
            
            if((pos_type == POSITION_TYPE_BUY && new_sl > pos_sl) ||
               (pos_type == POSITION_TYPE_SELL && new_sl < pos_sl))
              {
               trade.PositionModify(PositionGetTicket(i), new_sl, pos_tp);
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   //--- Release indicator handles
   if(atr_handle != INVALID_HANDLE)
     {
      IndicatorRelease(atr_handle);
     }
   if(bbands_handle != INVALID_HANDLE)
     {
      IndicatorRelease(bbands_handle);
     }

   Print("Gold EA Deinitialized");
  }
