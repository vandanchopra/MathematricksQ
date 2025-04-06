from AlgorithmImports import *

class MeanReversionStrategy(object):
    def __init__(self, algorithm, symbol):
        self.algorithm = algorithm
        self.symbol = symbol
        
        # Mean reversion indicators
        self.rsi = self.RSI(self.symbol, 5)           # Very short RSI
        self.bb = self.BB(self.symbol, 20, 2)         # Bollinger Bands
        
        # Risk management parameters
        self.stop_loss_pct = 0.01     # 1% stop loss
        self.take_profit_pct = 0.02   # 2% take profit
        self.max_leverage = 1.5       # Reduced leverage
        
        # Position tracking
        self.entry_price = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        
        # Warmup
        self.algorithm.SetWarmUp(100)

    def OnData(self, data):
        if self.algorithm.IsWarmingUp or not all([self.rsi.IsReady, self.bb.IsReady]):
            return

        if not data.Bars.ContainsKey(self.symbol):
            return

        current_price = data.Bars[self.symbol].Close
        holdings = self.algorithm.Portfolio[self.symbol].Quantity
        
        # Get indicator values
        rsi_value = self.rsi.Current.Value
        bb_upper = self.bb.UpperBand.Current.Value
        bb_lower = self.bb.LowerBand.Current.Value
        
        try:
            if holdings == 0:  # Not in position
                # Oversold condition
                oversold = current_price <= bb_lower and rsi_value < 40
                
                # Overbought condition
                overbought = current_price >= bb_upper and rsi_value > 60
                
                if oversold:
                    # Enter long position
                    self.algorithm.SetHoldings(self.symbol, 0.75)  # 75% position size
                    self.entry_price = current_price
                    self.Log(f"LONG Entry - Price: {current_price}, RSI: {rsi_value:.2f}")
                    
                elif overbought:
                    # Enter short position
                    self.algorithm.SetHoldings(self.symbol, -0.75)  # 75% position size
                    self.entry_price = current_price
                    self.Log(f"SHORT Entry - Price: {current_price}, RSI: {rsi_value:.2f}")
                    
            elif holdings > 0:  # Long position
                unrealized_pnl = (current_price - self.entry_price) / self.entry_price
                
                # Exit long position
                should_exit = (
                    unrealized_pnl <= -self.stop_loss_pct or  # Stop loss
                    unrealized_pnl >= self.take_profit_pct or  # Take profit
                    rsi_value > 50                             # RSI back to neutral
                )
                
                if should_exit:
                    self.algorithm.Liquidate(self.symbol)
                    self.Log(f"LONG Exit - Price: {current_price}, PnL: {unrealized_pnl:.2%}")
                    
            elif holdings < 0:  # Short position
                unrealized_pnl = (self.entry_price - current_price) / self.entry_price
                
                # Exit short position
                should_exit = (
                    unrealized_pnl <= -self.stop_loss_pct or  # Stop loss
                    unrealized_pnl >= self.take_profit_pct or  # Take profit
                    rsi_value < 50                             # RSI back to neutral
                )
                
                if should_exit:
                    self.algorithm.Liquidate(self.symbol)
                    self.Log(f"SHORT Exit - Price: {current_price}, PnL: {unrealized_pnl:.2%}")

        except Exception as e:
            self.Log(f"Error: {e}")

    def Log(self, message):
        self.algorithm.Log(f"MeanReversion: {message}")
