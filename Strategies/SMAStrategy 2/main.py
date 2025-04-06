from AlgorithmImports import *
import numpy as np

class TrendFollowingStrategy:
    def __init__(self, algorithm, symbol):
        self.algorithm = algorithm
        self.symbol = symbol
        
        # Trend indicators
        self.ema_fast = algorithm.EMA(symbol, 5)
        self.ema_med = algorithm.EMA(symbol, 21)
        self.ema_slow = algorithm.EMA(symbol, 50)
        
        # Momentum and volatility indicators
        self.rsi = algorithm.RSI(symbol, 14)
        self.atr = algorithm.ATR(symbol, 14)
        self.macd = algorithm.MACD(symbol, 12, 26, 9)
        self.adx = algorithm.ADX(symbol, 14)
        
        # Risk management parameters
        self.stop_loss_pct = 0.02     # 2% stop loss
        self.take_profit_pct = 0.05   # 5% take profit
        self.max_leverage = 1.5       # Max leverage
        
        # Position tracking
        self.entry_price = 0
        self.in_position = False
        self.position_size = 0

    def OnData(self, data):
        if not all([self.ema_slow.IsReady, self.rsi.IsReady, self.macd.IsReady, self.adx.IsReady]):
            return

        current_price = data.Bars[self.symbol].Close
        holdings = self.algorithm.Portfolio[self.symbol].Quantity
        
        # Calculate signals
        fast_value = self.ema_fast.Current.Value
        med_value = self.ema_med.Current.Value
        slow_value = self.ema_slow.Current.Value
        rsi_value = self.rsi.Current.Value
        macd_value = self.macd.Current.Value
        macd_signal = self.macd.Signal.Current.Value
        adx_value = self.adx.Current.Value
        
        # Advanced trend analysis
        short_trend = fast_value > med_value
        medium_trend = med_value > slow_value
        macd_trend = macd_value > macd_signal and macd_value > 0
        strong_trend = adx_value > 25
        
        # Calculate trend strength (0 to 1)
        trend_factors = [
            short_trend,
            medium_trend,
            macd_trend,
            strong_trend,
            30 < rsi_value < 70,  # Not overbought/oversold
            adx_value > 20,       # Trending market
        ]
        trend_strength = sum(trend_factors) / len(trend_factors)
        
        # Position sizing based on multiple factors
        atr_pct = self.atr.Current.Value / current_price
        volatility_factor = max(0, 1.0 - (atr_pct * 10))  # Reduce size in high volatility
        momentum_factor = min(1.0, abs(macd_value / current_price) * 100)  # Scale with momentum
        adx_factor = min(1.0, adx_value / 50)  # Scale with trend strength
        
        # Calculate final position size
        position_size = (
            trend_strength * 
            volatility_factor * 
            momentum_factor * 
            adx_factor * 
            self.max_leverage
        )
        position_size = max(0.5, min(position_size, self.max_leverage))
        
        try:
            if holdings == 0 and not self.in_position:  # Not in position
                # Entry conditions
                trend_signal = (
                    trend_strength >= 0.7 and          # Strong overall trend
                    volatility_factor >= 0.7 and       # Low volatility
                    adx_value > 25 and                 # Strong trend
                    momentum_factor > 0.5              # Good momentum
                )
                
                if trend_signal:
                    self.position_size = position_size
                    self.algorithm.SetHoldings(self.symbol, position_size)
                    self.entry_price = current_price
                    self.in_position = True
                    self.algorithm.Log(f"TREND: LONG Entry - Price: {current_price}, Size: {position_size:.2f}")
                    
            elif holdings > 0 and self.in_position:  # Long position
                if self.entry_price != 0:
                    unrealized_pnl = (current_price - self.entry_price) / self.entry_price
                    
                    # Dynamic stop loss based on ATR
                    atr_stop = self.atr.Current.Value * 2 / current_price
                    dynamic_stop = max(self.stop_loss_pct, atr_stop)
                    
                    # Dynamic take profit based on trend strength
                    dynamic_tp = self.take_profit_pct * (1 + trend_strength)
                    
                    # Exit conditions
                    should_exit = (
                        unrealized_pnl <= -dynamic_stop or     # Stop loss hit
                        unrealized_pnl >= dynamic_tp or        # Take profit hit
                        (trend_strength < 0.3 and             # Trend weakening
                         adx_value < 20) or                   # Low trend strength
                        (rsi_value > 75 and                   # Overbought
                         not macd_trend)                      # MACD bearish
                    )
                    
                    if should_exit:
                        self.algorithm.Liquidate(self.symbol)
                        self.in_position = False
                        self.algorithm.Log(f"TREND: LONG Exit - Price: {current_price}, PnL: {unrealized_pnl:.2%}")

        except Exception as e:
            self.algorithm.Log(f"Error in trend trading logic: {str(e)}")

