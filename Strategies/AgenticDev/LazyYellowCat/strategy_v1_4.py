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

        # Risk Management Parameters
        self.max_drawdown_percent = 0.10  # Maximum drawdown before liquidating
        self.stop_loss_percent = 0.05      # Stop loss for individual positions
        self.position_size = 0.20         # Maximum position size for each asset (20% of portfolio, reduced to diversify more)

        # Volatility Scaling Parameters
        self.volatility_lookback = 20
        self.volatility = {}

        #ATR Stop Loss
        self.atr_period = 14
        self.atr = {}

    def OnData(self, data):

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateATR(data)
        self.CalculateMomentum(data)
        self.CalculateVolatility(data)
        self.RebalancePortfolio()
        self.last_rebalance = self.Time

        self.CheckDrawdown()
        #self.ManageStopLosses(data) #Replaced with ATR Stop Loss


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
        Calculates the historical volatility for each symbol.
        """
        for symbol in self.symbols:
            if not data.ContainsKey(symbol):
                continue

            history = self.History(symbol, self.volatility_lookback, Resolution.DAILY)

            if history.empty:
                self.volatility[symbol] = 0.1  # Default volatility if no history
                continue

            returns = history['close'].pct_change().dropna()
            self.volatility[symbol] = returns.std()

    def CalculateATR(self, data):
        """
        Calculates the Average True Range for each symbol.
        """
        for symbol in self.symbols:
            if not data.ContainsKey(symbol):
                continue

            history = self.History(symbol, self.atr_period, Resolution.DAILY)

            if history.empty:
                self.atr[symbol] = 0.01  # Default ATR if no history
                continue

            tr = list()
            for i in range(1, len(history)):
                high = history['high'][i]
                low = history['low'][i]
                close_prev = history['close'][i-1]

                true_range = max(high - low, abs(high - close_prev), abs(low - close_prev))
                tr.append(true_range)

            self.atr[symbol] = np.mean(tr)

    def RebalancePortfolio(self):
        """
        Adjusts portfolio holdings based on momentum scores and volatility.
        Longs the top two momentum stocks and shorts the bottom two.
        Positions are scaled based on inverse volatility.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = [symbol for symbol, _ in sorted_symbols[:2]]
        short_symbols = [symbol for symbol, _ in sorted_symbols[-2:]]


        # Calculate weights based on inverse volatility
        total_inverse_volatility_long = sum([1 / (self.volatility.get(s, 0.1) + 0.01) for s in long_symbols]) #Added small value to volatility to prevent division by zero and improve stability
        total_inverse_volatility_short = sum([1 / (self.volatility.get(s, 0.1) + 0.01) for s in short_symbols])#Added small value to volatility to prevent division by zero and improve stability

        long_weights = {s: (1 / (self.volatility.get(s, 0.1) + 0.01)) / total_inverse_volatility_long * self.position_size if total_inverse_volatility_long > 0 else 0 for s in long_symbols}
        short_weights = {s: -(1 / (self.volatility.get(s, 0.1) + 0.01)) / total_inverse_volatility_short * self.position_size if total_inverse_volatility_short > 0 else 0 for s in short_symbols}

        # Liquidate existing positions
        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)

        # Set new holdings
        for symbol, weight in long_weights.items():
            self.SetHoldings(symbol, weight)

        for symbol, weight in short_weights.items():
            self.SetHoldings(symbol, weight)
        
        self.SetATRStopLosses() #Set Stop Losses after rebalancing


    def CheckDrawdown(self):
        """
        Monitors portfolio drawdown and liquidates if it exceeds the maximum allowed.
        """
        drawdown = self.Portfolio.TotalPortfolioValue / self.StartingPortfolioValue - 1
        if drawdown < -self.max_drawdown_percent:
            self.Log("Maximum drawdown exceeded. Liquidating portfolio.")
            self.Liquidate()

    def SetATRStopLosses(self):
        """
        Sets ATR-based stop losses for all open positions.
        """
        for symbol, holding in self.Portfolio.items():
            if holding.Invested:
                atr_value = self.atr.get(symbol, 0.01)  # Get ATR value, default to 0.01
                if holding.IsLong:
                    stop_loss_price = holding.AveragePrice - (2 * atr_value) # 2 ATRs below entry
                    self.StopMarketOrder(symbol, -holding.Quantity, stop_loss_price)
                elif holding.IsShort:
                    stop_loss_price = holding.AveragePrice + (2 * atr_value) # 2 ATRs above entry
                    self.StopMarketOrder(symbol, -holding.Quantity, stop_loss_price)


    def ManageStopLosses(self, data):
        """
        Implements stop-loss orders for each open position.
        """
        for symbol, holding in self.Portfolio.items():
            if holding.Invested:
                if data.ContainsKey(symbol) and data[symbol] is not None:
                    current_price = data[symbol].Close
                    entry_price = holding.AveragePrice
                    stop_loss_level = entry_price * (1 - self.stop_loss_percent)

                    if holding.IsLong and current_price <= stop_loss_level:
                        self.Log(f"Stop loss triggered for {symbol}. Liquidating long position.")
                        self.Liquidate(symbol)
                    elif holding.IsShort and current_price >= entry_price * (1 + self.stop_loss_percent):
                        self.Log(f"Stop loss triggered for {symbol}. Liquidating short position.")
                        self.Liquidate(symbol)


    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")