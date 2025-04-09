from AlgorithmImports import *
from datetime import timedelta

class MultiStockMomentumStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        self.tickers = ["AAPL", "MSFT", "AMZN", "META", "GOOG", "NVDA", "JPM", "UNH", "XOM", "JNJ"]
        self.symbols = []
        self.lookback = 90
        self.momentum_threshold = 0.05
        self.tolerance = 0.002

        self.close_windows = {}

        for ticker in self.tickers:
            symbol = self.AddEquity(ticker, Resolution.Daily).Symbol
            self.symbols.append(symbol)
            self.close_windows[symbol] = RollingWindow[float](self.lookback + 1)

        self.SetWarmUp(timedelta(days=150))  # fill up rolling windows

    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return

        for symbol in self.symbols:
            # Update rolling window with new close if data exists
            if symbol in data.Bars:
                self.close_windows[symbol].Add(data.Bars[symbol].Close)
            else:
                continue

            if self.close_windows[symbol].Count < self.lookback + 1:
                continue

            # Momentum calculation
            recent_close = self.close_windows[symbol][0]
            past_close = self.close_windows[symbol][self.lookback]
            momentum = (recent_close / past_close) - 1

            invested = self.Portfolio[symbol].Invested

            # Entry signal
            if momentum > self.momentum_threshold * (1 + self.tolerance) and not invested:
                self.SetHoldings(symbol, 1.0 / len(self.symbols))
                self.Debug(f"BUY {symbol.Value} | {self.Time.date()} | Momentum: {momentum:.2%}")

            # Exit signal
            elif momentum < self.momentum_threshold * (1 - self.tolerance) and invested:
                self.Liquidate(symbol)
                self.Debug(f"SELL {symbol.Value} | {self.Time.date()} | Momentum: {momentum:.2%}")
