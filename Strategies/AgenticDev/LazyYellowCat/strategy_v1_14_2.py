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

        self.SetWarmUp(self.lookback)
        
        # Add trailing stop loss
        self.trailing_stop_percentage = 0.05  # 5% trailing stop
        self.highest_prices = {}

        # Volatility filter parameters
        self.volatility_lookback = 20
        self.volatility_threshold = 0.3  # Tune this based on your risk tolerance

        #Dynamic weighting
        self.leverage_limit = 1.0 #maximum leverage
        self.volatility_scale = 0.5 #scale down position sizes based on volatlity
        self.average_volatility = {}

    def OnData(self, data):

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.CalculateVolatility(data)
        self.RebalancePortfolio(data)
        self.last_rebalance = self.Time
        self.UpdateTrailingStops(data)


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
            # Adjusted Momentum Calculation: Exponential Weighted Moving Average
            # Gives more weight to recent returns
            weights = np.exp(np.linspace(-1., 0., num=len(returns)))
            weights /= weights.sum()
            momentum_score = np.dot(returns, weights)

            self.momentum[symbol] = momentum_score

    def CalculateVolatility(self, data):
        """
        Calculates the rolling volatility for each symbol.
        """
        for symbol in self.symbols:
            if not data.ContainsKey(symbol):
                self.average_volatility[symbol] = 0 #set default value
                continue

            history = self.History(symbol, self.volatility_lookback, Resolution.DAILY)

            if history.empty:
                self.average_volatility[symbol] = 0 #set default value
                continue

            returns = history['close'].pct_change().dropna()
            self.average_volatility[symbol] = np.std(returns) #standard deviation of returns

    def RebalancePortfolio(self, data):
        """
        Adjusts portfolio holdings based on momentum scores and volatility.
        Longs the top two momentum stocks and shorts the bottom two,
        but filters out high-volatility stocks.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = []
        short_symbols = []

        # Select long candidates, filtering by volatility
        for symbol, _ in sorted_symbols:
            if symbol in self.average_volatility and self.average_volatility[symbol] < self.volatility_threshold:
                long_symbols.append(symbol)
                if len(long_symbols) == 2:
                    break

        # Select short candidates, filtering by volatility
        for symbol, _ in reversed(sorted_symbols): #reversed to get the bottom
            if symbol in self.average_volatility and self.average_volatility[symbol] < self.volatility_threshold:
                short_symbols.append(symbol)
                if len(short_symbols) == 2:
                    break

        #Dynamic weighting based on volatility
        total_volatility = 0
        for symbol in long_symbols + short_symbols:
            if symbol in self.average_volatility:
                total_volatility += self.average_volatility[symbol]

        long_weight = 0
        short_weight = 0

        if long_symbols:
             long_weight = (self.leverage_limit/2) / len(long_symbols)
        if short_symbols:
            short_weight = (-self.leverage_limit/2) / len(short_symbols)

        # Liquidate existing positions before rebalancing
        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)
                self.highest_prices[holding.Symbol] = 0  # Reset highest price

        for symbol in long_symbols:
            #volatility scaling
            if symbol in self.average_volatility and total_volatility > 0:
                target_weight = long_weight * (1 - self.volatility_scale * (self.average_volatility[symbol] / total_volatility))
            else:
                target_weight = long_weight
            self.SetHoldings(symbol, target_weight)
            self.highest_prices[symbol] = self.CurrentSlice.Bars[symbol].Close  # Initialize highest price

        for symbol in short_symbols:
            #volatility scaling
            if symbol in self.average_volatility and total_volatility > 0:
                target_weight = short_weight * (1 - self.volatility_scale * (self.average_volatility[symbol] / total_volatility))
            else:
                target_weight = short_weight

            self.SetHoldings(symbol, target_weight)
            self.highest_prices[symbol] = self.CurrentSlice.Bars[symbol].Close  # Initialize highest price

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")

    def UpdateTrailingStops(self, data):
        """
        Updates the trailing stop loss for each held security.
        """
        for symbol, holding in self.Portfolio.items():
            if holding.Invested and data.ContainsKey(symbol):
                current_price = data[symbol].Close
                
                # Update highest price
                if symbol in self.highest_prices:
                    self.highest_prices[symbol] = max(self.highest_prices[symbol], current_price)
                else:
                    self.highest_prices[symbol] = current_price

                # Calculate stop loss price
                if holding.IsLong:
                    stop_loss_price = self.highest_prices[symbol] * (1 - self.trailing_stop_percentage)
                    if current_price <= stop_loss_price:
                        self.Liquidate(symbol)
                        self.Log(f"Trailing stop loss triggered for {symbol} at {current_price}")
                        self.highest_prices[symbol] = 0 #reset

                elif holding.IsShort:
                    stop_loss_price = self.highest_prices[symbol] * (1 + self.trailing_stop_percentage)
                    if current_price >= stop_loss_price:
                        self.Liquidate(symbol)
                        self.Log(f"Trailing stop loss triggered for {symbol} at {current_price}")
                        self.highest_prices[symbol] = 0 #reset.