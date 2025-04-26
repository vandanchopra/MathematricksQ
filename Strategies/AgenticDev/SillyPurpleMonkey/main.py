from AlgorithmImports import *

class CryptoTradingAlgorithm(QCAlgorithm):

    def Initialize(self):
        """Initialise the data and resolution required, as well as the cash and start-end dates for backtesting.
        """
        self.SetStartDate(2023, 1, 1)  # Set Start Date
        self.SetEndDate(2024, 1, 1)    # Set End Date
        self.SetCash(100000)             # Set Strategy Cash

        # Define the cryptocurrency we want to trade
        self.symbol = "BTCUSD"  # Example: Bitcoin/USD
        self.AddCrypto(self.symbol, Resolution.Minute)

        # Define moving average periods (adjust as needed)
        self.fast_period = 12
        self.slow_period = 26

        # Create moving average indicators
        self.fast_ma = self.SMA(self.symbol, self.fast_period, Resolution.Minute)
        self.slow_ma = self.SMA(self.symbol, self.slow_period, Resolution.Minute)

        # Warm up the indicators (important for backtesting)
        self.SetWarmUp(max(self.fast_period, self.slow_period))

        # Set flag to prevent excessive orders
        self.is_invested = False

        # Schedule events for rebalancing/strategy adjustments (optional)
        # self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.At(9, 30), self.Rebalance)


    def OnData(self, data: Slice):
        """OnData event handler.  This method is called each time new data is available.
        """

        if self.IsWarmingUp:
            return

        # Get the current price of the cryptocurrency
        price = data[self.symbol].Close

        # Check if both moving averages are ready
        if not self.fast_ma.IsReady or not self.slow_ma.IsReady:
            return

        # Strategy Logic: Moving Average Crossover
        if self.fast_ma > self.slow_ma and not self.is_invested:
            # Fast MA crosses above Slow MA: Buy Signal
            self.SetHoldings(self.symbol, 1)  # Invest 100% of portfolio
            self.Debug(f"BUY: Fast MA ({self.fast_ma.Current.Value}) > Slow MA ({self.slow_ma.Current.Value}) at price {price}")
            self.is_invested = True

        elif self.fast_ma < self.slow_ma and self.is_invested:
            # Fast MA crosses below Slow MA: Sell Signal
            self.Liquidate(self.symbol)
            self.Debug(f"SELL: Fast MA ({self.fast_ma.Current.Value}) < Slow MA ({self.slow_ma.Current.Value}) at price {price}")
            self.is_invested = False

    def Rebalance(self):
        """
        Optional:  A function to rebalance the portfolio based on other signals or market conditions.
        This is called by the scheduled event.
        """
        # Example:  You could add logic here to adjust position size based on volatility, news sentiment, etc.
        # For now, it's just a placeholder.
        pass