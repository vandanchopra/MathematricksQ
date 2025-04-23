from AlgorithmImports import *

class SimpleStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 12, 1)
        self.SetEndDate(2025, 4, 15)
        self.SetCash(100000)
        self.symbol = self.AddEquity("AAPL", Resolution.Minute).Symbol
        self.sma = self.SMA(self.symbol, 20, Resolution.Minute)

    def OnData(self, data):
        if not self.sma.IsReady or not self.symbol in data:
            return
        if data[self.symbol].Close > self.sma.Current.Value:
            self.SetHoldings(self.symbol, 1.0)
        else:
            self.Liquidate()