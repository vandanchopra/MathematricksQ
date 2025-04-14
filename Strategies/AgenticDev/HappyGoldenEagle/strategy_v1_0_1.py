from AlgorithmImports import *

class RsiStrategyAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        # Security selection
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # RSI indicator
        self.rsi_period = 14
        self.rsi = self.RSI(self.symbol, self.rsi_period, MovingAverageType.Wilders, Resolution.Daily)
        
    def OnData(self, data):
        # Ensure RSI is ready
        if not self.rsi.IsReady:
            return

        rsi_value = self.rsi.Current.Value

        # Buy signal: RSI < 30, not already invested
        if rsi_value < 30 and not self.Portfolio[self.symbol].Invested:
            self.SetHoldings(self.symbol, 1)
            self.Debug(f"BUY at {self.Time} | RSI: {rsi_value:.2f}")

        # Sell signal: RSI > 70, currently invested
        elif rsi_value > 70 and self.Portfolio[self.symbol].Invested:
            self.Liquidate(self.symbol)
            self.Debug(f"SELL at {self.Time} | RSI: {rsi_value:.2f}")