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
        
        # Trailing stop loss and profit target
        self.trailing_stop_percentage = 0.05  # 5% trailing stop
        self.profit_target_percentage = 0.10 #10% profit target
        self.highest_prices = {}
        self.entry_prices = {} #store initial entry price

        # Risk Management - Volatility Scaling
        self.volatility_lookback = 60
        self.volatility = {}
        self.risk_free_rate = 0.02  # Annual risk-free rate (e.g., Treasury yield)
        self.target_volatility = 0.10  # Target portfolio volatility (annualized)

    def OnData(self, data):

        if self.Time - self.last_rebalance < self.rebalance_frequency:
            return

        if self.IsWarmingUp:
            return

        self.CalculateMomentum(data)
        self.RebalancePortfolio(data)  # Pass data to RebalancePortfolio
        self.last_rebalance = self.Time
        self.UpdateTrailingStopsAndProfitTargets(data)
        self.CalculateVolatility(data)


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


    def RebalancePortfolio(self, data):
        """
        Adjusts portfolio holdings based on momentum scores, incorporating volatility scaling.
        Longs the top two momentum stocks and shorts the bottom two.
        """
        if not self.momentum:
            self.Log("No momentum data available. Skipping rebalancing.")
            return

        sorted_symbols = sorted(self.momentum.items(), key=lambda x: x[1], reverse=True)

        long_symbols = [symbol for symbol, _ in sorted_symbols[:2]]
        short_symbols = [symbol for symbol, _ in sorted_symbols[-2:]]

        # Calculate portfolio volatility and scaling factor
        portfolio_volatility = self.CalculatePortfolioVolatility()
        if portfolio_volatility > 0:
            scale_factor = self.target_volatility / portfolio_volatility
            scale_factor = min(scale_factor, 1.5)  # Cap the scaling factor
        else:
            scale_factor = 1.0

        long_weight = (0.5 * scale_factor) / len(long_symbols) if long_symbols else 0
        short_weight = (-0.5 * scale_factor) / len(short_symbols) if short_symbols else 0

        for holding in self.Portfolio.Values:
            if holding.Invested:
                self.Liquidate(holding.Symbol)
                self.highest_prices[holding.Symbol] = 0  # Reset highest price
                self.entry_prices[holding.Symbol] = 0

        for symbol in long_symbols:
            self.SetHoldings(symbol, long_weight)
            self.highest_prices[symbol] = data[symbol].Close  # Initialize highest price
            self.entry_prices[symbol] = data[symbol].Close

        for symbol in short_symbols:
            self.SetHoldings(symbol, short_weight)
            self.highest_prices[symbol] = data[symbol].Close  # Initialize highest price
            self.entry_prices[symbol] = data[symbol].Close

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Filled:
            self.Log(f"{orderEvent.Symbol} Order filled. Quantity: {orderEvent.FillQuantity}, Fill Price: {orderEvent.FillPrice}")

    def UpdateTrailingStopsAndProfitTargets(self, data):
        """
        Updates the trailing stop loss and profit target for each held security.
        """
        for symbol, holding in self.Portfolio.items():
            if holding.Invested and data.ContainsKey(symbol):
                current_price = data[symbol].Close
                
                # Update highest price
                if symbol in self.highest_prices:
                    self.highest_prices[symbol] = max(self.highest_prices[symbol], current_price)
                else:
                    self.highest_prices[symbol] = current_price

                # Calculate stop loss and profit target prices
                if holding.IsLong:
                    stop_loss_price = self.highest_prices[symbol] * (1 - self.trailing_stop_percentage)
                    profit_target_price = self.entry_prices[symbol] * (1 + self.profit_target_percentage)

                    if current_price <= stop_loss_price:
                        self.Liquidate(symbol)
                        self.Log(f"Trailing stop loss triggered for {symbol} at {current_price}")
                        self.highest_prices[symbol] = 0 #reset
                        self.entry_prices[symbol] = 0
                    elif current_price >= profit_target_price:
                        self.Liquidate(symbol)
                        self.Log(f"Profit target triggered for {symbol} at {current_price}")
                        self.highest_prices[symbol] = 0
                        self.entry_prices[symbol] = 0


                elif holding.IsShort:
                    stop_loss_price = self.highest_prices[symbol] * (1 + self.trailing_stop_percentage)
                    profit_target_price = self.entry_prices[symbol] * (1 - self.profit_target_percentage)


                    if current_price >= stop_loss_price:
                        self.Liquidate(symbol)
                        self.Log(f"Trailing stop loss triggered for {symbol} at {current_price}")
                        self.highest_prices[symbol] = 0 #reset.
                        self.entry_prices[symbol] = 0

                    elif current_price <= profit_target_price:
                        self.Liquidate(symbol)
                        self.Log(f"Profit target triggered for {symbol} at {current_price}")
                        self.highest_prices[symbol] = 0
                        self.entry_prices[symbol] = 0

    def CalculateVolatility(self, data):
        """
        Calculates the annualized volatility for each symbol.
        """
        for symbol in self.symbols:
            history = self.History(symbol, self.volatility_lookback, Resolution.DAILY)
            if history.empty:
                self.volatility[symbol] = 0.0
                continue

            returns = history['close'].pct_change().dropna()
            if len(returns) < 2:
                self.volatility[symbol] = 0.0
                continue

            self.volatility[symbol] = np.std(returns) * np.sqrt(252)  # Annualize volatility

    def CalculatePortfolioVolatility(self):
        """
        Calculates the overall portfolio volatility based on individual asset volatilities and weights.
        This is a simplified calculation and doesn't account for correlations.
        """
        total_weight = 0.0
        weighted_volatility = 0.0

        for symbol, holding in self.Portfolio.items():
            if symbol in self.volatility:
                weight = abs(holding. holdingsValue / self.Portfolio.TotalPortfolioValue)
                weighted_volatility += weight * self.volatility[symbol]
                total_weight += weight

        if total_weight > 0:
            return weighted_volatility
        else:
            return 0.0