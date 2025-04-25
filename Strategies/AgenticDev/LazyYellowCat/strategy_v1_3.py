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
        self.volatility = {}  # Add volatility calculation

        self.SetWarmUp(self.lookback)

        self.position_size = 0.25 # Reduce the size of each position to control risk


    def OnData(self, data):

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.CalculateVolatility(data)  # Calculate volatility
        self.RebalancePortfolio()
        self.last_rebalance = self.Time


    def CalculateMomentum(self, data):
        """
        Calculates the momentum score for each symbol based on historical returns.
        """
        for symbol in self.symbols:
            if not data.ContainsKey(symbol):
                self.Log(f"No data for {symbol} at {self.Time}. Skipping momentum calculation.")
                continue

            history = self.History(symbol, self.lookback, Resolution.DAILY)

            if history.empty:
                self.Log(f"No history data for {symbol}. Skipping momentum calculation.")
                continue

            returns = history['close'].pct_change().dropna()
            momentum_score = returns.sum()

            self.momentum[symbol] = momentum_score

    def CalculateVolatility(self, data):
        """
        Calculates the volatility of each symbol based on historical returns.
        """
        for symbol in self.symbols:
            if not data.ContainsKey(symbol):
                self.Log(f"No data for {symbol} at {self.Time}. Skipping volatility calculation.")
                continue

            history = self.History(symbol, self.lookback, Resolution.DAILY)

            if history.empty:
                self.Log(f"No history data for {symbol}. Skipping volatility calculation.")
                continue

            returns = history['close'].pct_change().dropna()
            self.volatility[symbol] = returns.std()


    def RebalancePortfolio(self):
        """
        Adjusts portfolio holdings based on momentum scores and volatility.
        Longs the top two momentum stocks and shorts the bottom two, adjusted for volatility.
        """
        if not self.momentum or not self.volatility:
            self.Log("No momentum or volatility data available. Skipping rebalancing.")
            return

        # Rank by momentum and adjust by volatility
        adjusted_momentum = {}
        for symbol in self.symbols:
            if symbol in self.momentum and symbol in self.volatility and self.volatility[symbol] > 0:
                adjusted_momentum[symbol] = self.momentum[symbol] / self.volatility[symbol]
            else:
                adjusted_momentum[symbol] = 0  # Assign a neutral value if volatility is zero or missing


        sorted_symbols = sorted(adjusted_momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = [symbol for symbol, _ in sorted_symbols[:2]]
        short_symbols = [symbol for symbol, _ in sorted_symbols[-2:]]

        # Reduce position size to manage risk
        long_weight = self.position_size / len(long_symbols) if long_symbols else 0
        short_weight = -self.position_size / len(short_symbols) if short_symbols else 0


        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)


        for symbol in long_symbols:
            self.SetHoldings(symbol, long_weight)

        for symbol in short_symbols:
            self.SetHoldings(symbol, short_weight)

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")