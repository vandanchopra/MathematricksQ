from AlgorithmImports import *

class MultiAssetLongShort(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 12, 1)
        self.SetEndDate(2025, 4, 15)
        self.SetCash(100000)

        tickers = ["TSLA", "SPY", "AAPL", "MSFT", "NVDA"]
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

        # Add volatility filter
        self.volatility = {}
        self.volatility_period = 20  # Lookback period for volatility calculation
        self.volatility_threshold = 0.5  # Threshold for volatility (adjust as needed)

        # Initialize indicators and dictionaries
        for symbol in self.symbols:
            self.macd[symbol] = self.MACD(symbol, self.fast_period, self.slow_period, self.signal_period, MovingAverageType.Exponential, Resolution.MINUTE)
            self.rsi[symbol] = self.RSI(symbol, self.rsi_period, MovingAverageType.Simple, Resolution.MINUTE)
            self.ema100[symbol] = self.EMA(symbol, self.ema100_period, Resolution.MINUTE)
            self.ema200[symbol] = self.EMA(symbol, self.ema200_period, Resolution.MINUTE)
            self.atr[symbol] = self.ATR(symbol, self.atr_period, MovingAverageType.Simple, Resolution.MINUTE)

            self.entry_price[symbol] = 0.0  # Initialize to a float value
            self.position_direction[symbol] = 0
            self.stop_loss[symbol] = 0.0 # Initialize to a float value
            self.take_profit[symbol] = 0.0 # Initialize to a float value
            self.last_trade_time[symbol] = datetime.min

            # Initialize volatility
            self.volatility[symbol] = RollingWindow[float](self.volatility_period)

        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(15, 50), self.LiquidatePositions)


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
            macd_hist = self.macd[symbol].Histogram.Current.Value
            rsi_val = self.rsi[symbol].Current.Value
            ema100_val = self.ema100[symbol].Current.Value
            ema200_val = self.ema200[symbol].Current.Value
            atr_val = self.atr[symbol].Current.Value

            long_position = self.Portfolio[symbol].IsLong
            short_position = self.Portfolio[symbol].IsShort

            uptrend = price > ema100_val
            downtrend = price < ema100_val

            # Update volatility
            log_return = np.log(price / data[symbol].Open) if data[symbol].Open != 0 else 0 # Avoid division by zero
            self.volatility[symbol].Add(log_return)

            # Position sizing
            if atr_val > 0:
                risk_per_share = atr_val * self.atr_stop_loss_mult
                total_equity = self.Portfolio.TotalPortfolioValue
                position_size = min(self.max_risk_per_trade * total_equity / risk_per_share, 1)
                position_size = max(position_size, self.min_trade_size)
            else:
                position_size = self.min_trade_size

            now = self.Time

            # Entry Logic with cooldown and volatility filter
            if (now - self.last_trade_time[symbol]) > self.trade_cooldown:
                # Calculate volatility (standard deviation of log returns)
                if self.volatility[symbol].IsReady:
                    volatility = np.std(list(self.volatility[symbol]))
                else:
                    volatility = 0.0  # Or some default value

                # Volatility Filter: Only trade if volatility is below threshold
                if volatility < self.volatility_threshold:  # Adjust threshold as needed

                    # Long Condition
                    if (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend and not long_position):
                        self.SetHoldings(symbol, position_size)
                        self.Debug(f"{symbol.Value} Going Long: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}, Volatility: {volatility:.4f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = 1
                        self.stop_loss[symbol] = price - self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price + self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now

                    # Short Condition
                    elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend and not short_position):
                        self.SetHoldings(symbol, -position_size)
                        self.Debug(f"{symbol.Value} Going Short: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}, Volatility: {volatility:.4f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = -1
                        self.stop_loss[symbol] = price + self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price - self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now

            # Exit Logic
            if long_position and self.position_direction[symbol] == 1:
                if price <= self.stop_loss[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Stop Loss Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif price >= self.take_profit[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Take Profit Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend):
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Exit: Signal flip to Short at {price:.2f}")
                    self._reset_position(symbol)

            if short_position and self.position_direction[symbol] == -1:
                if price >= self.stop_loss[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Stop Loss Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif price <= self.take_profit[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Take Profit Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend):
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Exit: Signal flip to Long at {price:.2f}")
                    self._reset_position(symbol)

    def _reset_position(self, symbol):
        self.entry_price[symbol] = 0.0
        self.position_direction[symbol] = 0
        self.stop_loss[symbol] = 0.0
        self.take_profit[symbol] = 0.0
        self.last_trade_time[symbol] = datetime.min # Reset trade time

    def OnOrderEvent(self, orderEvent):
        self.Debug(str(orderEvent))

    def LiquidatePositions(self):
        for symbol in self.symbols:
            if self.Portfolio[symbol].Invested:
                self.Liquidate(symbol)
                self.Debug(f"Scheduled liquidation of {symbol}")
                self._reset_position(symbol)