class MeanReversionStrategy:
    def __init__(self, algorithm, symbol):
        self.algorithm = algorithm
        self.symbol = symbol
        
        # Mean reversion indicators
        self.rsi = algorithm.RSI(symbol, 2)            # Very short RSI
        self.bb = algorithm.BB(symbol, 20, 2.5)        # Wider Bollinger Bands
        self.atr = algorithm.ATR(symbol, 14)           # ATR for volatility
        self.stoch = algorithm.Stoch(symbol, 14, 3, 3) # Stochastic
        
        # Risk management parameters
        self.stop_loss_pct = 0.015    # 1.5% stop loss
        self.take_profit_pct = 0.03   # 3% take profit
        self.max_leverage = 1.0       # Reduced leverage
        
        # Position tracking
        self.entry_price = 0
        self.in_position = False
        self.position_size = 0
        self.trades_today = 0
        self.last_trade_date = None

    def OnData(self, data):
        if not all([self.rsi.IsReady, self.bb.IsReady, self.stoch.IsReady]):
            return

        current_price = data.Bars[self.symbol].Close
        holdings = self.algorithm.Portfolio[self.symbol].Quantity
        current_date = data.Bars[self.symbol].EndTime.date()
        
        # Reset daily trade counter
        if self.last_trade_date != current_date:
            self.trades_today = 0
            self.last_trade_date = current_date
        
        # Get indicator values
        rsi_value = self.rsi.Current.Value
        bb_upper = self.bb.UpperBand.Current.Value
        bb_lower = self.bb.LowerBand.Current.Value
        bb_middle = self.bb.MiddleBand.Current.Value
        stoch_k = self.stoch.StochK.Current.Value
        stoch_d = self.stoch.StochD.Current.Value
        
        # Calculate mean reversion strength (0 to 1)
        price_to_bb = abs((current_price - bb_middle) / (bb_upper - bb_lower))
        rev_strength = min(1, price_to_bb * 2)
        
        # Position sizing based on multiple factors
        atr_pct = self.atr.Current.Value / current_price
        volatility_factor = max(0, 1.0 - (atr_pct * 10))
        oversold_factor = max(0, (30 - rsi_value) / 30) if rsi_value < 30 else 0
        overbought_factor = max(0, (rsi_value - 70) / 30) if rsi_value > 70 else 0
        
        try:
            if holdings == 0 and not self.in_position and self.trades_today < 3:  # Limit daily trades
                # Calculate position size
                long_size = rev_strength * volatility_factor * oversold_factor * self.max_leverage
                short_size = rev_strength * volatility_factor * overbought_factor * self.max_leverage
                
                # Oversold condition (long entry)
                oversold = (
                    current_price <= bb_lower and 
                    rsi_value < 30 and
                    stoch_k < 20 and
                    stoch_k > stoch_d  # Stochastic turning up
                )
                
                # Overbought condition (short entry)
                overbought = (
                    current_price >= bb_upper and 
                    rsi_value > 70 and
                    stoch_k > 80 and
                    stoch_k < stoch_d  # Stochastic turning down
                )
                
                if oversold and long_size > 0.5:
                    self.position_size = long_size
                    self.algorithm.SetHoldings(self.symbol, long_size)
                    self.entry_price = current_price
                    self.in_position = True
                    self.trades_today += 1
                    self.algorithm.Log(f"MEAN_REV: LONG Entry - Price: {current_price}, RSI: {rsi_value:.2f}")
                    
                elif overbought and short_size > 0.5:
                    self.position_size = -short_size
                    self.algorithm.SetHoldings(self.symbol, -short_size)
                    self.entry_price = current_price
                    self.in_position = True
                    self.trades_today += 1
                    self.algorithm.Log(f"MEAN_REV: SHORT Entry - Price: {current_price}, RSI: {rsi_value:.2f}")
                    
            elif holdings != 0 and self.in_position:  # In position
                if self.entry_price != 0:
                    unrealized_pnl = (current_price - self.entry_price) / self.entry_price
                    if holdings < 0:  # Short position
                        unrealized_pnl = -unrealized_pnl
                    
                    # Dynamic stop loss based on ATR
                    atr_stop = self.atr.Current.Value * 1.5 / current_price
                    dynamic_stop = max(self.stop_loss_pct, atr_stop)
                    
                    # Dynamic take profit based on mean reversion strength
                    dynamic_tp = self.take_profit_pct * (1 + rev_strength)
                    
                    # Exit conditions
                    should_exit = (
                        unrealized_pnl <= -dynamic_stop or     # Stop loss hit
                        unrealized_pnl >= dynamic_tp or        # Take profit hit
                        (holdings > 0 and rsi_value > 60) or   # Long exit
                        (holdings < 0 and rsi_value < 40) or   # Short exit
                        (abs(current_price - bb_middle) / bb_middle < 0.001)  # Price at middle band
                    )
                    
                    if should_exit:
                        self.algorithm.Liquidate(self.symbol)
                        self.in_position = False
                        self.algorithm.Log(f"MEAN_REV: Exit - Price: {current_price}, PnL: {unrealized_pnl:.2%}")

        except Exception as e:
            self.algorithm.Log(f"Error in mean reversion logic: {str(e)}")

