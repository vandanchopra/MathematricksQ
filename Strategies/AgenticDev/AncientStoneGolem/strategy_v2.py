from AlgorithmImports import *

class SMAStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Subscribe to AAPL at daily resolution
        self.symbol = self.AddEquity("AAPL", Resolution.Daily).Symbol

        # Create the SMAs
        self.sma20 = self.SMA(self.symbol, 20, Resolution.Daily)
        self.sma50 = self.SMA(self.symbol, 50, Resolution.Daily)

        # Keep track of previous SMA values for crossover detection
        self.previous_sma20 = None
        self.previous_sma50 = None

    def OnData(self, data):
        if not self.sma20.IsReady or not self.sma50.IsReady:
            return

        current_sma20 = self.sma20.Current.Value
        current_sma50 = self.sma50.Current.Value

        if self.previous_sma20 is not None and self.previous_sma50 is not None:
            # Check for crossover and execute trades
            if (current_sma20 > current_sma50 and self.previous_sma20 <= self.previous_sma50):
                self.LongEntry()
            elif (current_sma20 < current_sma50 and self.previous_sma20 >= self.previous_sma50):
                self.ShortEntry()

        self.previous_sma20 = current_sma20
        self.previous_sma50 = current_sma50

    def LongEntry(self):
        # Close any existing short position
        if self.Portfolio[self.symbol].IsShort:
            self.Liquidate(self.symbol)

        # Enter long position if not already long
        if not self.Portfolio[self.symbol].IsLong:
            self.SetHoldings(self.symbol, 1.0)

    def ShortEntry(self):
        # Close any existing long position
        if self.Portfolio[self.symbol].IsLong:
            self.Liquidate(self.symbol)

        # Enter short position if not already short
        if not self.Portfolio[self.symbol].IsShort:
            self.SetHoldings(self.symbol, -1.0)