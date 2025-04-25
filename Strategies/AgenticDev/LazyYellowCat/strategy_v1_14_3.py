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
        
        # Trailing stop loss
        self.trailing_stop_percentage = 0.05
        self.highest_prices = {}

        # Volatility filter parameters
        self.volatility_lookback = 20  # Lookback period for volatility calculation
        self.volatility_threshold = 0.30  # Maximum allowed volatility (annualized)

        #Add A EMA filter
        self.ema_fast_period = 5
        self.ema_slow_period = 20
        self.ema = {} # Dictionary to store EMA indicators
        
        # Initialize EMA indicators
        for symbol in self.symbols:
            self.ema[symbol] = self.EMA(symbol, self.ema_fast_period, Resolution.DAILY)
            
    def OnData(self, data):
        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.RebalancePortfolio(data)
        self.last_rebalance = self.Time
        self.UpdateTrailingStops(data)

    def CalculateMomentum(self, data):
        """
        Calculates the momentum score for each symbol based on historical returns.
        """
        for symbol in self.symbols:
            if not data.ContainsKey(symbol) or not data[symbol] or data[symbol].Close <= 0:
                self.Log(f"No valid data for {symbol} at {self.Time}. Skipping momentum calculation.")
                continue

            history = self.History(symbol, self.lookback, Resolution.DAILY)

            if history.empty:
                self.Log(f"No history data for {symbol}. Skipping momentum calculation.")
                continue

            returns = history['close'].pct_change().dropna()
            if returns.empty:
                self.momentum[symbol] = 0  # Set momentum to 0 if no returns are available
                continue

            weights = np.exp(np.linspace(-1., 0., num=len(returns)))
            weights /= weights.sum()
            momentum_score = np.dot(returns, weights)

            self.momentum[symbol] = momentum_score


    def CalculateVolatility(self, symbol):
        """Calculates the annualized volatility of a symbol."""
        history = self.History(symbol, self.volatility_lookback, Resolution.DAILY)
        if history.empty:
            return float('inf')  # Return a high value if no history is available

        returns = history['close'].pct_change().dropna()
        if returns.empty:
            return float('inf')

        daily_volatility = np.std(returns)
        annualized_volatility = daily_volatility * np.sqrt(252)  # Assuming 252 trading days in a year
        return annualized_volatility

    def RebalancePortfolio(self, data):
        """
        Adjusts portfolio holdings based on momentum scores, volatility, and EMA filter.
        Longs the top two momentum stocks and shorts the bottom two.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = []
        short_symbols = []

        for symbol, _ in sorted_symbols[:2]:  # Top 2 momentum
            volatility = self.CalculateVolatility(symbol)
            if volatility < self.volatility_threshold and self.ema[symbol].Current.Value > data[symbol].Close: # Add EMA Filter
                long_symbols.append(symbol)
            else:
                self.Log(f"Skipping long {symbol} due to high volatility ({volatility:.2f}) or EMA filter.")

        for symbol, _ in sorted_symbols[-2:]:  # Bottom 2 momentum
            volatility = self.CalculateVolatility(symbol)
            if volatility < self.volatility_threshold and self.ema[symbol].Current.Value < data[symbol].Close: # Add EMA Filter
                short_symbols.append(symbol)
            else:
                 self.Log(f"Skipping short {symbol} due to high volatility ({volatility:.2f}) or EMA filter.")


        long_weight = 0.5 / len(long_symbols) if long_symbols else 0
        short_weight = -0.5 / len(short_symbols) if short_symbols else 0

        # Liquidate existing positions
        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)
                self.highest_prices[holding.Symbol] = 0  # Reset highest price


        for symbol in long_symbols:
            self.SetHoldings(symbol, long_weight)
            self.highest_prices[symbol] = data[symbol].Close  # Initialize highest price

        for symbol in short_symbols:
            self.SetHoldings(symbol, short_weight)
            self.highest_prices[symbol] = data[symbol].Close  # Initialize highest price

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")

    def UpdateTrailingStops(self, data):
        """
        Updates the trailing stop loss for each held security.
        """
        for symbol, holding in self.Portfolio.items():
            if holding.Invested and data.ContainsKey(symbol) and data[symbol]:
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
                        self.highest_prices[symbol] = 0 #reset