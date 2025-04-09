from AlgorithmImports import *

class TestSMACrossover(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(1921, 1, 1)
        self.SetEndDate(1923, 12, 31)
        self.SetCash(100000)
        self.symbols = [self.AddEquity(ticker, Resolution.Daily).Symbol for ticker in ["AAPL", "GOOG"]]
        self.fast = {}
        self.slow = {}
        for symbol in self.symbols:
            self.fast[symbol] = self.SMA(symbol, 10, Resolution.Daily)
            self.slow[symbol] = self.SMA(symbol, 30, Resolution.Daily)
        self.last_action = {}

    def OnData(self, data):
        for symbol in self.symbols:
            if not self.fast[symbol].IsReady or not self.slow[symbol].IsReady:
                continue
            holdings = self.Portfolio[symbol].Quantity
            if self.fast[symbol].Current.Value > self.slow[symbol].Current.Value and holdings <= 0:
                self.SetHoldings(symbol, 0.33)
            elif self.fast[symbol].Current.Value < self.slow[symbol].Current.Value and holdings > 0:
                self.Liquidate(symbol)
