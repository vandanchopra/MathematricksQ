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
        self.ema_fast_period = 5
        self.ema_slow_period = 20
        self.ema_fast = {}
        self.ema_slow = {}

        for symbol in self.symbols:
            self.ema_fast[symbol] = ExponentialMovingAverage(self.ema_fast_period)
            self.ema_slow[symbol] = ExponentialMovingAverage(self.ema_slow_period)
            self.RegisterIndicator(symbol, self.ema_fast[symbol], Resolution.DAILY)
            self.RegisterIndicator(symbol, self.ema_slow[symbol], Resolution.DAILY)



    def OnData(self, data):

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.CalculateVolatility(data) # Calculate volatility
        self.RebalancePortfolio(data)
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
        Calculates the volatility for each symbol.  Uses standard deviation of returns.
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
            self.volatility[symbol] = returns.std()  # Use standard deviation as volatility



    def RebalancePortfolio(self, data):
        """
        Adjusts portfolio holdings based on momentum scores and volatility.
        Longs the top two momentum stocks and shorts the bottom two, adjusted by volatility.
        Also considers EMA crossover.
        """
        if not self.momentum or not self.volatility:
            self.Log("No momentum or volatility data available. Skipping rebalancing.")
            return

        # Rank by momentum divided by volatility (risk-adjusted momentum)
        risk_adjusted_momentum = {}
        for symbol in self.symbols:
            if self.volatility[symbol] > 0:
                risk_adjusted_momentum[symbol] = self.momentum[symbol] / self.volatility[symbol]
            else:
                risk_adjusted_momentum[symbol] = 0  # Avoid division by zero

        sorted_symbols = sorted(risk_adjusted_momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = [symbol for symbol, _ in sorted_symbols[:2]]
        short_symbols = [symbol for symbol, _ in sorted_symbols[-2:]]

        # EMA crossover filter
        filtered_long_symbols = []
        filtered_short_symbols = []

        for symbol in long_symbols:
             if self.ema_fast[symbol].Current.Value > self.ema_slow[symbol].Current.Value:
                 filtered_long_symbols.append(symbol)
             else:
                 self.Log(f"Skipping long {symbol} due to EMA crossover.")

        for symbol in short_symbols:
            if self.ema_fast[symbol].Current.Value < self.ema_slow[symbol].Current.Value:
                filtered_short_symbols.append(symbol)
            else:
                self.Log(f"Skipping short {symbol} due to EMA crossover.")

        long_weight = 0.5 / len(filtered_long_symbols) if filtered_long_symbols else 0
        short_weight = -0.5 / len(filtered_short_symbols) if filtered_short_symbols else 0


        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)


        for symbol in filtered_long_symbols:
            self.SetHoldings(symbol, long_weight)

        for symbol in filtered_short_symbols:
            self.SetHoldings(symbol, short_weight)

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")