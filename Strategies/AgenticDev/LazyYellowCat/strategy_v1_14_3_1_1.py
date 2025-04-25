from AlgorithmImports import *

class ImprovedLongShortEquityStrategyV5(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)

        # Add more trading pairs - Increased number of symbols
        self.symbols = [
            self.AddEquity("SPY", Resolution.DAILY).Symbol,
            self.AddEquity("AAPL", Resolution.DAILY).Symbol,
            self.AddEquity("MSFT", Resolution.DAILY).Symbol,
            self.AddEquity("NVDA", Resolution.DAILY).Symbol,
            self.AddEquity("GOOGL", Resolution.DAILY).Symbol,
            self.AddEquity("AMZN", Resolution.DAILY).Symbol,
            self.AddEquity("TSLA", Resolution.DAILY).Symbol,
            self.AddEquity("JPM", Resolution.DAILY).Symbol,
            self.AddEquity("XOM", Resolution.DAILY).Symbol,
            self.AddEquity("META", Resolution.DAILY).Symbol,
            self.AddEquity("UNH", Resolution.DAILY).Symbol,
            self.AddEquity("JNJ", Resolution.DAILY).Symbol,
            self.AddEquity("V", Resolution.DAILY).Symbol,    # Added Visa
            self.AddEquity("PG", Resolution.DAILY).Symbol,   # Added Proctor & Gamble
            self.AddEquity("HD", Resolution.DAILY).Symbol    # Added Home Depot
        ]

        self.lookback = 10  # Further reduced lookback to react faster
        self.rebalance_frequency = timedelta(days=1)  # Increased rebalancing frequency even more
        self.last_rebalance = datetime.min

        self.momentum = {}

        self.SetWarmUp(self.lookback)

        # Volatility filter parameters
        self.volatility_lookback = 10  # Reduced lookback for faster volatility response
        self.volatility_threshold = 0.60  # Increased volatility threshold to allow more trades

        # EMA filter parameters
        self.ema_fast_period = 3  # Further reduced EMA periods for faster response
        self.ema_slow_period = 7  # Further reduced EMA periods for faster response
        self.ema = {} # Dictionary to store EMA indicators

        # Initialize EMA indicators
        for symbol in self.symbols:
            self.ema[symbol] = self.EMA(symbol, self.ema_fast_period, Resolution.DAILY)

        #ADX Filter
        self.adx_period = 7  # Reduced ADX period for faster response
        self.adx = {}
        for symbol in self.symbols:
            self.adx[symbol] = self.ADX(symbol, self.adx_period, Resolution.DAILY)

        #ATR Risk Management
        self.atr_period = 7  # Reduced ATR period for faster response
        self.atr_multiplier = 1.3  # Adjust this based on risk tolerance - reduced for more trades
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
                continue

            history = self.History(symbol, self.lookback, Resolution.DAILY)

            if history.empty:
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
        Longs the top N momentum stocks and shorts the bottom N.  Adjust N based on number of symbols.
        """
        if not self.momentum:
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        num_long_short = min(5, len(self.symbols) // 2) # Increased number of long/short positions. Limit to 5.

        long_symbols = []
        short_symbols = []

        for symbol, _ in sorted_symbols[:num_long_short]:  # Top N momentum
            volatility = self.CalculateVolatility(symbol)
            adx_value = self.adx[symbol].Current.Value
            #Loosen entry conditions: Require that the fast EMA is above a percentage of the slow EMA AND ADX > 15.
            ema_fast = self.ema[symbol].Current.Value
            ema_slow = self.ema[symbol].Samples[0]  # Access the last value of the slow EMA
            if volatility < self.volatility_threshold and ema_fast > (0.96 * ema_slow) and adx_value > 15: #Reduced ADX requirement, reduced EMA threshold
                long_symbols.append(symbol)
                self.Debug(f"Long {symbol} ADX: {adx_value}")
            else:
                 self.Debug(f"Skipping long {symbol} due to high volatility ({volatility:.2f}), EMA filter or low ADX ({adx_value:.2f}). EMA Fast: {ema_fast}, EMA Slow: {ema_slow}")

        for symbol, _ in sorted_symbols[-num_long_short:]:  # Bottom N momentum
            volatility = self.CalculateVolatility(symbol)
            adx_value = self.adx[symbol].Current.Value
            #Loosen entry conditions: Require that the fast EMA is below a percentage of the slow EMA AND ADX > 15.
            ema_fast = self.ema[symbol].Current.Value
            ema_slow = self.ema[symbol].Samples[0] # Access the last value of the slow EMA
            if volatility < self.volatility_threshold and ema_fast < (1.04 * ema_slow) and adx_value > 15: #Reduced ADX requirement, increased EMA threshold
                short_symbols.append(symbol)
                self.Debug(f"Short {symbol} ADX: {adx_value}")
            else:
                 self.Debug(f"Skipping short {symbol} due to high volatility ({volatility:.2f}), EMA filter, or low ADX ({adx_value:.2f}). EMA Fast: {ema_fast}, EMA Slow: {ema_slow}")


        long_weight = 0.5 / len(long_symbols) if long_symbols else 0
        short_weight = -0.5 / len(short_symbols) if short_symbols else 0

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
            self.Debug(f"Set long {symbol} with ATR stop loss at {stop_loss_price}")

        for symbol in short_symbols:
            self.SetHoldings(symbol, short_weight)
            atr_value = self.atr[symbol].Current.Value
            stop_loss_price = data[symbol].Close + self.atr_multiplier * atr_value
            self.StopMarketOrder(symbol, -self.Portfolio[symbol].Quantity, stop_loss_price)
            self.Debug(f"Set short {symbol} with ATR stop loss at {stop_loss_price}")


    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")