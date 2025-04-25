from AlgorithmImports import *

class LongShortEquityStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)

        self.spy = self.AddEquity("SPY", Resolution.DAILY).Symbol
        self.aapl = self.AddEquity("AAPL", Resolution.DAILY).Symbol
        self.msft = self.AddEquity("MSFT", Resolution.DAILY).Symbol
        self.nvda = self.AddEquity("NVDA", Resolution.DAILY).Symbol

        self.symbols = [self.spy, self.aapl, self.msft, self.nvda]

        self.lookback = 20
        self.rebalance_frequency = timedelta(days=5)
        self.last_rebalance = datetime.min

        self.momentum = {}

        self.SetWarmUp(self.lookback)


    def OnData(self, data):

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.RebalancePortfolio()
        self.last_rebalance = self.Time


    def CalculateMomentum(self, data):
        """
        Calculates the momentum score for each symbol based on historical returns.
        """
        for symbol in self.symbols:
            try:
                history = self.History(symbol, self.lookback, Resolution.DAILY)

                if history.empty:
                    self.Log(f"No history data for {symbol}. Skipping momentum calculation.")
                    self.momentum[symbol] = 0  # Assign a default value to avoid errors later
                    continue

                returns = history['close'].pct_change().dropna()
                if returns.empty:
                    self.Log(f"No returns data for {symbol}. Skipping momentum calculation.")
                    self.momentum[symbol] = 0  # Assign a default value
                    continue

                momentum_score = returns.sum()
                self.momentum[symbol] = momentum_score

            except Exception as e:
                self.Log(f"Error calculating momentum for {symbol}: {e}")
                self.momentum[symbol] = 0 # Assign a default value


    def RebalancePortfolio(self):
        """
        Adjusts portfolio holdings based on momentum scores.
        Longs the top two momentum stocks and shorts the bottom two.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = [symbol for symbol, _ in sorted_symbols[:2]]
        short_symbols = [symbol for symbol, _ in sorted_symbols[-2:]]


        long_weight = 0.5 / len(long_symbols) if long_symbols else 0
        short_weight = -0.5 / len(short_symbols) if short_symbols else 0


        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)


        for symbol in long_symbols:
            if self.Securities[symbol].IsTradable:
                self.SetHoldings(symbol, long_weight)
            else:
                self.Log(f"Symbol {symbol} is not tradable. Skipping.")

        for symbol in short_symbols:
            if self.Securities[symbol].IsTradable:
                self.SetHoldings(symbol, short_weight)
            else:
                self.Log(f"Symbol {symbol} is not tradable. Skipping.")

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")