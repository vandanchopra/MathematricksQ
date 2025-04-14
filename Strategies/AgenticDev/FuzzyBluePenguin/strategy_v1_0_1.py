from AlgorithmImports import *
from datetime import timedelta

class E2F79F0BC841428485FA788C5F20F4DCStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # g-function parameters
        self.x = 1.0
        self.lookback = 30  # Days of history for context
        self.prediction_horizon = 5  # Forecast t days ahead

        # For controlling trade frequency
        self.next_action_time = self.Time
        
        # Warm up period for history
        self.SetWarmUp(self.lookback, Resolution.Daily)

        # State
        self.last_signal = None

    def g_function(self, t, x=None):
        """
        Implements: g(t, 1) = 0.5 * Floor[1548 * (0.26t + 0.74)^x - 1548] / 100 + 1
        """
        if x is None:
            x = self.x
        base = 0.26 * t + 0.74
        value = 1548 * (base ** x) - 1548
        floored = math.floor(value)
        result = 0.5 * floored / 100.0 + 1
        return result

    def termination_curve(self, t, direction=1, shift_coef=0.1):
        """
        Termination curve is a shifted g-function.
        direction: +1 = up, -1 = down
        shift_coef: how much to shift
        """
        return self.g_function(t) + direction * shift_coef

    def OnData(self, data: Slice):
        # Only trade at start of each day
        if self.IsWarmingUp or self.Time < self.next_action_time:
            return

        # Get historical close prices
        history = self.History(self.symbol, self.lookback, Resolution.Daily)
        if history.empty or len(history.index) < self.lookback:
            return

        # Access the close series for the symbol
        try:
            last_close = float(history.loc[self.symbol]['close'].iloc[-1])
        except Exception as e:
            self.Log(f"History access error: {e}")
            return

        t = self.prediction_horizon  # days ahead

        # Calculate g-function forecast as a MULTIPLIER of last close
        forecast_multiplier = self.g_function(t)
        predicted_price = last_close * forecast_multiplier

        # Compute termination curves (up and down)
        shift_coef = 0.05
        termination_up = last_close * self.termination_curve(t, direction=1, shift_coef=shift_coef)
        termination_down = last_close * self.termination_curve(t, direction=-1, shift_coef=shift_coef)

        # Signal logic
        signal = 0
        if predicted_price > termination_up:
            signal = 1  # Long
        elif predicted_price < termination_down:
            signal = -1  # Short
        else:
            signal = 0  # Neutral

        holdings = self.Portfolio[self.symbol].Quantity

        # Only trade if signal changes
        if signal != self.last_signal:
            if signal == 1:
                self.SetHoldings(self.symbol, 1)
                self.Log(f"{self.Time.date()}: BUY at {last_close:.2f}, predict {predicted_price:.2f}, term_up {termination_up:.2f}")
            elif signal == -1:
                self.SetHoldings(self.symbol, -1)
                self.Log(f"{self.Time.date()}: SHORT at {last_close:.2f}, predict {predicted_price:.2f}, term_down {termination_down:.2f}")
            else:
                self.Liquidate(self.symbol)
                self.Log(f"{self.Time.date()}: LIQUIDATE at {last_close:.2f}")

            self.last_signal = signal

        # Prevent overtrading: only check once per day
        self.next_action_time = self.Time + timedelta(days=1)