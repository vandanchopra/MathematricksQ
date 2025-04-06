# region imports
from AlgorithmImports import *
import numpy as np
from scipy.optimize import minimize
# endregion

class FundBalancing(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2010, 2, 1)
        self.set_end_date(2025, 3, 25)
        self.set_cash(1000000)
        self.symbols = [self.add_equity(ticker, data_normalization_mode=DataNormalizationMode.RAW).symbol for ticker in ["TQQQ", "SVXY", "VXZ", "TMF", "EDZ", "UGL"]]
        self.schedule.on(self.date_rules.week_start(), self.time_rules.at(9, 33), self.rebalance)

    def constraint_settings(self):
        constraints = {
            "type": "eq", 
            "fun": lambda w: np.sum(w) - 1
            }
        return constraints

    def run_risk_momentum_analysis(self, ret, bounds, x0, constraints):
        opt = minimize(
            lambda w: 0.5 * (w.T @ ret.cov() @ w) - x0 @ w, x0=x0, constraints=constraints, bounds=bounds, tol=1e-8, method="SLSQP"
            )
        return opt

    def rebalance(self):
        ret = self.history(self.symbols, 253, Resolution.DAILY).close.unstack(0).pct_change().dropna()
        x0 = [1/ret.shape[1]] * ret.shape[1]
        constraints = self.constraint_settings()
        bounds = [(0, 1)] * ret.shape[1]
        opt = self.run_risk_momentum_analysis(ret, bounds, x0, constraints)
        self.set_holdings(
            [PortfolioTarget(symbol, weight) for symbol, weight in zip(ret.columns, opt.x)]
            )
