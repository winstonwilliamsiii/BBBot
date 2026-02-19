//+------------------------------------------------------------------+
//|                                              RigelForexEA.mq5    |
//|                                  Bentley Budget Bot Team         |
//|                          Multi-Pair Mean Reversion Forex EA       |
//+------------------------------------------------------------------+
#property copyright "Bentley Budget Bot Team"
#property link      "https://github.com/winstonwilliamsiii/BBBot"
#property version   "1.00"
#property description "Multi-pair mean reversion EA with risk management"
#property description "Compatible with Rigel Python bot logic"

//+------------------------------------------------------------------+
//| INCLUDES                                                          |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                  |
//+------------------------------------------------------------------+

// === Trading Pairs ===
input group "===== TRADING PAIRS ====="
input bool   Trade_EURUSD = true;       // Trade EUR/USD
input bool   Trade_GBPUSD = true;       // Trade GBP/USD
input bool   Trade_USDJPY = true;       // Trade USD/JPY
input bool   Trade_USDCHF = true;       // Trade USD/CHF
input bool   Trade_AUDUSD = true;       // Trade AUD/USD
input bool   Trade_NZDUSD = true;       // Trade NZD/USD
input bool   Trade_USDCAD = true;       // Trade USD/CAD

// === Trading Session ===
input group "===== TRADING SESSION ====="
input int    SessionStartHour = 9;      // Session Start Hour (EST)
input int    SessionEndHour = 16;       // Session End Hour (EST)

// === Strategy Parameters ===
input group "===== STRATEGY ====="
input bool   LongStrategy = true;       // Enable Long Positions
input bool   ShortStrategy = true;      // Enable Short Positions

// === Technical Indicators ===
input group "===== INDICATORS ====="
input int    EMA_Fast = 20;             // EMA Fast Period
input int    EMA_Slow = 50;             // EMA Slow Period
input int    RSI_Period = 14;           // RSI Period
input double RSI_Oversold = 45.0;       // RSI Oversold Level
input double RSI_Overbought = 55.0;     // RSI Overbought Level
input int    BB_Period = 20;            // Bollinger Bands Period
input double BB_Deviation = 2.0;        // Bollinger Bands Std Dev
input int    ATR_Period = 14;           // ATR Period

// === Risk Management ===
input group "===== RISK MANAGEMENT ====="
input double RiskPerTrade = 1.0;        // Risk Per Trade (%)
input int    MaxOpenPositions = 3;      // Max Open Positions
input double LiquidityBuffer = 25.0;    // Liquidity Buffer (%)
input double MaxDailyLoss = 5.0;        // Max Daily Loss (%)

// === Stop Loss / Take Profit ===
input group "===== STOP LOSS / TAKE PROFIT ====="
input int    StopLoss_Long = 50;        // Stop Loss - Long (pips)
input int    TakeProfit_Long = 100;     // Take Profit - Long (pips)
input int    StopLoss_Short = 30;       // Stop Loss - Short (pips)
input int    TakeProfit_Short = 60;     // Take Profit - Short (pips)

// === ML Integration ===
input group "===== ML INTEGRATION ====="
input bool   EnableML = false;          // Enable ML Predictions
input double MLConfidenceThreshold = 0.70; // ML Confidence Threshold

// === Safety Controls ===
input group "===== SAFETY ====="
input bool   DryRun = true;             // Dry Run (No Real Orders)
input bool   EnableTrading = false;     // Enable Trading
input int    MagicNumber = 123456;      // Magic Number
input string CommentPrefix = "Rigel";   // Order Comment Prefix

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+

CTrade         trade;
CPositionInfo  positionInfo;
CAccountInfo   accountInfo;

// Trading pairs array
string TradingPairs[];

// Indicator handles
struct IndicatorHandles {
    int ema_fast;
    int ema_slow;
    int rsi;
    int bb;
    int atr;
};

IndicatorHandles Handles[];

// Last trade time tracking (to prevent overtrading)
datetime LastTradeTime[];

