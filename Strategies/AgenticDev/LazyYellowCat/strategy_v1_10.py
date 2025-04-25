from AlgorithmImports import *

class ImprovedLongShortEquityStrategy(QCAlgorithm):

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
        self.volatility = {}  # Store volatility for each symbol
        self.SetWarmUp(self.lookback)
        self.unstable_period = 5  # Period to determine if a stock is unstable
        self.volatility_threshold = 0.05  # Threshold for volatility
        self.EnableAutomaticIndicatorWarmUp = True

    def OnData(self, data):

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.CalculateVolatility(data)
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
        Calculates the volatility for each symbol based on historical data.
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
            self.volatility[symbol] = returns.std()  # Standard deviation as volatility

    def RebalancePortfolio(self):
        """
        Adjusts portfolio holdings based on momentum scores and volatility.
        Longs the top two momentum stocks and shorts the bottom two.
        Avoids highly volatile stocks.
        """
        if not self.momentum or not self.volatility:
            self.Log("No momentum or volatility data available. Skipping rebalancing.")
            return

        # Filter out unstable stocks
        stable_symbols = [
            symbol
            for symbol in self.symbols
            if self.volatility.get(symbol, 0) < self.volatility_threshold
        ]

        # Sort symbols based on momentum, considering only stable stocks
        sorted_symbols = sorted(
            [(symbol, self.momentum[symbol]) for symbol in stable_symbols if symbol in self.momentum],
            key=lambda x: x[1],
            reverse=True,
        )

        long_symbols = [symbol for symbol, _ in sorted_symbols[:2]]
        short_symbols = [symbol for symbol, _ in sorted_symbols[-2:]]

        long_weight = 0.5 / len(long_symbols) if long_symbols else 0
        short_weight = -0.5 / len(short_symbols) if short_symbols else 0

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