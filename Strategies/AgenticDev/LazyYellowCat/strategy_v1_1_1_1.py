from AlgorithmImports import *

class LongShortEquityStrategyImproved(QCAlgorithm):

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

        # Risk management parameters
        self.max_drawdown_threshold = -0.05  # Stop trading if drawdown exceeds 5%
        self.initial_portfolio_value = self.Portfolio.TotalPortfolioValue
        self.high_watermark = self.initial_portfolio_value # track the maximum value
        self.stopped_trading = False
        self.stop_loss_percentage = 0.02 # Stop loss at 2%

        # Volatility filter parameters
        self.volatility_lookback = 20  # Lookback period for volatility calculation
        self.volatility_threshold = 0.02  # Threshold for acceptable volatility

        #ATR Stop Loss parameters
        self.atr_period = 14
        self.atr_multiple = 2  # Adjust based on testing; lower values tighten the stop
        self.atr = {}

        # Correlation Filter Parameters
        self.correlation_lookback = 20
        self.max_correlation = 0.7  # Maximum allowed correlation between assets


    def OnData(self, data):

        if self.stopped_trading:
            return

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        # Risk Management: Check drawdown
        current_drawdown = (self.Portfolio.TotalPortfolioValue - self.high_watermark) / self.high_watermark
        if current_drawdown < self.max_drawdown_threshold:
            self.Log("Maximum drawdown exceeded. Liquidating positions and stopping trading.")
            self.Liquidate()
            self.stopped_trading = True
            return

        #Update high watermark
        if self.Portfolio.TotalPortfolioValue > self.high_watermark:
            self.high_watermark = self.Portfolio.TotalPortfolioValue
            self.Log(f"New high watermark: {self.high_watermark}")


        self.CalculateMomentum(data)
        self.RebalancePortfolio(data)  # Pass data to RebalancePortfolio for volatility check
        self.last_rebalance = self.Time

        #Implement Stop Loss
        self.ManageStopLosses(data)


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
            # Adjusted momentum calculation: Exponentially weighted moving average of returns
            momentum_score = returns.ewm(span=self.lookback).mean().iloc[-1]

            self.momentum[symbol] = momentum_score


    def RebalancePortfolio(self, data):
        """
        Adjusts portfolio holdings based on momentum scores, incorporating volatility and correlation filtering.
        Longs the top one momentum stocks and shorts the bottom one to reduce risk.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = [symbol for symbol, _ in sorted_symbols[:1]]  # Top 1
        short_symbols = [symbol for symbol, _ in sorted_symbols[-1:]] # Bottom 1


        # Volatility Filter:  Only trade if volatility is within acceptable limits
        tradable_longs = []
        tradable_shorts = []
        for symbol in long_symbols:
            if self.IsVolatilityAcceptable(symbol, data):
                tradable_longs.append(symbol)

        for symbol in short_symbols:
            if self.IsVolatilityAcceptable(symbol, data):
                tradable_shorts.append(symbol)

        # Correlation Filter: Check correlation between long and short positions
        tradable_longs, tradable_shorts = self.ApplyCorrelationFilter(tradable_longs, tradable_shorts)


        long_weight = 0.5 / len(tradable_longs) if tradable_longs else 0
        short_weight = -0.5 / len(tradable_shorts) if tradable_shorts else 0


        # Liquidate existing positions *before* setting new ones
        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)


        for symbol in tradable_longs:
            self.SetHoldings(symbol, long_weight)
            self.CalculateATR(symbol)  # Calculate ATR after entering position


        for symbol in tradable_shorts:
            self.SetHoldings(symbol, short_weight)
            self.CalculateATR(symbol)  # Calculate ATR after entering position



    def IsVolatilityAcceptable(self, symbol, data):
        """
        Checks if the volatility of a symbol is within acceptable limits.
        """
        history = self.History(symbol, self.volatility_lookback, Resolution.DAILY)

        if history.empty:
            self.Log(f"No history data for {symbol} to calculate volatility.")
            return False

        returns = history['close'].pct_change().dropna()
        if len(returns) < 2: # need at least 2 data points to compute stddev
            return False;

        volatility = returns.std()

        if volatility > self.volatility_threshold:
            self.Log(f"Volatility for {symbol} is too high ({volatility:.4f}). Skipping trade.")
            return False

        return True


    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")


    def ManageStopLosses(self, data):
        """
        Implements a simple stop-loss for each holding.
        """
        for holding in self.Portfolio.Values:
            if holding.Invested:
                symbol = holding.Symbol
                if data.ContainsKey(symbol) and data[symbol] is not None:
                    current_price = data[symbol].Close
                    # Long Positions
                    if holding.IsLong:
                         stop_loss_price = holding.AveragePrice - (self.atr.get(symbol, 0) * self.atr_multiple)
                         if current_price <= stop_loss_price:
                            self.Log(f"Stop loss triggered for {symbol} at price {current_price}. Selling.")
                            self.Liquidate(symbol)

                    # Short Positions
                    elif holding.IsShort:
                        stop_loss_price = holding.AveragePrice + (self.atr.get(symbol, 0) * self.atr_multiple)
                        if current_price >= stop_loss_price:
                            self.Log(f"Stop loss triggered for {symbol} at price {current_price}. Buying to cover.")
                            self.Liquidate(symbol)



    def CalculateATR(self, symbol):
        """
        Calculates the Average True Range (ATR) for a given symbol.
        """
        history = self.History(symbol, self.atr_period, Resolution.DAILY)

        if history.empty:
            self.Log(f"No history data for {symbol} to calculate ATR.")
            return

        true_range = []
        for i in range(1, len(history)):
            high = history['high'][i]
            low = history['low'][i]
            close_prev = history['close'][i-1]

            true_range.append(max(high - low, abs(high - close_prev), abs(low - close_prev)))

        atr = sum(true_range) / self.atr_period
        self.atr[symbol] = atr
        self.Log(f"ATR for {symbol}: {atr}")


    def ApplyCorrelationFilter(self, long_symbols, short_symbols):
        """
        Filters long and short symbols based on correlation to reduce risk.
        """
        if not long_symbols or not short_symbols:
            return long_symbols, short_symbols

        long_symbol = long_symbols[0]
        short_symbol = short_symbols[0]

        history_long = self.History(long_symbol, self.correlation_lookback, Resolution.DAILY)
        history_short = self.History(short_symbol, self.correlation_lookback, Resolution.DAILY)

        if history_long.empty or history_short.empty:
            return [], [] # Don't trade if history is missing

        # Calculate returns and correlation
        returns_long = history_long['close'].pct_change().dropna()
        returns_short = history_short['close'].pct_change().dropna()

        # Align the returns based on the index (dates)
        aligned_returns = returns_long.to_frame('long').join(returns_short.to_frame('short'), how='inner')

        if len(aligned_returns) < 2:
            return [], []  # Need at least 2 data points for correlation

        correlation = aligned_returns['long'].corr(aligned_returns['short'])


        if abs(correlation) > self.max_correlation:
            self.Log(f"Correlation between {long_symbol} and {short_symbol} is too high ({correlation:.2f}). Skipping trade.")
            return [], []  # Skip trading if correlation is too high

        return long_symbols, short_symbols