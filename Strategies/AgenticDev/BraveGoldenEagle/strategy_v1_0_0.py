from AlgorithmImports import *
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from statsmodels.tsa.stattools import grangercausalitytests

class VolTSGrangerClusteringAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)

        # Major NYSE & NasdaqGS stocks
        self.tickers = [
            "AAPL", "MSFT", "AMZN", "GOOG", "JPM", "JNJ", "V", "TSLA", "NVDA"
        ]
        self.symbols = [self.AddEquity(ticker, Resolution.Daily).Symbol for ticker in self.tickers]
        
        self.lookback = 63  # 3 months
        self.rebalance_days = 22  # monthly
        self.next_rebalance = self.Time

        # Placeholders
        self.selected_stocks = set()
        self.vol_history = {symbol: RollingWindow[float](self.lookback) for symbol in self.symbols}
        self.price_history = {symbol: RollingWindow[float](self.lookback+1) for symbol in self.symbols}
        
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen(self.symbols[0], 30), self.DataCollection)

    def DataCollection(self):
        # Collect rolling window prices and volatility
        for symbol in self.symbols:
            hist = self.History(symbol, self.lookback+1, Resolution.Daily)
            if hist.empty or len(hist) < self.lookback+1:
                return
            closes = hist.close.values
            # Store price history
            self.price_history[symbol].Reset()
            for c in closes:
                self.price_history[symbol].Add(c)
            # Calculate and store volatility (std of log returns)
            logrets = np.diff(np.log(closes))
            vol = np.std(logrets)
            self.vol_history[symbol].Add(vol)
        
        # Rebalance if due
        if self.Time >= self.next_rebalance:
            self.next_rebalance = self.Time + timedelta(days=self.rebalance_days)
            self.VolTS_Strategy()

    def VolTS_Strategy(self):
        # Step 1: Prepare volatility data for clustering
        vols = []
        for symbol in self.symbols:
            if self.vol_history[symbol].IsReady:
                vols.append(np.mean(list(self.vol_history[symbol])))
            else:
                # Not enough data
                return
        vol_df = pd.DataFrame([vols], columns=[str(s) for s in self.symbols])

        # Step 2: k-means++ clustering
        kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
        clusters = kmeans.fit_predict(vol_df.T)
        cluster_map = {str(sym): clusters[i] for i, sym in enumerate(self.symbols)}

        # Step 3: Granger Causality Test
        granger_results = []
        price_df = pd.DataFrame({str(sym): list(self.price_history[sym]) for sym in self.symbols})
        # Ensure no NaNs
        if price_df.isnull().values.any():
            return

        # Use log returns for Granger Causality
        returns_df = np.log(price_df).diff().dropna()

        for i, col_x in enumerate(returns_df.columns):
            for j, col_y in enumerate(returns_df.columns):
                if i != j:
                    try:
                        # Test if x Granger-causes y
                        # Use lag=2 for test
                        test_result = grangercausalitytests(returns_df[[col_y, col_x]], maxlag=2, verbose=False)
                        # p-value of F-test at lag 2
                        p_value = test_result[2][0]['ssr_ftest'][1]
                        if p_value < 0.05:
                            granger_results.append((col_x, col_y))
                    except Exception as e:
                        self.Debug(f"Granger test failed for {col_x}->{col_y}: {e}")

        # Step 4: Select stocks involved in Granger causality relationships
        selected_stocks = set()
        for pair in granger_results:
            selected_stocks.add(pair[0])
            selected_stocks.add(pair[1])
        self.selected_stocks = selected_stocks

        self.SetHoldingsBasedOnSelection()

    def SetHoldingsBasedOnSelection(self):
        invested = set([str(sec.Symbol) for sec in self.Portfolio.Values if sec.Invested])
        to_invest = self.selected_stocks

        # Liquidate stocks not in selection
        for symbol in invested:
            if symbol not in to_invest:
                self.Liquidate(symbol)

        # Equally weight selected stocks
        if len(to_invest) > 0:
            weight = 1.0 / len(to_invest)
            for symbol in to_invest:
                self.SetHoldings(symbol, weight)