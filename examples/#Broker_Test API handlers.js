#Broker_Test API handlers

{
  broker: 'schwab' | 'binance' | 'tradestation',
  positions: NormalizedPosition[],
  balance: NormalizedBalance,
  orderStatus: NormalizedOrderStatus
}