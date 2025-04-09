from AlgorithmImports import *

class MomentumAAPLStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        self.symbol = self.AddEquity("AAPL", Resolution.Daily).Symbol
        
        # Lookback period for momentum calculation
        self.lookback = 90
        
        # Rolling window to store close prices
        self.closes = RollingWindow[float](self.lookback + 1)
        
        # Warm up period to fill rolling window
        self.SetWarmUp(timedelta(days=150))  # generous warmup for safety
        
        self.momentum_threshold = 0.05  # 5%
        self.tolerance = 0.002

    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return
        
        # Update rolling window with current close if new data exists
        if self.symbol in data.Bars:
            close = data.Bars[self.symbol].Close
            self.closes.Add(close)
        else:
            return  # no data
        
        # Ensure we have enough data
        if self.closes.Count < self.lookback + 1:
            return
        
        # Calculate momentum: last close / close N days ago - 1
        recent_close = self.closes[0]
        past_close = self.closes[self.lookback]
        momentum = (recent_close / past_close) - 1
        
        invested = self.Portfolio[self.symbol].Invested
        
        # Long if momentum exceeds threshold and not invested
        if momentum > self.momentum_threshold * (1 + self.tolerance) and not invested:
            self.SetHoldings(self.symbol, 1)
            self.Debug(f"BUY AAPL on {self.Time.date()} | Momentum: {momentum:.2%}")
        
        # Liquidate if momentum falls below threshold and currently invested
        elif momentum < self.momentum_threshold * (1 - self.tolerance) and invested:
            self.Liquidate(self.symbol)
            self.Debug(f"SELL AAPL on {self.Time.date()} | Momentum: {momentum:.2%}")