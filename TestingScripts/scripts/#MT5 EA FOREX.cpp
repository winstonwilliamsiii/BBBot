#MT5 EA FOREX 

// Pseudocode scaffold for MT5 EA

input string pair = "GBPJPY";   // or "XAUUSD"
input bool long_strategy = true; // toggle long/short

void OnTick() {
   if (TimeHour(TimeCurrent()) >= 12 && TimeHour(TimeCurrent()) <= 16) {
      if (long_strategy) {
         if (EMA(20) > EMA(50) && RSI(14) > 55) {
            PlaceBuyOrder(pair, SL=50, TP=100);
         }
      } else {
         if (RSI(14) > 70 && PriceRejectsResistance()) {
            PlaceSellOrder(pair, SL=10, TP=20);
         }
      }
   }
}