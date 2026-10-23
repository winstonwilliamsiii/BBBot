-- Active: 1763499046791@@127.0.0.1@3306@mansa_quant
#metatrader Expert Advisor

#property strict

string api_url = "http://127.0.0.1:8000/notify/signal";
string bot_name = "Titan";   // Change per bot instance

int OnInit()
{
   Print("Mansa EA initialized for bot: ", bot_name);
   return(INIT_SUCCEEDED);
}

void SendSignal(string symbol, string decision, double cosmic_score)
{
   string json = StringFormat(
      "{\"bot_name\":\"%s\",\"symbol\":\"%s\",\"decision\":\"%s\",\"cosmic_score\":%f,\"mode\":\"live\"}",
      bot_name, symbol, decision, cosmic_score
   );

   char data[];
   int data_size = StringToCharArray(json, data, 0, WHOLE_ARRAY, CP_UTF8);
   if (data_size > 0)
   {
      ArrayResize(data, data_size - 1);
   }

   char result[];
   string headers = "Content-Type: application/json\r\n";
   int status = WebRequest("POST", api_url, headers, 5000, data, result);

   if (status == -1)
   {
      Print("WebRequest error: check URL permissions");
   }
   else if (status < 200 || status >= 300)
   {
      Print("Signal delivery failed. HTTP status: ", status);
   }
   else
   {
      Print("Signal delivered. HTTP status: ", status);
   }
}

void OnTick()
{
   string symbol = _Symbol;

   // Example logic — replace with your bot logic
   double price = SymbolInfoDouble(symbol, SYMBOL_BID);
   double cosmic_score = 72.5;

   string decision = (price > iMA(symbol, PERIOD_H1, 50, 0, MODE_SMA, PRICE_CLOSE, 0))
                     ? "BUY"
                     : "SELL";

   SendSignal(symbol, decision, cosmic_score);
}
