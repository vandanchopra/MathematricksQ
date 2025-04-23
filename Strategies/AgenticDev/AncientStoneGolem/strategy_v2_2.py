from AlgorithmImports import *

class SMAStrategyOptimized(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Subscribe to AAPL at daily resolution
        self.symbol = self.AddEquity("AAPL", Resolution.Daily).Symbol

        # Optimized SMA periods - these were found through backtesting/optimization (example values)
        self.fast_period = 15  # Adjusted fast SMA period (previously 20)
        self.slow_period = 60  # Adjusted slow SMA period (previously 50)

        # Create the SMAs
        self.sma_fast = self.SMA(self.symbol, self.fast_period, Resolution.Daily)
        self.sma_slow = self.SMA(self.symbol, self.slow_period, Resolution.Daily)

        # Keep track of previous SMA values for crossover detection
        self.previous_sma_fast = None
        self.previous_sma_slow = None

        # Stop-loss and Take-profit levels (as percentages)
        self.stop_loss_percentage = 0.02  # 2% stop loss
        self.take_profit_percentage = 0.05 # 5% take profit

        # Flag to indicate if we are currently managing a trade
        self.in_trade = False


    def OnData(self, data):
        if not self.sma_fast.IsReady or not self.sma_slow.IsReady:
            return

        current_sma_fast = self.sma_fast.Current.Value
        current_sma_slow = self.sma_slow.Current.Value

        if self.previous_sma_fast is not None and self.previous_sma_slow is not None:
            # Check for crossover and execute trades
            if (current_sma_fast > current_sma_slow and self.previous_sma_fast <= self.previous_sma_slow):
                self.LongEntry()
            elif (current_sma_fast < current_sma_slow and self.previous_sma_fast >= self.previous_sma_slow):
                self.ShortEntry()

        self.previous_sma_fast = current_sma_fast
        self.previous_sma_slow = current_sma_slow

        # Manage existing trade with stop-loss and take-profit
        if self.in_trade:
            self.ManageTrade()


    def LongEntry(self):
        # Close any existing short position
        if self.Portfolio[self.symbol].IsShort:
            self.Liquidate(self.symbol)
            self.Debug(f"Closing short position at {self.Time}")

        # Enter long position if not already long
        if not self.Portfolio[self.symbol].IsLong:
            self.SetHoldings(self.symbol, 1.0)
            self.Debug(f"Entering long position at {self.Time}")
            self.in_trade = True


    def ShortEntry(self):
        # Close any existing long position
        if self.Portfolio[self.symbol].IsLong:
            self.Liquidate(self.symbol)
            self.Debug(f"Closing long position at {self.Time}")


        # Enter short position if not already short
        if not self.Portfolio[self.symbol].IsShort:
            self.SetHoldings(self.symbol, -1.0)
            self.Debug(f"Entering short position at {self.Time}")
            self.in_trade = True


    def ManageTrade(self):
        # Get the current holding quantity and average price
        holding = self.Portfolio[self.symbol]
        if holding.Quantity == 0:
            self.in_trade = False
            return

        avg_price = holding.AveragePrice
        current_price = self.Securities[self.symbol].Price

        # Calculate stop-loss and take-profit prices
        if holding.IsLong:
            stop_loss_price = avg_price * (1 - self.stop_loss_percentage)
            take_profit_price = avg_price * (1 + self.take_profit_percentage)

            # Close position if stop-loss or take-profit is hit
            if current_price <= stop_loss_price:
                self.Liquidate(self.symbol)
                self.Debug(f"Long position stop-loss triggered at {self.Time}, price: {current_price}")
                self.in_trade = False
            elif current_price >= take_profit_price:
                self.Liquidate(self.symbol)
                self.Debug(f"Long position take-profit triggered at {self.Time}, price: {current_price}")
                self.in_trade = False

        elif holding.IsShort:
            stop_loss_price = avg_price * (1 + self.stop_loss_percentage)
            take_profit_price = avg_price * (1 - self.take_profit_percentage)

            # Close position if stop-loss or take-profit is hit
            if current_price >= stop_loss_price:
                self.Liquidate(self.symbol)
                self.Debug(f"Short position stop-loss triggered at {self.Time}, price: {current_price}")
                self.in_trade = False
            elif current_price <= take_profit_price:
                self.Liquidate(self.symbol)
                self.Debug(f"Short position take-profit triggered at {self.Time}, price: {current_price}")
                self.in_trade = False