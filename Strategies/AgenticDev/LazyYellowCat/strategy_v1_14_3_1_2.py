from AlgorithmImports import *

class ImprovedLongShortEquityStrategyV4(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)

        # Add more symbols for increased trading opportunities, including diverse sectors
        self.symbols = [
            self.AddEquity("SPY", Resolution.DAILY).Symbol,  # Broad Market
            self.AddEquity("AAPL", Resolution.DAILY).Symbol,  # Tech
            self.AddEquity("MSFT", Resolution.DAILY).Symbol,  # Tech
            self.AddEquity("NVDA", Resolution.DAILY).Symbol,  # Tech
            self.AddEquity("GOOGL", Resolution.DAILY).Symbol, # Tech
            self.AddEquity("AMZN", Resolution.DAILY).Symbol,  # Consumer Discretionary
            self.AddEquity("TSLA", Resolution.DAILY).Symbol,  # Consumer Discretionary
            self.AddEquity("META", Resolution.DAILY).Symbol,  # Tech
            self.AddEquity("JPM", Resolution.DAILY).Symbol,   # Financials
            self.AddEquity("XOM", Resolution.DAILY).Symbol,   # Energy
            self.AddEquity("UNH", Resolution.DAILY).Symbol,   # Healthcare
            self.AddEquity("BAC", Resolution.DAILY).Symbol,   #Financials
            self.AddEquity("V", Resolution.DAILY).Symbol    # Financials
        ]

        self.lookback = 15  # Shorten lookback for more responsive momentum
        self.rebalance_frequency = timedelta(days=2)  # Rebalance more frequently
        self.last_rebalance = datetime.min

        self.momentum = {}

        self.SetWarmUp(self.lookback)  # Corrected typo here

        # Volatility filter parameters - loosened slightly
        self.volatility_lookback = 15  # Shorter lookback for volatility
        self.volatility_threshold = 0.45  # Maximum allowed volatility (annualized) - loosened

        # EMA filter
        self.ema_fast_period = 5
        self.ema_slow_period = 20
        self.ema = {}
        for symbol in self.symbols:
            self.ema[symbol] = self.EMA(symbol, self.ema_fast_period, self.ema_slow_period, Resolution.DAILY)

        #ADX Filter
        self.adx_period = 14
        self.adx = {}
        for symbol in self.symbols:
            self.adx[symbol] = self.ADX(symbol, self.adx_period, Resolution.DAILY)

        #ATR Risk Management
        self.atr_period = 14
        self.atr_multiplier = 2 # Adjust this based on risk tolerance
        self.atr = {}
        for symbol in self.symbols:
            self.atr[symbol] = self.ATR(symbol, self.atr_period, Resolution.DAILY)

    def OnData(self, data):
        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.RebalancePortfolio(data)
        self.last_rebalance = self.Time

    def CalculateMomentum(self, data):
        """
        Calculates the momentum score for each symbol based on historical returns.
        """
        for symbol in self.symbols:
            if not data.ContainsKey(symbol) or not data[symbol] or data[symbol].Close <= 0:
                #self.Log(f"No valid data for {symbol} at {self.Time}. Skipping momentum calculation for {symbol}.")
                continue

            history = self.History(symbol, self.lookback, Resolution.DAILY)

            if history.empty:
                #self.Log(f"No history data for {symbol}. Skipping momentum calculation for {symbol}.")
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
        Adjusts portfolio holdings based on momentum scores, volatility, EMA filter, and ADX.
        Longs the top stocks and shorts the bottom. Number of long/short positions depends on how many stocks meet criteria.
        """
        if not self.momentum:
            #self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = []
        short_symbols = []

        # Use a smaller ADX threshold to allow more trades.
        adx_threshold = 20

        # Adjust EMA cross condition to be more sensitive.  Use the current values directly instead of history.
        for symbol, _ in sorted_symbols:
            if not (data.ContainsKey(symbol) and self.ema[symbol].IsReady and self.adx[symbol].IsReady):
                continue

            volatility = self.CalculateVolatility(symbol)
            adx_value = self.adx[symbol].Current.Value
            fast_ema = self.ema[symbol].Fast.Current.Value
            slow_ema = self.ema[symbol].Slow.Current.Value
            current_price = data[symbol].Close

            #Long Condition
            if (volatility < self.volatility_threshold and
                fast_ema > slow_ema and #EMA crossover condition
                adx_value > adx_threshold):
                long_symbols.append(symbol)
                #self.Debug(f"Long {symbol} - Volatility: {volatility:.2f}, ADX: {adx_value:.2f}, Fast EMA: {fast_ema:.2f}, Slow EMA: {slow_ema:.2f}, Price: {current_price}")
            #Short Condition
            elif (volatility < self.volatility_threshold and
                  fast_ema < slow_ema and #EMA crossover condition
                  adx_value > adx_threshold):
                short_symbols.append(symbol)
                #self.Debug(f"Short {symbol} - Volatility: {volatility:.2f}, ADX: {adx_value:.2f}, Fast EMA: {fast_ema:.2f}, Slow EMA: {slow_ema:.2f}, Price: {current_price}")
            #else:
                #self.Debug(f"Skipping {symbol} - Volatility: {volatility:.2f}, ADX: {adx_value:.2f}, Fast EMA: {fast_ema:.2f}, Slow EMA: {slow_ema:.2f}, Price: {current_price}")

        # Calculate weights based on the number of long and short positions. Avoid division by zero.
        num_long = len(long_symbols)
        num_short = len(short_symbols)

        total_positions = num_long + num_short
        if total_positions == 0:
            return  # No positions to take

        long_weight = 0.5 / num_long if num_long > 0 else 0
        short_weight = -0.5 / num_short if num_short > 0 else 0


        # Liquidate existing positions
        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)

        # Set holdings and ATR stop loss
        for symbol in long_symbols:
            self.SetHoldings(symbol, long_weight)
            atr_value = self.atr[symbol].Current.Value
            stop_loss_price = data[symbol].Close - self.atr_multiplier * atr_value
            self.StopMarketOrder(symbol, -self.Portfolio[symbol].Quantity, stop_loss_price)
            #self.Debug(f"Set long {symbol} with ATR stop loss at {stop_loss_price}")

        for symbol in short_symbols:
            self.SetHoldings(symbol, short_weight)
            atr_value = self.atr[symbol].Current.Value
            stop_loss_price = data[symbol].Close + self.atr_multiplier * atr_value
            self.StopMarketOrder(symbol, -self.Portfolio[symbol].Quantity, stop_loss_price)
            #self.Debug(f"Set short {symbol} with ATR stop loss at {stop_loss_price}")


    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")