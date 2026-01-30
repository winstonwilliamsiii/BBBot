//+------------------------------------------------------------------+
//| Custom Indicators Library                                        |
//| Version: 1.0.0                                                   |
//| Contains: Indicator calculations and helpers                     |
//+------------------------------------------------------------------+

#pragma once

//+------------------------------------------------------------------+
//| CCustomIndicators Class                                          |
//+------------------------------------------------------------------+
class CCustomIndicators
  {
public:
   //--- Calculate Simple Moving Average
   static double SMA(int handle, int shift = 0)
     {
      double buffer[];
      if(CopyBuffer(handle, 0, shift, 1, buffer) == 1)
        return buffer[0];
      return 0;
     }

   //--- Calculate Exponential Moving Average
   static double EMA(int handle, int shift = 0)
     {
      double buffer[];
      if(CopyBuffer(handle, 0, shift, 1, buffer) == 1)
        return buffer[0];
      return 0;
     }

   //--- Calculate RSI
   static double RSI(int handle, int shift = 0)
     {
      double buffer[];
      if(CopyBuffer(handle, 0, shift, 1, buffer) == 1)
        return buffer[0];
      return 0;
     }

   //--- Calculate ATR (Average True Range)
   static double ATR(int handle, int shift = 0)
     {
      double buffer[];
      if(CopyBuffer(handle, 0, shift, 1, buffer) == 1)
        return buffer[0];
      return 0;
     }

   //--- Calculate MACD
   static bool MACD(int handle, int shift, double& macd_line, double& signal_line, double& histogram)
     {
      double macd_buffer[], signal_buffer[], hist_buffer[];
      
      if(CopyBuffer(handle, 0, shift, 1, macd_buffer) != 1 ||
         CopyBuffer(handle, 1, shift, 1, signal_buffer) != 1 ||
         CopyBuffer(handle, 2, shift, 1, hist_buffer) != 1)
        return false;
      
      macd_line = macd_buffer[0];
      signal_line = signal_buffer[0];
      histogram = hist_buffer[0];
      
      return true;
     }

   //--- Calculate Bollinger Bands
   static bool BollingerBands(int handle, int shift, 
                              double& upper, double& middle, double& lower)
     {
      double upper_buffer[], middle_buffer[], lower_buffer[];
      
      if(CopyBuffer(handle, 1, shift, 1, upper_buffer) != 1 ||
         CopyBuffer(handle, 0, shift, 1, middle_buffer) != 1 ||
         CopyBuffer(handle, 2, shift, 1, lower_buffer) != 1)
        return false;
      
      upper = upper_buffer[0];
      middle = middle_buffer[0];
      lower = lower_buffer[0];
      
      return true;
     }

   //--- Calculate Stochastic Oscillator
   static bool Stochastic(int handle, int shift, double& k_line, double& d_line)
     {
      double k_buffer[], d_buffer[];
      
      if(CopyBuffer(handle, 0, shift, 1, k_buffer) != 1 ||
         CopyBuffer(handle, 1, shift, 1, d_buffer) != 1)
        return false;
      
      k_line = k_buffer[0];
      d_line = d_buffer[0];
      
      return true;
     }

   //--- Check for Golden Cross (EMA20 > EMA50)
   static bool GoldenCross(double ema20_curr, double ema50_curr, 
                           double ema20_prev, double ema50_prev)
     {
      return (ema20_prev <= ema50_prev && ema20_curr > ema50_curr);
     }

   //--- Check for Death Cross (EMA20 < EMA50)
   static bool DeathCross(double ema20_curr, double ema50_curr, 
                          double ema20_prev, double ema50_prev)
     {
      return (ema20_prev >= ema50_prev && ema20_curr < ema50_curr);
     }

   //--- Calculate Price Action Volatility
   static double CalculateVolatility(double high, double low, double close, double period = 20)
     {
      double range = high - low;
      if(close == 0)
        return 0;
      return (range / close) * 100;
     }

   //--- Detect Divergence
   static bool DetectBullishDivergence(double rsi_current, double rsi_previous,
                                       double price_current, double price_previous)
     {
      return (price_current < price_previous && rsi_current > rsi_previous);
     }

   //--- Normalize Indicator (0-100)
   static double Normalize(double value, double min_val, double max_val)
     {
      if(max_val == min_val)
        return 0;
      return ((value - min_val) / (max_val - min_val)) * 100;
     }
  };