// Daily statistics
double DailyStartBalance = 0;
datetime LastDayReset = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("========================================");
    Print("RIGEL FOREX EA INITIALIZATION");
    Print("========================================");
    
    // Set magic number
    trade.SetExpertMagicNumber(MagicNumber);
    
    // Initialize trading pairs array
    InitializeTradingPairs();
    
    // Initialize indicators for each pair
    if(!InitializeIndicators())
    {
        Print("ERROR: Failed to initialize indicators");
        return INIT_FAILED;
    }
    
    // Initialize trade time tracking
    ArrayResize(LastTradeTime, ArraySize(TradingPairs));
    ArrayInitialize(LastTradeTime, 0);
    
    // Set daily balance
    DailyStartBalance = accountInfo.Balance();
    LastDayReset = TimeCurrent();
    
    // Print configuration
    PrintConfiguration();
    
    Print("========================================");
    Print("INITIALIZATION COMPLETE");
    Print("========================================");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("========================================");
    Print("RIGEL FOREX EA SHUTDOWN");
    Print("Reason: ", reason);
    Print("========================================");
    
    // Release indicator handles
    for(int i = 0; i < ArraySize(Handles); i++)
    {
        IndicatorRelease(Handles[i].ema_fast);
        IndicatorRelease(Handles[i].ema_slow);
        IndicatorRelease(Handles[i].rsi);
        IndicatorRelease(Handles[i].bb);
        IndicatorRelease(Handles[i].atr);
    }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if new bar (run once per bar for efficiency)
    static datetime lastBarTime = 0;
    datetime currentBarTime = iTime(_Symbol, PERIOD_H1, 0);
    
    if(currentBarTime == lastBarTime)
        return;
        
    lastBarTime = currentBarTime;
    
    // Check trading session
    if(!IsTradingSession())
    {
        Comment("Outside trading session");
        return;
    }
    
    // Check daily loss limit
    if(!CheckDailyLossLimit())
    {
        Comment("Daily loss limit exceeded");
        return;
    }
    
    // Reset daily stats if new day
    ResetDailyStatsIfNeeded();
    
    // Get risk metrics
    int openPositions = CountOpenPositions();
    double liquidityRatio = CalculateLiquidityRatio();
    
    // Update comment
    Comment(StringFormat("Rigel EA | Positions: %d/%d | Liquidity: %.1f%%",
                        openPositions, MaxOpenPositions, liquidityRatio * 100));
    
    // Scan all pairs for signals
    for(int i = 0; i < ArraySize(TradingPairs); i++)
    {
        string symbol = TradingPairs[i];
        
        // Check if we can trade this pair
        if(!CanOpenNewPosition(openPositions, liquidityRatio))
            continue;
            
        // Rate limiting: min 1 hour between trades per pair
        if(TimeCurrent() - LastTradeTime[i] < 3600)
            continue;
        
        // Analyze pair
        AnalyzeAndTrade(symbol, i);
    }
}

//+------------------------------------------------------------------+
//| Initialize trading pairs array                                   |
//+------------------------------------------------------------------+
void InitializeTradingPairs()
{
    int count = 0;
    
    if(Trade_EURUSD) { ArrayResize(TradingPairs, count + 1); TradingPairs[count++] = "EURUSD"; }
    if(Trade_GBPUSD) { ArrayResize(TradingPairs, count + 1); TradingPairs[count++] = "GBPUSD"; }
    if(Trade_USDJPY) { ArrayResize(TradingPairs, count + 1); TradingPairs[count++] = "USDJPY"; }
    if(Trade_USDCHF) { ArrayResize(TradingPairs, count + 1); TradingPairs[count++] = "USDCHF"; }
    if(Trade_AUDUSD) { ArrayResize(TradingPairs, count + 1); TradingPairs[count++] = "AUDUSD"; }
    if(Trade_NZDUSD) { ArrayResize(TradingPairs, count + 1); TradingPairs[count++] = "NZDUSD"; }
    if(Trade_USDCAD) { ArrayResize(TradingPairs, count + 1); TradingPairs[count++] = "USDCAD"; }
    
    Print("Trading ", count, " pairs: ", ArrayToString(TradingPairs));
}

