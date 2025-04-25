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
        self.rolling_window = {}

        self.SetWarmUp(self.lookback)

        # Initialize rolling window for each symbol
        for symbol in self.symbols:
            self.rolling_window[symbol] = RollingWindow[float](self.lookback)

        self.trades_this_rebalance = False #Flag to control trading frequency


    def OnData(self, data):

        # Update rolling window with current price
        for symbol in self.symbols:
            if data.ContainsKey(symbol) and data[symbol].Price > 0: # Check for valid data
                self.rolling_window[symbol].Add(float(data[symbol].Close))


        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        if self.trades_this_rebalance: #Only rebalance once per period
            return

        self.CalculateMomentum(data)
        self.RebalancePortfolio()
        self.last_rebalance = self.Time
        self.trades_this_rebalance = True #Set flag to prevent further trades

    def CalculateMomentum(self, data):
        """
        Calculates the momentum score for each symbol based on historical returns.
        Uses a rate of change calculation for a more robust momentum.
        """
        for symbol in self.symbols:

            if self.rolling_window[symbol].Samples < self.lookback:
                self.Log(f"Not enough data in rolling window for {symbol} at {self.Time}. Skipping momentum calculation for {symbol}.")
                continue

            # Calculate rate of change (ROC) using the rolling window
            past_price = self.rolling_window[symbol][0] # Price 'lookback' days ago
            current_price = self.rolling_window[symbol][self.lookback - 1] # Current price

            if past_price == 0:
                momentum_score = 0 # Avoid division by zero
            else:
                momentum_score = (current_price - past_price) / past_price

            self.momentum[symbol] = momentum_score


    def RebalancePortfolio(self):
        """
        Adjusts portfolio holdings based on momentum scores.
        Longs the top  momentum stock and shorts the bottom .
        Added a neutral position if momentum is weak.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        # Improved Logic: Only trade if there's sufficient momentum
        # Adjust threshold as needed based on backtesting results.
        momentum_threshold = 0.01 # Example: 1% change over the lookback period

        long_symbols = []
        short_symbols = []

        if sorted_symbols[0][1] > momentum_threshold:
            long_symbols = [sorted_symbols[0][0]]  #Long the top 1
        else:
            self.Log(f"Weak positive momentum.  Not initiating long positions.")


        if sorted_symbols[-1][1] < -momentum_threshold:
            short_symbols = [sorted_symbols[-1][0]] #Short the bottom 1
        else:
            self.Log(f"Weak negative momentum. Not initiating short positions.")


        long_weight = 0.5 / len(long_symbols) if long_symbols else 0
        short_weight = -0.5 / len(short_symbols) if short_symbols else 0


        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)


        for symbol in long_symbols:
            if self.Portfolio[symbol].IsLong:  # Check if already long
                continue
            self.SetHoldings(symbol, long_weight)

        for symbol in short_symbols:
            if self.Portfolio[symbol].IsShort:  # Check if already short
                continue
            self.SetHoldings(symbol, short_weight)

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")

    def OnEndOfDay(self):
        # Reset the trading flag at the end of the rebalance period
        if self.Time - self.last_rebalance >= self.rebalance_frequency:
             self.trades_this_rebalance = False #Allow trading on the next rebalance period