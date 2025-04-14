from AlgorithmImports import *

class RsiStrategyAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Set Backtest Parameters
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        # Add Equity
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # RSI Parameters
        self.rsi_period = 14
        self.rsi = self.RSI(self.symbol, self.rsi_period, MovingAverageType.Wilders, Resolution.Daily)
        
        # Warm-up Indicator
        self.SetWarmUp(self.rsi_period + 1, Resolution.Daily)
        
    def OnData(self, data):
        # Ensure RSI is ready and symbol is in data
        if self.IsWarmingUp or not self.rsi.IsReady or self.symbol not in data:
            return

        rsi_value = self.rsi.Current.Value

        # Buy Signal: RSI < 30 and not invested
        if rsi_value < 30 and not self.Portfolio[self.symbol].Invested:
            self.SetHoldings(self.symbol, 1)
            self.Debug(f"BUY {self.symbol} at {self.Time} | RSI: {rsi_value:.2f}")

        # Sell Signal: RSI > 70 and invested
        elif rsi_value > 70 and self.Portfolio[self.symbol].Invested:
            self.Liquidate(self.symbol)
            self.Debug(f"SELL {self.symbol} at {self.Time} | RSI: {rsi_value:.2f}")