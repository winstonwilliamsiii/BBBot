//+------------------------------------------------------------------+
//| Bentley Bot - Core Library                                       |
//| Version: 1.0.0                                                   |
//| Contains: Utilities, time filters, and helper functions          |
//+------------------------------------------------------------------+

#pragma once

//+------------------------------------------------------------------+
//| BentleyBot Class                                                 |
//+------------------------------------------------------------------+
class BentleyBot
  {
private:
   datetime last_trade_time;
   int      trade_cooldown_seconds;

public:
   //--- Constructor
   BentleyBot() : last_trade_time(0), trade_cooldown_seconds(300) {}

   //--- Check if current time is within trading hours (UTC)
   bool IsWithinTradingHours(int start_hour, int end_hour)
     {
      int current_hour = TimeHour(TimeCurrent());
      return (current_hour >= start_hour && current_hour < end_hour);
     }

   //--- Check day of week filter
   bool IsValidTradingDay()
     {
      int day_of_week = DayOfWeek();
      // Filter out weekends (Saturday=6, Sunday=0)
      return (day_of_week != 0 && day_of_week != 6);
     }

   //--- Calculate Profit/Loss percentage
   double CalculateProfitPercent(double entry, double current, bool is_long)
     {
      if(entry == 0)
        return 0;
      
      double change = (current - entry) / entry * 100;
      return is_long ? change : -change;
     }

   //--- Check if price is near resistance level
   bool CheckResistanceRejection(string symbol, ENUM_TIMEFRAMES tf, int bars = 20)
     {
      double high = iHigh(symbol, tf, 0);
      double prev_high = iHigh(symbol, tf, 1);
      
      // Price touches resistance but closes below midpoint
      return (high > prev_high && Close[0] < (high + iLow(symbol, tf, 0)) / 2);
     }

   //--- Check if price is near support level
   bool CheckSupportBounce(string symbol, ENUM_TIMEFRAMES tf, int bars = 20)
     {
      double low = iLow(symbol, tf, 0);
      double prev_low = iLow(symbol, tf, 1);
      
      // Price touches support but closes above midpoint
      return (low < prev_low && Close[0] > (iHigh(symbol, tf, 0) + low) / 2);
     }

   //--- Apply trade cooldown to prevent over-trading
   bool CanExecuteTrade()
     {
      if(TimeCurrent() - last_trade_time >= trade_cooldown_seconds)
        {
         last_trade_time = TimeCurrent();
         return true;
        }
      return false;
     }

   //--- Calculate Risk-Reward Ratio
   double CalculateRiskRewardRatio(double entry, double sl, double tp)
     {
      double risk = MathAbs(entry - sl);
      double reward = MathAbs(tp - entry);
      
      if(risk == 0)
        return 0;
      
      return reward / risk;
     }

   //--- Validate Risk-Reward Ratio
   bool ValidateRiskRewardRatio(double rr_ratio, double min_ratio = 1.5)
     {
      return (rr_ratio >= min_ratio);
     }

   //--- Get volatility percentile
   double GetVolatilityPercentile(int atr_handle, double atr_current, int period = 20)
     {
      if(atr_handle == INVALID_HANDLE)
        return 0;
      
      double atr_array[];
      if(CopyBuffer(atr_handle, 0, 0, period, atr_array) != period)
        return 0;
      
      double min_atr = atr_array[0];
      double max_atr = atr_array[0];
      
      for(int i = 1; i < period; i++)
        {
         if(atr_array[i] < min_atr) min_atr = atr_array[i];
         if(atr_array[i] > max_atr) max_atr = atr_array[i];
        }
      
      if(max_atr == min_atr)
        return 50;
      
      return ((atr_current - min_atr) / (max_atr - min_atr)) * 100;
     }

   //--- Log trade information
   void LogTrade(string action, string symbol, double price, double sl, double tp, double lot_size)
     {
      string log_message = StringFormat(
         "[%s] %s | Symbol: %s | Price: %.5f | SL: %.5f | TP: %.5f | Lot: %.2f",
         TimeToString(TimeCurrent()),
         action,
         symbol,
         price,
         sl,
         tp,
         lot_size
      );
      Print(log_message);
      Print("Timestamp: ", TimeCurrent());
     }
  };
