from AlgorithmImports import *
import numpy as np

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
        self.holding_time = {} # track holding time

        # Parameters
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

        # Rolling Window for Volatility Calculation and price momentum
        self.lookback = 20
        self.price_history = {symbol: RollingWindow[float](self.lookback) for symbol in self.symbols}
        self.momentum = {}

        # Volatility & Correlation Filter
        self.volatility = {}
        self.correlation_window = 60 # Lookback for correlation
        self.correlation = {} # Store correlation values

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
            self.momentum[symbol] = 0.0 # Initialize momentum
            self.volatility[symbol] = 0.0 # Initialize volatility
            self.correlation[symbol] = 0.0 # Initialize Correlation
            self.holding_time[symbol] = None # Initialize holding time

        # Warmup Correlation
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(0, 0), self.CalculateCorrelations)
        self.correlation_data = {}

    def OnData(self, data):
        # Max drawdown protection
        current_equity = self.Portfolio.TotalPortfolioValue
        if current_equity > self.equity_peak:
            self.equity_peak = current_equity
        drawdown = (self.equity_peak - current_equity) / self.equity_peak
        if drawdown > self.max_drawdown_pct:
            self.Liquidate()
            self.Debug(f"Max drawdown exceeded. Liquidating all positions.")
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
            self.price_history[symbol].Add(price)
            if self.price_history[symbol].Samples < self.lookback:
                continue

            macd_hist = self.macd[symbol].Histogram.Current.Value
            rsi_val = self.rsi[symbol].Current.Value
            ema100_val = self.ema100[symbol].Current.Value
            ema200_val = self.ema200[symbol].Current.Value
            atr_val = self.atr[symbol].Current.Value

            long_position = self.Portfolio[symbol].IsLong
            short_position = self.Portfolio[symbol].IsShort

            uptrend = price > ema100_val
            downtrend = price < ema100_val

            # Volatility calculation using the rolling window
            returns = np.diff(list(self.price_history[symbol]))
            if len(returns) > 0:
                self.volatility[symbol] = np.std(returns)
            else:
                self.volatility[symbol] = 0.01

            # Calculate momentum
            self.momentum[symbol] = (price - list(self.price_history[symbol])[-1]) / list(self.price_history[symbol])[-1] if list(self.price_history[symbol])[-1] != 0 else 0

            # Dynamic position sizing based on volatility
            total_equity = self.Portfolio.TotalPortfolioValue
            position_size = min(self.max_risk_per_trade * total_equity / (price * self.volatility[symbol]), 1)
            position_size = max(position_size, self.min_trade_size)

            now = self.Time

            # Correlation Filter: Avoid correlated trades
            if abs(self.correlation[symbol]) > 0.7: # Adjustable threshold
                continue

            # Entry Logic with cooldown
            if (now - self.last_trade_time[symbol]) > self.trade_cooldown:

                # Long Condition
                if (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend and self.momentum[symbol] > 0): #Added momentum filter
                    if not long_position:
                        self.SetHoldings(symbol, position_size)
                        self.Debug(f"{symbol.Value} Going Long: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}, Momentum: {self.momentum[symbol]:.4f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = 1
                        self.stop_loss[symbol] = price - self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price + self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now
                        self.holding_time[symbol] = now # Start tracking holding time

                # Short Condition
                elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend and self.momentum[symbol] < 0): # Added momentum filter
                    if not short_position:
                        self.SetHoldings(symbol, -position_size)
                        self.Debug(f"{symbol.Value} Going Short: MACD Hist: {macd_hist:.4f}, RSI: {rsi_val:.2f}, Price: {price}, EMA100: {ema100_val:.2f}, Momentum: {self.momentum[symbol]:.4f}")
                        self.entry_price[symbol] = price
                        self.position_direction[symbol] = -1
                        self.stop_loss[symbol] = price + self.atr_stop_loss_mult * atr_val
                        self.take_profit[symbol] = price - self.atr_take_profit_mult * atr_val
                        self.last_trade_time[symbol] = now
                        self.holding_time[symbol] = now # Start tracking holding time

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
                elif (macd_hist < self.short_macd_threshold and rsi_val > self.rsi_overbought and downtrend):
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Exit: Signal flip to Short at {price:.2f}")
                    self._reset_position(symbol)
                # Time-based Exit
                elif (now - self.holding_time[symbol]) > timedelta(hours=4):  # Hold for maximum 4 hours
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Long Exit: Holding time exceeded at {price:.2f}")
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
                elif (macd_hist > self.long_macd_threshold and rsi_val < self.rsi_oversold and uptrend):
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Exit: Signal flip to Long at {price:.2f}")
                    self._reset_position(symbol)
                # Time-based Exit
                elif (now - self.holding_time[symbol]) > timedelta(hours=4):  # Hold for maximum 4 hours
                    self.Liquidate(symbol)
                    self.Debug(f"{symbol.Value} Short Exit: Holding time exceeded at {price:.2f}")
                    self._reset_position(symbol)


    def _reset_position(self, symbol):
        self.entry_price[symbol] = None
        self.position_direction[symbol] = 0
        self.stop_loss[symbol] = None
        self.take_profit[symbol] = None
        self.holding_time[symbol] = None # Reset holding time


    def OnOrderEvent(self, orderEvent):
        self.Debug(str(orderEvent))

    def CalculateCorrelations(self):
        # Fetch historical data for correlation calculation
        history = self.History(self.symbols, self.correlation_window, Resolution.MINUTE)

        if history.empty:
            self.Debug("Not enough history data to calculate correlations.")
            return

        # Organize data into a dictionary for easier handling
        for symbol in self.symbols:
            self.correlation_data[symbol] = history.loc[symbol].close.values

        # Calculate correlations between all pairs of assets
        for i in range(len(self.symbols)):
            for j in range(i + 1, len(self.symbols)):
                symbol1 = self.symbols[i]
                symbol2 = self.symbols[j]

                # Ensure data is available for both symbols
                if symbol1 in self.correlation_data and symbol2 in self.correlation_data:
                    # Calculate the correlation
                    correlation = np.corrcoef(self.correlation_data[symbol1], self.correlation_data[symbol2])[0, 1]
                    # Store the correlation value - choose one symbol to represent the pair
                    self.correlation[symbol1] = correlation
                    self.correlation[symbol2] = correlation

                    self.Debug(f"Correlation between {symbol1} and {symbol2}: {correlation:.2f}")
                else:
                    self.Debug(f"Missing data for {symbol1} or {symbol2}, cannot calculate correlation.")