from AlgorithmImports import *

class SimpleMovingAverageAlgorithm(QCAlgorithm):
    def Initialize(self):
        """
        Initialize algorithm settings, data, and indicators
        """
        self.SetStartDate(2011, 1, 1)    
        self.SetEndDate(2024, 12, 31)     
        self.SetCash(10000)              

        # Add SPY equity with minute resolution data
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Create two simple moving averages
        self.fast_sma = self.SMA(self.symbol, 20)
        self.slow_sma = self.SMA(self.symbol, 25)

        # Set warmup period to let SMA gather enough data
        self.SetWarmUp(200)

    def OnData(self, data):
        """
        OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.
        """
        # Skip if we're still in warmup or don't have all data points
        if self.IsWarmingUp or not self.slow_sma.IsReady:
            return

        # Get current holdings
        holdings = self.Portfolio[self.symbol].Quantity

        # Trading logic
        if self.fast_sma.Current.Value > self.slow_sma.Current.Value:
            # Crossover above: Buy signal
            if holdings <= 0:
                self.SetHoldings(self.symbol, 1.0)  # Full long position
        
        elif self.fast_sma.Current.Value < self.slow_sma.Current.Value:
            # Crossover below: Sell signal
            if holdings >= 0:
                self.SetHoldings(self.symbol, -1)  # Half short position
