from AlgorithmImports import *

class MultiAssetLongShortImproved(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 12, 1)
        self.SetEndDate(2025, 4, 15)
        self.SetCash(100000)

        tickers = ["TSLA", "SPY", "AAPL", "MSFT", "NVDA"]  # Reduced ticker list for faster backtesting
        self.symbols = [self.AddEquity(t, Resolution.MINUTE).Symbol for t in tickers]

        # Indicator and trade management dictionaries
        self.macd = {}
        self.rsi = {}
        self.ema100 = {}
        self.ema200 = {}
        self.atr = {}

        self.entry_price = {}
        self.position_direction = {}
        self.stop_loss = {}
        self.take_profit = {}
        self.last_trade_time = {}

        # Parameters (same for all, can be made symbol-specific if desired)
        self.fast_period = 8
        self.slow_period = 18
        self.signal_period = 6

        self.rsi_period = 9
        self.ema100_period = 100
        self.ema200_period = 200
        self.atr_period = 10

        self.long_macd_threshold = 0.03
        self.short_macd_threshold = -0.03
        self.rsi_oversold = 35
        self.rsi_overbought = 65

        self.max_risk_per_trade = 0.01
        self.min_trade_size = 0.05
        self.atr_stop_loss_mult = 2.0
        self.atr_take_profit_mult = 3.0

        self.trade_cooldown = timedelta(minutes=1)
        self.max_drawdown_pct = 0.10
        self.equity_peak = self.Portfolio.TotalPortfolioValue

        # Rolling Window for Volatility Calculation
        self.lookback = 20  # Lookback period for volatility
        self.price_history = {symbol: RollingWindow[float](self.lookback) for symbol in self.symbols}
        self.returns_history = {symbol: RollingWindow[float](self.lookback) for symbol in self.symbols} #Rolling window for returns

        # Trailing stop loss percentage (adjust as needed)
        self.trailing_stop_percentage = 0.01  # 1% trailing stop

        # Flag to prevent trading during high volatility
        self.high_volatility_threshold = 0.05 #example threshold, tune this
        self.avoid_high_volatility = True  # Enable/disable high volatility filter

        # Add flag for trend confirmation
        self.trend_confirmation = {} #Stores the EMA trend status

        for symbol in self.symbols:
            self.macd[symbol] = self.MACD(symbol, self.fast_period, self.slow_period, self.signal_period, MovingAverageType.Exponential, Resolution.MINUTE)
            self.rsi[symbol] = self.RSI(symbol, self.rsi_period, MovingAverageType.Simple, Resolution.MINUTE)
            self.ema100[symbol] = self.EMA(symbol, self.ema100_period, Resolution.MINUTE)
            self.ema200[symbol] = self.EMA(symbol, self.ema200_period, Resolution.MINUTE)
            self.atr[symbol] = self.ATR(symbol, self.atr_period, MovingAverageType.Simple, Resolution.MINUTE)
            self.entry_price[symbol] = None
            self.position_direction[symbol] = 0
            self.stop_loss[symbol] = None
            self.take_profit[symbol] = None
            self.last_trade_time[symbol] = datetime.min
            self.price_history[symbol] = RollingWindow[float](self.lookback)
            self.returns_history[symbol] = RollingWindow[float](self.lookback)
            self.trend_confirmation[symbol] = 0 #Initialize trend flag

    def OnData(self, data):
        # Max drawdown protection
        current_equity = self.Portfolio.TotalPortfolioValue
        if current_equity > self.equity_peak:
            self.equity_peak = current_equity
        drawdown = (self.equity_peak - current_equity) / self.equity_peak
        if drawdown > self.max_drawdown_pct:
            self.Liquidate()
            self.Debug(f"Max drawdown exceeded. Liquidating all positions.")
            # Reset all position tracking
            for symbol in self.symbols:
                self._reset_position(symbol)
            return

        for symbol in self.symbols:
            # Data and indicators ready?
            if not (self.macd[symbol].IsReady and self.rsi[symbol].IsReady and self.ema100[symbol].IsReady and self.ema200[symbol].IsReady and self.atr[symbol].IsReady):
                continue
            if symbol not in data or not data[symbol]:
                continue

            price = data[symbol].Close
            self.price_history[symbol].Add(price)  # Add the current price to the rolling window
            if self.price_history[symbol].Samples < self.lookback:
                continue # Not enough data yet

            # Calculate returns and add to the rolling window
            if self.price_history[symbol].Samples > 1:
                previous_price = list(self.price_history[symbol])[-2] #Get the previous price
                returns = (price - previous_price) / previous_price
                self.returns_history[symbol].Add(returns)

            macd_hist = self.macd[symbol].Histogram.Current.Value
            rsi_val = self.rsi[symbol].Current.Value
            ema100_val = self.ema100[symbol].Current.Value
            ema200_val = self.ema200[symbol].Current.Value
            atr_val = self.atr[symbol].Current.Value

            long_position = self.Portfolio[symbol].IsLong
            short_position = self.Portfolio[symbol].IsShort

            uptrend = price > ema100_val and ema100_val > ema200_val
            downtrend = price < ema100_val and ema100_val < ema200_val

            # Volatility calculation using the rolling window of returns
            if self.returns_history[symbol].Samples >= self.lookback:
                volatility = np.std(list(self.returns_history[symbol]))
            else:
                volatility = 0.01  # Default value if not enough returns are available

            # Dynamic position sizing based on volatility
            total_equity = self.Portfolio.TotalPortfolioValue
            position_size = self.CalculatePositionSize(symbol, volatility, price, total_equity) # New position sizing

            position_size = max(position_size, self.min_trade_size)

            now = self.Time

            #High volatility filter
            if self.avoid_high_volatility and volatility > self.high_volatility_threshold:
                continue #skip trading during high volatility

            # Entry Logic with cooldown
            if (now - self.last_trade_time[symbol]) > self.trade_cooldown:
                # Long Condition
                if (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend):
                    if not long_position:
                        self.SetHoldings(symbol, position_size)
                        self.Debug(f"{symbol.Value} Going Long: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = 1
                        self.stop_loss[symbol] = price - self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price + self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now
                        self.trend_confirmation[symbol] = 1

                # Short Condition
                elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend):
                    if not short_position:
                        self.SetHoldings(symbol, -position_size)
                        self.Debug(f"{symbol.Value} Going Short: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = -1
                        self.stop_loss[symbol] = price + self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price - self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now
                        self.trend_confirmation[symbol] = -1

            # Exit Logic
            # Long Exits
            if long_position and self.position_direction[symbol] == 1:
                # Trailing Stop Loss
                self.stop_loss[symbol] = max(self.stop_loss[symbol], price * (1 - self.trailing_stop_percentage))

                if price <= self.stop_loss[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Stop Loss Triggered at {price:.2f}")
                    self._reset_position(symbol)
                    self.trend_confirmation[symbol] = 0 #Reset trend
                elif price >= self.take_profit[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Take Profit Triggered at {price:.2f}")
                    self._reset_position(symbol)
                    self.trend_confirmation[symbol] = 0 #Reset trend
                elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend):
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Exit: Signal flip to Short at {price:.2f}")
                    self._reset_position(symbol)
                    self.trend_confirmation[symbol] = 0 #Reset trend

            # Short Exits
            if short_position and self.position_direction[symbol] == -1:
                # Trailing Stop Loss
                self.stop_loss[symbol] = min(self.stop_loss[symbol], price * (1 + self.trailing_stop_percentage))

                if price >= self.stop_loss[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Stop Loss Triggered at {price:.2f}")
                    self._reset_position(symbol)
                    self.trend_confirmation[symbol] = 0 #Reset trend
                elif price <= self.take_profit[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Take Profit Triggered at {price:.2f}")
                    self._reset_position(symbol)
                    self.trend_confirmation[symbol] = 0 #Reset trend
                elif (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend):
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Exit: Signal flip to Long at {price:.2f}")
                    self._reset_position(symbol)
                    self.trend_confirmation[symbol] = 0 #Reset trend

    def _reset_position(self, symbol):
        self.entry_price[symbol] = None
        self.position_direction[symbol] = 0
        self.stop_loss[symbol] = None
        self.take_profit[symbol] = None

    def OnOrderEvent(self, orderEvent):
        self.Debug(str(orderEvent))

    def CalculatePositionSize(self, symbol, volatility, price, total_equity):
        """Calculates the position size based on volatility and ATR."""
        atr_val = self.atr[symbol].Current.Value
        risk_per_share = atr_val * self.atr_stop_loss_mult
        #risk_per_share = price * volatility  #Alternative volatility based risk
        position_size = min(self.max_risk_per_trade * total_equity / risk_per_share, 1)
        return position_size