from AlgorithmImports import *

class MultiAssetLongShortImproved(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2023, 12, 1)
        self.SetEndDate(2025, 4, 15)
        self.SetCash(100000)

        tickers = ["AAPL"]  # Consider adding/removing tickers based on performance
        self.symbols = [self.AddEquity(t, Resolution.MINUTE).Symbol for t in tickers]

        # Indicator and trade management dictionaries
        self.macd = {}
        self.rsi = {}
        self.ema100 = {}
        self.ema200 = {}
        self.atr = {}
        self.bb = {}  # Bollinger Bands

        self.entry_price = {}
        self.position_direction = {}
        self.stop_loss = {}
        self.take_profit = {}
        self.last_trade_time = {}

        # Parameters (Optimized)
        self.fast_period = 12  # Adjusted for potentially smoother signals
        self.slow_period = 26  # Adjusted for potentially smoother signals
        self.signal_period = 9  # Standard MACD signal period

        self.rsi_period = 14  # Standard RSI period
        self.ema100_period = 100
        self.ema200_period = 200
        self.atr_period = 14  # Standard ATR period
        self.bb_period = 20   # Standard Bollinger Band period
        self.bb_std = 2.0      # Standard Deviations for BB

        self.long_macd_threshold = 0.01  # Tightened for more selective entries
        self.short_macd_threshold = -0.01 # Tightened for more selective entries
        self.rsi_oversold = 30  # More aggressive oversold
        self.rsi_overbought = 70 # More aggressive overbought

        self.max_risk_per_trade = 0.0075  # Reduced risk per trade
        self.min_trade_size = 0.05
        self.atr_stop_loss_mult = 1.5  # Tighter stop loss
        self.atr_take_profit_mult = 2.5  # Reduced take profit

        self.trade_cooldown = timedelta(minutes=2) # Increased cooldown
        self.max_drawdown_pct = 0.075 # Reduced drawdown limit
        self.equity_peak = self.Portfolio.TotalPortfolioValue
        self.rebalance_time = datetime.min # Rebalancing

        for symbol in self.symbols:
            self.macd[symbol] = self.MACD(symbol, self.fast_period, self.slow_period, self.signal_period, MovingAverageType.Exponential, Resolution.MINUTE)
            self.rsi[symbol] = self.RSI(symbol, self.rsi_period, MovingAverageType.Simple, Resolution.MINUTE)
            self.ema100[symbol] = self.EMA(symbol, self.ema100_period, Resolution.MINUTE)
            self.ema200[symbol] = self.EMA(symbol, self.ema200_period, Resolution.MINUTE)
            self.atr[symbol] = self.ATR(symbol, self.atr_period, MovingAverageType.Simple, Resolution.MINUTE)
            self.bb[symbol] = self.BB(symbol, self.bb_period, self.bb_std, MovingAverageType.Simple, Resolution.MINUTE)

            self.entry_price[symbol] = None
            self.position_direction[symbol] = 0
            self.stop_loss[symbol] = None
            self.take_profit[symbol] = None
            self.last_trade_time[symbol] = datetime.min

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
            if not (self.macd[symbol].IsReady and self.rsi[symbol].IsReady and self.ema100[symbol].IsReady and self.ema200[symbol].IsReady and self.atr[symbol].IsReady and self.bb[symbol].IsReady):
                continue
            if symbol not in data or not data[symbol]:
                continue

            price = data[symbol].Close
            macd_hist = self.macd[symbol].Histogram.Current.Value
            rsi_val = self.rsi[symbol].Current.Value
            ema100_val = self.ema100[symbol].Current.Value
            ema200_val = self.ema200[symbol].Current.Value
            atr_val = self.atr[symbol].Current.Value
            bb_upper = self.bb[symbol].UpperBand.Current.Value
            bb_lower = self.bb[symbol].LowerBand.Current.Value

            long_position = self.Portfolio[symbol].IsLong
            short_position = self.Portfolio[symbol].IsShort

            uptrend = price > ema100_val and ema100_val > ema200_val # Added 200 EMA check
            downtrend = price < ema100_val and ema100_val < ema200_val # Added 200 EMA check

            # Position sizing
            if atr_val > 0:
                risk_per_share = atr_val * self.atr_stop_loss_mult
                total_equity = self.Portfolio.TotalPortfolioValue
                position_size = min(self.max_risk_per_trade * total_equity / risk_per_share, 1)
                position_size = max(position_size, self.min_trade_size)
            else:
                position_size = self.min_trade_size

            now = self.Time

            # Entry Logic with cooldown
            if (now - self.last_trade_time[symbol]) > self.trade_cooldown:
                # Long Condition - Added BB Lower band confirmation
                if (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend and price < bb_lower):
                    if not long_position:
                        self.SetHoldings(symbol, position_size)
                        self.Debug(f"{symbol.Value} Going Long: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}, BB_Lower: {bb_lower:.2f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = 1
                        self.stop_loss[symbol] = price - self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price + self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now

                # Short Condition - Added BB Upper Band confirmation
                elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend and price > bb_upper):
                    if not short_position:
                        self.SetHoldings(symbol, -position_size)
                        self.Debug(f"{symbol.Value} Going Short: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}, BB_Upper: {bb_upper:.2f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = -1
                        self.stop_loss[symbol] = price + self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price - self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now

            # Exit Logic
            # Long Exits
            if long_position and self.position_direction[symbol] == 1:
                if price <= self.stop_loss[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Stop Loss Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif price >= self.take_profit[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Take Profit Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend): # Exit when signal flips
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Exit: Signal flip to Short at {price:.2f}")
                    self._reset_position(symbol)
                elif price > bb_upper: # Exit when price is above upper Bollinger Band
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Exit: Price above Upper BB at {price:.2f}")
                    self._reset_position(symbol)

            # Short Exits
            if short_position and self.position_direction[symbol] == -1:
                if price >= self.stop_loss[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Stop Loss Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif price <= self.take_profit[symbol]:
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Take Profit Triggered at {price:.2f}")
                    self._reset_position(symbol)
                elif (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend): # Exit when signal flips
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Exit: Signal flip to Long at {price:.2f}")
                    self._reset_position(symbol)
                elif price < bb_lower: # Exit when price is below lower Bollinger Band
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Exit: Price below Lower BB at {price:.2f}")
                    self._reset_position(symbol)

    def _reset_position(self, symbol):
        self.entry_price[symbol] = None
        self.position_direction[symbol] = 0
        self.stop_loss[symbol] = None
        self.take_profit[symbol] = None

    def OnOrderEvent(self, orderEvent):
        self.Debug(str(orderEvent))