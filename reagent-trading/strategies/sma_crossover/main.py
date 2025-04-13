# SMA Crossover Strategy
from AlgorithmImports import *

class SmaCrossoverStrategy(QCAlgorithm):
    def Initialize(self):
        # Set start date, end date, and initial cash
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2020, 1, 1)
        self.SetCash(100000)
        
        # Add SPY equity
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # Create two SMAs
        self.fast_sma = self.SMA(self.spy, 20)
        self.slow_sma = self.SMA(self.spy, 50)
        
        # Set warm-up period
        self.SetWarmUp(50)
        
    def OnData(self, data):
        # Skip if we're still in warm-up or don't have data
        if self.IsWarmingUp or not data.ContainsKey(self.spy):
            return
            
        # Get current holdings
        holdings = self.Portfolio[self.spy].Quantity
        
        # Check for buy signal
        if holdings <= 0 and self.fast_sma.Current.Value > self.slow_sma.Current.Value:
            self.SetHoldings(self.spy, 1.0)
            self.Log(f"Buy signal: Fast SMA {self.fast_sma.Current.Value} > Slow SMA {self.slow_sma.Current.Value}")
            
        # Check for sell signal
        elif holdings > 0 and self.fast_sma.Current.Value < self.slow_sma.Current.Value:
            self.Liquidate(self.spy)
            self.Log(f"Sell signal: Fast SMA {self.fast_sma.Current.Value} < Slow SMA {self.slow_sma.Current.Value}")
            
    def ManageRisk(self):
        if self.Portfolio.Invested:
            holding = self.Portfolio[self.spy]
            
            # Implement stop loss (3%)
            if holding.Price < holding.AveragePrice * 0.97:
                self.Liquidate(self.spy)
                self.Log("Stop loss triggered")
                return
                
            # Implement take profit (9%)
            if holding.Price > holding.AveragePrice * 1.09:
                self.Liquidate(self.spy)
                self.Log("Take profit triggered")
                return
