from AlgorithmImports import *

class TrendFollowingStrategy(object):
    def __init__(self, algorithm, symbol):
        self.algorithm = algorithm
        self.symbol = symbol
        
        # Trend indicators
        self.ema_fast = self.EMA(self.symbol, 3)
        self.ema_med = self.EMA(self.symbol, 10)
        self.ema_slow = self.EMA(self.symbol, 30)
        
        # Momentum and volatility indicators
        self.rsi = self.RSI(self.symbol, 7)
        self.atr = self.ATR(self.symbol, 14)
        self.roc = self.ROC(self.symbol, 10)
        
        # Risk management parameters
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.05
        self.max_leverage = 2.0
        
        # Position tracking
        self.entry_price = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        
        # Warmup
        self.algorithm.SetWarmUp(100)

    def OnData(self, data):
        if self.algorithm.IsWarmingUp or not all([self.ema_slow.IsReady, self.rsi.IsReady]):
            return

        if not data.Bars.ContainsKey(self.symbol):
            return

        current_price = data.Bars[self.symbol].Close
        holdings = self.algorithm.Portfolio[self.symbol].Quantity
        
        # Calculate trend signals
        fast_value = self.ema_fast.Current.Value
        med_value = self.ema_med.Current.Value
        slow_value = self.ema_slow.Current.Value
        rsi_value = self.rsi.Current.Value
        roc_value = self.roc.Current.Value
        
        # Trend analysis
        short_term_trend = fast_value > med_value
        medium_term_trend = med_value > slow_value
        price_momentum = roc_value > 0
        
        # Calculate trend strength
        trend_strength = (
            (fast_value / med_value - 1) * 100 +  # Short-term strength
            (med_value / slow_value - 1) * 100    # Medium-term strength
        ) / 2
        
        # Position sizing based on trend strength and volatility
        atr_pct = self.atr.Current.Value / current_price
        base_position = 1.0 + (abs(trend_strength) * 0.2)
        volatility_factor = 1.0 - (atr_pct * 5)  # Reduce size in high volatility
        momentum_factor = 0.5 + (abs(roc_value) * 0.1)  # Increase size with stronger momentum
        
        # Calculate final position size with all factors
        position_size = base_position * volatility_factor * momentum_factor
        position_size = min(position_size, self.max_leverage)
        position_size = max(position_size, 0.5)  # Minimum position size
        
        try:
            if holdings == 0:  # Not in position
                # More aggressive entry conditions
                strong_trend = (
                    short_term_trend and                   # Short-term trend up
                    medium_term_trend and                  # Medium-term trend up
                    trend_strength > 0.5 and          # Strong trend momentum
                    price_momentum                        # Positive price momentum
                )
                
                good_momentum = (
                    30 < rsi_value < 70 or           # Normal RSI range
                    (rsi_value <= 30 and short_term_trend) or  # Oversold with uptrend
                    (rsi_value >= 70 and trend_strength > 1)  # Overbought but strong trend
                )
                
                if strong_trend and good_momentum:
                    self.algorithm.SetHoldings(self.symbol, position_size)
                    self.entry_price = current_price
                    self.Log(f"LONG Entry - Price: {current_price}, Size: {position_size}, RSI: {rsi_value:.2f}")
                    
            elif holdings > 0:  # Long position
                unrealized_pnl = (current_price - self.entry_price) / self.entry_price
                
                # Dynamic exit conditions
                trend_reversal = (
                    not short_term_trend and not medium_term_trend and  # Both trends down
                    trend_strength < -0.5                     # Strong downward momentum
                )
                
                should_exit = (
                    unrealized_pnl <= -self.stop_loss_pct or     # Stop loss
                    unrealized_pnl >= self.take_profit_pct or    # Take profit
                    trend_reversal or                            # Trend reversal
                    (rsi_value > 80 and not medium_term_trend)    # Overbought without trend
                )
                
                if should_exit:
                    self.algorithm.Liquidate(self.symbol)
                    self.Log(f"LONG Exit - Price: {current_price}, PnL: {unrealized_pnl:.2%}")

        except Exception as e:
            self.Log(f"Error in trading logic: {str(e)}")

    def Log(self, message):
        self.algorithm.Log(f"Trend: {message}")