class SimpleMovingAverageAlgorithm(QCAlgorithm):
    def Initialize(self):
        """
        Initialize algorithm settings, data, and indicators
        """
        self.SetStartDate(2011, 1, 1)    
        self.SetEndDate(2024, 12, 31)     
        self.SetCash(10000)              

        # Add SPY equity with daily resolution
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # Set commission model to account for slippage and fees
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage)

        # Market regime detection
        self.long_sma = self.SMA(self.symbol, 200)  # 200-day for major trend
        self.regime_roc = self.ROC(self.symbol, 200)  # 200-day rate of change
        self.regime_vol = self.STD(self.symbol, 50)   # 50-day volatility
        self.regime_atr = self.ATR(self.symbol, 50)   # 50-day ATR
        self.vix = self.AddEquity("VXX", Resolution.Daily).Symbol  # VIX proxy
        
        # Define strategies
        self.trend_strategy = TrendFollowingStrategy(self, self.symbol)
        self.mean_reversion_strategy = MeanReversionStrategy(self, self.symbol)
        
        # Risk management
        self.max_portfolio_leverage = 1.5
        self.max_concentration = 0.95
        self.drawdown_tolerance = 0.20
        
        # Performance tracking
        self.equity_peak = 10000
        self.max_drawdown = 0
        self.daily_returns = []
        self.regime_changes = 0
        
        # Set warmup period
        self.SetWarmUp(200)

    def OnData(self, data):
        """
        OnData event is the primary entry point for your algorithm.
        """
        if self.IsWarmingUp:
            return

        if not all([self.long_sma.IsReady, self.regime_roc.IsReady, self.regime_vol.IsReady]):
            return

        if not data.Bars.ContainsKey(self.symbol):
            return

        current_price = data.Bars[self.symbol].Close
        
        # Update performance metrics
        current_equity = self.Portfolio.TotalPortfolioValue
        self.equity_peak = max(self.equity_peak, current_equity)
        current_drawdown = (self.equity_peak - current_equity) / self.equity_peak
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
        # Calculate daily return
        if len(self.daily_returns) > 0:
            daily_return = (current_equity / self.daily_returns[-1]) - 1
            self.daily_returns.append(daily_return)
        else:
            self.daily_returns.append(0)
        
        # Market regime analysis
        price_to_sma = current_price / self.long_sma.Current.Value - 1
        roc_200 = self.regime_roc.Current.Value
        volatility = self.regime_vol.Current.Value / current_price
        atr_pct = self.regime_atr.Current.Value / current_price
        
        # Get VIX value if available
        vix_value = data.Bars[self.vix].Close if data.Bars.ContainsKey(self.vix) else None
        
        # Advanced regime scoring
        trend_score = (price_to_sma * 10 + roc_200) / 2  # Trend strength
        vol_score = max(0, 1 - (volatility * 10))        # Volatility penalty
        vix_factor = 1.0
        if vix_value is not None:
            vix_factor = max(0.5, 1 - (vix_value / 100))  # VIX adjustment
        
        # Market environment score (-1 to 1)
        market_score = trend_score * vol_score * vix_factor
        
        # Determine market regime
        if market_score > 0.3:
            market_regime = 1  # Strong trend following
        elif market_score < -0.3:
            market_regime = -1  # Strong mean reversion
        else:
            market_regime = 0  # Mixed
        
        # Dynamic capital allocation
        base_allocation = 0.5
        regime_strength = abs(market_score)
        
        if market_regime == 1:  # Trend following regime
            self.trend_allocation = base_allocation + (regime_strength * 0.3)
            self.mean_reversion_allocation = base_allocation - (regime_strength * 0.3)
        elif market_regime == -1:  # Mean reversion regime
            self.trend_allocation = base_allocation - (regime_strength * 0.3)
            self.mean_reversion_allocation = base_allocation + (regime_strength * 0.3)
        else:  # Neutral regime
            self.trend_allocation = base_allocation
            self.mean_reversion_allocation = base_allocation
        
        # Risk management adjustments
        if current_drawdown > self.drawdown_tolerance:
            # Reduce position sizes in drawdown
            risk_factor = 1 - (current_drawdown / self.drawdown_tolerance)
            self.trend_allocation *= risk_factor
            self.mean_reversion_allocation *= risk_factor
        
        # Scale allocations to respect maximum leverage
        total_allocation = self.trend_allocation + self.mean_reversion_allocation
        if total_allocation > self.max_portfolio_leverage:
            scale_factor = self.max_portfolio_leverage / total_allocation
            self.trend_allocation *= scale_factor
            self.mean_reversion_allocation *= scale_factor
        
        # Execute strategies with current allocations
        self.trend_strategy.OnData(data)
        self.mean_reversion_strategy.OnData(data)
        
        # Log market conditions
        self.Log(f"Market Score: {market_score:.2f}, Regime: {market_regime}, " +
                f"Trend Alloc: {self.trend_allocation:.2f}, MR Alloc: {self.mean_reversion_allocation:.2f}")
