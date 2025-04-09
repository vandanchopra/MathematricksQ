from AlgorithmImports import *

class MomentumAAPLStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        self.symbol = self.AddEquity("AAPL", Resolution.Daily).Symbol
        
        # Lookback period for momentum calculation (e.g., 90 days)
        self.lookback = 90
        
        # Warm up period to get enough history
        self.SetWarmUp(self.lookback + 1)
        
        # Daily close price history
        self.history = None
        
        # Tolerance buffer to avoid excessive trading
        self.tolerance = 0.002
        
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        # Get historical close prices
        history = self.History(self.symbol, self.lookback + 1, Resolution.Daily)
        if history.empty:
            return
        
        closes = history['close'].unstack(level=0)[self.symbol]
        
        # Calculate momentum: current close / close n days ago - 1
        momentum = (closes[-1] / closes[-self.lookback -1]) -1
        
        # Define a momentum threshold
        threshold = 0.05  # 5%
        
        invested = self.Portfolio[self.symbol].Invested
        
        # Long if momentum exceeds threshold and not already invested
        if momentum > threshold * (1 + self.tolerance) and not invested:
            self.SetHoldings(self.symbol, 1)
            self.Debug(f"BUY AAPL at {self.Time.date()} | Momentum: {momentum:.2%}")
            
        # Liquidate if momentum falls below threshold and invested
        elif momentum < threshold * (1 - self.tolerance) and invested:
            self.Liquidate(self.symbol)
            self.Debug(f"SELL AAPL at {self.Time.date()} | Momentum: {momentum:.2%}")