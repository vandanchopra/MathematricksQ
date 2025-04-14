from AlgorithmImports import *

class RsiStrategyAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Set start and end dates for backtest
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 1, 1)
        # Set initial cash
        self.SetCash(100000)
        
        # Choose the security to trade, e.g., SPY
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # RSI parameters
        self.rsi_period = 14
        self.rsi = self.RSI(self.symbol, self.rsi_period, MovingAverageType.Wilders, Resolution.Daily)
        
        # To prevent repeated orders
        self.last_signal = None

    def OnData(self, data):
        # Ensure RSI is ready and data is available
        if not self.rsi.IsReady:
            return
        
        rsi_value = self.rsi.Current.Value

        # Buy if RSI < 30 and not already invested
        if rsi_value < 30:
            if not self.Portfolio[self.symbol].Invested and self.last_signal != 'buy':
                self.SetHoldings(self.symbol, 1)  # Invest 100% portfolio
                self.last_signal = 'buy'
                self.Debug(f"BUY at {self.Time} | RSI: {rsi_value:.2f}")
        
        # Sell if RSI > 70 and currently invested
        elif rsi_value > 70:
            if self.Portfolio[self.symbol].Invested and self.last_signal != 'sell':
                self.Liquidate(self.symbol)
                self.last_signal = 'sell'
                self.Debug(f"SELL at {self.Time} | RSI: {rsi_value:.2f}")