//+------------------------------------------------------------------+
//| Initialize indicators for all pairs                              |
//+------------------------------------------------------------------+
bool InitializeIndicators()
{
    int pairCount = ArraySize(TradingPairs);
    ArrayResize(Handles, pairCount);
    
    for(int i = 0; i < pairCount; i++)
    {
        string symbol = TradingPairs[i];
        
        Handles[i].ema_fast = iMA(symbol, PERIOD_H1, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
        Handles[i].ema_slow = iMA(symbol, PERIOD_H1, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
        Handles[i].rsi = iRSI(symbol, PERIOD_H1, RSI_Period, PRICE_CLOSE);
        Handles[i].bb = iBands(symbol, PERIOD_H1, BB_Period, 0, BB_Deviation, PRICE_CLOSE);
        Handles[i].atr = iATR(symbol, PERIOD_H1, ATR_Period);
        
        if(Handles[i].ema_fast == INVALID_HANDLE || 
           Handles[i].ema_slow == INVALID_HANDLE ||
           Handles[i].rsi == INVALID_HANDLE ||
           Handles[i].bb == INVALID_HANDLE ||
           Handles[i].atr == INVALID_HANDLE)
        {
            Print("ERROR: Failed to create indicators for ", symbol);
            return false;
        }
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check if current time is within trading session                  |
//+------------------------------------------------------------------+
bool IsTradingSession()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    int currentHour = dt.hour;
    
    return (currentHour >= SessionStartHour && currentHour <= SessionEndHour);
}

//+------------------------------------------------------------------+
//| Check if we can open new position                                |
//+------------------------------------------------------------------+
bool CanOpenNewPosition(int openPositions, double liquidityRatio)
{
    if(openPositions >= MaxOpenPositions)
        return false;
        
    if(liquidityRatio < (LiquidityBuffer / 100.0))
        return false;
        
    return true;
}

//+------------------------------------------------------------------+
//| Count open positions managed by this EA                          |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
    int count = 0;
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(positionInfo.SelectByIndex(i))
        {
            if(positionInfo.Magic() == MagicNumber)
                count++;
        }
    }
    
    return count;
}

//+------------------------------------------------------------------+
//| Calculate liquidity ratio                                        |
//+------------------------------------------------------------------+
double CalculateLiquidityRatio()
{
    double equity = accountInfo.Equity();
    double margin = accountInfo.Margin();
    double freeMargin = accountInfo.FreeMargin();
    
    if(equity <= 0)
        return 0;
    
    return freeMargin / equity;
}

//+------------------------------------------------------------------+
//| Check daily loss limit                                           |
//+------------------------------------------------------------------+
bool CheckDailyLossLimit()
{
    double currentBalance = accountInfo.Balance();
    double dailyPL = currentBalance - DailyStartBalance;
    double dailyPLPercent = (dailyPL / DailyStartBalance) * 100;
    
    if(dailyPLPercent < -MaxDailyLoss)
    {
        Print("DAILY LOSS LIMIT EXCEEDED: ", dailyPLPercent, "%");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Reset daily stats if new day                                     |
//+------------------------------------------------------------------+
void ResetDailyStatsIfNeeded()
{
    MqlDateTime dtCurrent, dtLast;
    TimeToStruct(TimeCurrent(), dtCurrent);
    TimeToStruct(LastDayReset, dtLast);
    
    if(dtCurrent.day != dtLast.day)
    {
        DailyStartBalance = accountInfo.Balance();
        LastDayReset = TimeCurrent();
        Print("Daily stats reset. New balance: ", DailyStartBalance);
    }
}

//+------------------------------------------------------------------+
//| Analyze pair and execute trade if signal present                 |
//+------------------------------------------------------------------+
void AnalyzeAndTrade(string symbol, int pairIndex)
{
    // Get indicator values
    double ema_fast[], ema_slow[], rsi[], bb_upper[], bb_middle[], bb_lower[], atr[];
    
    ArraySetAsSeries(ema_fast, true);
    ArraySetAsSeries(ema_slow, true);
    ArraySetAsSeries(rsi, true);
    ArraySetAsSeries(bb_upper, true);
    ArraySetAsSeries(bb_middle, true);
    ArraySetAsSeries(bb_lower, true);
    ArraySetAsSeries(atr, true);
    
    // Copy indicator buffers
    if(CopyBuffer(Handles[pairIndex].ema_fast, 0, 0, 3, ema_fast) < 3 ||
       CopyBuffer(Handles[pairIndex].ema_slow, 0, 0, 3, ema_slow) < 3 ||
       CopyBuffer(Handles[pairIndex].rsi, 0, 0, 3, rsi) < 3 ||
       CopyBuffer(Handles[pairIndex].bb, 1, 0, 3, bb_upper) < 3 ||
       CopyBuffer(Handles[pairIndex].bb, 0, 0, 3, bb_middle) < 3 ||
       CopyBuffer(Handles[pairIndex].bb, 2, 0, 3, bb_lower) < 3 ||
       CopyBuffer(Handles[pairIndex].atr, 0, 0, 3, atr) < 3)
    {
        Print("ERROR: Failed to copy indicator buffers for ", symbol);
        return;
    }
    
    // Get current price
    double currentPrice = SymbolInfoDouble(symbol, SYMBOL_ASK);
    
    // Calculate signal
    bool isLongSignal = false;
    bool isShortSignal = false;
    
    // LONG SIGNAL: EMA Fast > Slow, RSI < Oversold, Price near lower BB
    if(LongStrategy &&
       ema_fast[0] > ema_slow[0] &&
       rsi[0] < RSI_Oversold &&
       MathAbs(currentPrice - bb_lower[0]) / bb_lower[0] < 0.01)
    {
        isLongSignal = true;
    }
    
    // SHORT SIGNAL: EMA Fast < Slow, RSI > Overbought, Price near upper BB
    if(ShortStrategy &&
       ema_fast[0] < ema_slow[0] &&
       rsi[0] > RSI_Overbought &&
       MathAbs(bb_upper[0] - currentPrice) / bb_upper[0] < 0.01)
    {
        isShortSignal = true;
    }
    
    // ML Prediction Hook (placeholder)
    if(EnableML)
    {
        // TODO: Integrate ML model predictions
        // Example: Call external Python API or load ONNX model
        // For now, we just log that ML is enabled
        // double mlConfidence = CallMLAPI(symbol, indicators);
    }
    
    // Execute trade
    if(isLongSignal)
    {
        ExecuteTrade(symbol, ORDER_TYPE_BUY, currentPrice, pairIndex);
    }
    else if(isShortSignal)
    {
        ExecuteTrade(symbol, ORDER_TYPE_SELL, currentPrice, pairIndex);
    }
}

//+------------------------------------------------------------------+
//| Execute trade with SL and TP                                     |
//+------------------------------------------------------------------+
void ExecuteTrade(string symbol, ENUM_ORDER_TYPE orderType, double price, int pairIndex)
{
    // Calculate position size
    double lotSize = CalculatePositionSize(symbol, orderType);
    
    if(lotSize <= 0)
    {
        Print("ERROR: Invalid lot size for ", symbol);
        return;
    }
    
    // Calculate SL and TP
    double sl, tp;
    int slPips, tpPips;
    
    if(orderType == ORDER_TYPE_BUY)
    {
        slPips = StopLoss_Long;
        tpPips = TakeProfit_Long;
        sl = price - slPips * SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;
        tp = price + tpPips * SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;
    }
    else
    {
        slPips = StopLoss_Short;
        tpPips = TakeProfit_Short;
        sl = price + slPips * SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;
        tp = price - tpPips * SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;
    }
    
    // Normalize prices
    int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    sl = NormalizeDouble(sl, digits);
    tp = NormalizeDouble(tp, digits);
    
    // Print trade info
    Print("========================================");
    Print("EXECUTING TRADE: ", symbol);
    Print("  Type: ", orderType == ORDER_TYPE_BUY ? "BUY" : "SELL");
    Print("  Lot Size: ", lotSize);
    Print("  Entry: ", price);
    Print("  Stop Loss: ", sl, " (", slPips, " pips)");
    Print("  Take Profit: ", tp, " (", tpPips, " pips)");
    Print("  Risk/Reward: 1:", DoubleToString((double)tpPips / slPips, 2));
    Print("========================================");
    
    if(DryRun)
    {
        Print("DRY RUN - Trade not executed");
        return;
    }
    
    if(!EnableTrading)
    {
        Print("Trading disabled in settings");
        return;
    }
    
    // Place order
    string comment = StringFormat("%s-%s", CommentPrefix, symbol);
    
    if(trade.PositionOpen(symbol, orderType, lotSize, price, sl, tp, comment))
    {
        Print("✓ Order placed successfully: ", trade.ResultOrder());
        LastTradeTime[pairIndex] = TimeCurrent();
    }
    else
    {
        Print("ERROR: Failed to place order: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Calculate position size based on risk                            |
//+------------------------------------------------------------------+
double CalculatePositionSize(string symbol, ENUM_ORDER_TYPE orderType)
{
    double equity = accountInfo.Equity();
    double riskAmount = equity * (RiskPerTrade / 100.0);
    
    // Get stop loss in pips
    int slPips = (orderType == ORDER_TYPE_BUY) ? StopLoss_Long : StopLoss_Short;
    
    // Calculate pip value
    double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
    double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    
    double pipValue = tickValue / (tickSize / point);
    
    // Calculate lot size
    double lotSize = riskAmount / (slPips * pipValue * 10);
    
    // Apply min/max lot size
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    
    lotSize = MathMax(lotSize, minLot);
    lotSize = MathMin(lotSize, maxLot);
    
    // Round to lot step
    lotSize = MathFloor(lotSize / lotStep) * lotStep;
    
    return lotSize;
}

//+------------------------------------------------------------------+
//| Print configuration                                              |
//+------------------------------------------------------------------+
void PrintConfiguration()
{
    Print("Configuration:");
    Print("  Trading Pairs: ", ArraySize(TradingPairs));
    Print("  Session: ", SessionStartHour, ":00 - ", SessionEndHour, ":00");
    Print("  Risk Per Trade: ", RiskPerTrade, "%");
    Print("  Max Positions: ", MaxOpenPositions);
    Print("  Liquidity Buffer: ", LiquidityBuffer, "%");
    Print("  Long Strategy: ", LongStrategy ? "Yes" : "No");
    Print("  Short Strategy: ", ShortStrategy ? "Yes" : "No");
    Print("  ML Enabled: ", EnableML ? "Yes" : "No");
    Print("  Dry Run: ", DryRun ? "Yes" : "No");
    Print("  Trading Enabled: ", EnableTrading ? "Yes" : "No");
}

//+------------------------------------------------------------------+
//| Helper: Convert array to string                                  |
//+------------------------------------------------------------------+
string ArrayToString(string &arr[])
{
    string result = "";
    for(int i = 0; i < ArraySize(arr); i++)
    {
        if(i > 0) result += ", ";
        result += arr[i];
    }
    return result;
}

//+------------------------------------------------------------------+
//| ML API Call Placeholder                                          |
//+------------------------------------------------------------------+
// TODO: Implement ML integration
// Options:
// 1. Call Python REST API with indicator data
// 2. Load ONNX model in MT5
// 3. Use MT5's built-in machine learning capabilities
//
// Example Python API call:
// string url = "http://localhost:5000/predict";
// string headers = "Content-Type: application/json";
// string data = StringFormat("{\"symbol\":\"%s\",\"rsi\":%.2f,\"ema_fast\":%.5f,\"ema_slow\":%.5f}", 
//                           symbol, rsi, ema_fast, ema_slow);
// char post[], result[];
// string resultHeaders;
// StringToCharArray(data, post);
// int res = WebRequest("POST", url, headers, 5000, post, result, resultHeaders);
//+------------------------------------------------------------------+
