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

        # Risk management parameters
        self.max_drawdown_threshold = -0.05  # Stop trading if drawdown exceeds 5%
        self.initial_portfolio_value = self.Portfolio.TotalPortfolioValue
        self.high_watermark = self.initial_portfolio_value # track the maximum value
        self.stopped_trading = False

        # Volatility filter parameters
        self.volatility_lookback = 20  # Lookback period for volatility calculation
        self.volatility_threshold = 0.02  # Threshold for acceptable volatility


    def OnData(self, data):

        if self.stopped_trading:
            return

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        # Risk Management: Check drawdown
        current_drawdown = (self.Portfolio.TotalPortfolioValue - self.high_watermark) / self.high_watermark
        if current_drawdown < self.max_drawdown_threshold:
            self.Log("Maximum drawdown exceeded. Liquidating positions and stopping trading.")
            self.Liquidate()
            self.stopped_trading = True
            return

        #Update high watermark
        if self.Portfolio.TotalPortfolioValue > self.high_watermark:
            self.high_watermark = self.Portfolio.TotalPortfolioValue
            self.Log(f"New high watermark: {self.high_watermark}")


        self.CalculateMomentum(data)
        self.RebalancePortfolio(data)  # Pass data to RebalancePortfolio for volatility check
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


    def RebalancePortfolio(self, data):
        """
        Adjusts portfolio holdings based on momentum scores, incorporating volatility filtering.
        Longs the top two momentum stocks and shorts the bottom two.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = [symbol for symbol, _ in sorted_symbols[:2]]
        short_symbols = [symbol for symbol, _ in sorted_symbols[-2:]]


        # Volatility Filter:  Only trade if volatility is within acceptable limits
        tradable_longs = []
        tradable_shorts = []
        for symbol in long_symbols:
            if self.IsVolatilityAcceptable(symbol, data):
                tradable_longs.append(symbol)

        for symbol in short_symbols:
            if self.IsVolatilityAcceptable(symbol, data):
                tradable_shorts.append(symbol)


        long_weight = 0.5 / len(tradable_longs) if tradable_longs else 0
        short_weight = -0.5 / len(tradable_shorts) if tradable_shorts else 0


        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)


        for symbol in tradable_longs:
            self.SetHoldings(symbol, long_weight)

        for symbol in tradable_shorts:
            self.SetHoldings(symbol, short_weight)


    def IsVolatilityAcceptable(self, symbol, data):
        """
        Checks if the volatility of a symbol is within acceptable limits.
        """
        history = self.History(symbol, self.volatility_lookback, Resolution.DAILY)

        if history.empty:
            self.Log(f"No history data for {symbol} to calculate volatility.")
            return False

        returns = history['close'].pct_change().dropna()
        if len(returns) < 2: # need at least 2 data points to compute stddev
            return False;

        volatility = returns.std()

        if volatility > self.volatility_threshold:
            self.Log(f"Volatility for {symbol} is too high ({volatility:.4f}). Skipping trade.")
            return False

        return True


    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")