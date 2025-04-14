from AlgorithmImports import *
import math

class E2F79F0BC841428485FA788C5F20F4DCStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Parameters for g-function
        self.x = 1.0 # You can optimize this parameter
        self.lookback = 30 # Number of past days to forecast forward
        
        # For tracking
        self.next_action_time = self.Time
        self.prediction_horizon = 5 # Days ahead to forecast

        self.last_prediction = None
        self.last_direction = None

    def g_function(self, t, x=None):
        """Implements: g(t, 1) = 0.5 * Floor[1548 * (0.26t + 0.74)^x - 1548] / 100 + 1"""
        if x is None:
            x = self.x
        value = 1548 * ((0.26 * t + 0.74) ** x) - 1548
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
        # Only trade at start of day
        if self.Time < self.next_action_time:
            return

        # Ensure we have enough history
        history = self.History(self.symbol, self.lookback, Resolution.Daily)
        if history.empty or len(history) < self.lookback:
            return

        t = self.prediction_horizon # Forecast t days ahead

        # Calculate price forecast using g-function as multiplier from last close
        last_close = history['close'].iloc[-1]
        forecast_multiplier = self.g_function(t)
        predicted_price = last_close * forecast_multiplier

        # Compute termination curve (one up, one down)
        termination_up = last_close * self.termination_curve(t, direction=1, shift_coef=0.05)
        termination_down = last_close * self.termination_curve(t, direction=-1, shift_coef=0.05)

        # Store for reference
        self.last_prediction = predicted_price

        # Basic trading logic:
        # If predicted price above termination_up, BUY.
        # If predicted price below termination_down, SELL/SHORT.
        # Else, do nothing.

        holdings = self.Portfolio[self.symbol].Quantity

        if predicted_price > termination_up and holdings <= 0:
            self.SetHoldings(self.symbol, 1)
            self.last_direction = "Long"
            self.Debug(f"{self.Time}: BUY at {last_close:.2f}, predict {predicted_price:.2f}, term_up {termination_up:.2f}")
        elif predicted_price < termination_down and holdings >= 0:
            self.SetHoldings(self.symbol, -1)
            self.last_direction = "Short"
            self.Debug(f"{self.Time}: SHORT at {last_close:.2f}, predict {predicted_price:.2f}, term_down {termination_down:.2f}")
        # else: hold position

        self.next_action_time = self.Time + timedelta(days=1)