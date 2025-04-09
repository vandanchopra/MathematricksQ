from AlgorithmImports import *

class MomentumAAPLStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        self.symbol = self.AddEquity("AAPL", Resolution.Daily).Symbol
        
        # Lookback period for momentum calculation
        self.lookback = 90
        
        # Momentum threshold (5%) and tolerance
        self.momentum_threshold = 0.05
        self.tolerance = 0.002
        
        # Use built-in ROC indicator to measure % change over lookback period
        self.mom = self.ROC(self.symbol, self.lookback, Resolution.Daily)
        
        # Warm up the indicator
        self.SetWarmUp(self.lookback + 1)
        
    def OnData(self, data: Slice):
        # Wait until momentum indicator is fully warmed up
        if self.IsWarmingUp or not self.mom.IsReady:
            return
        
        momentum = self.mom.Current.Value / 100  # ROC returns percent, convert to decimal

        invested = self.Portfolio[self.symbol].Invested
        
        # Go long if momentum significantly above threshold and not invested
        if momentum > self.momentum_threshold * (1 + self.tolerance) and not invested:
            self.SetHoldings(self.symbol, 1)
            self.Debug(f"BUY AAPL on {self.Time.date()} | Momentum: {momentum:.2%}")
            
        # Liquidate if momentum drops significantly below threshold and invested
        elif momentum < self.momentum_threshold * (1 - self.tolerance) and invested:
            self.Liquidate(self.symbol)
            self.Debug(f"SELL AAPL on {self.Time.date()} | Momentum: {momentum:.2%}")