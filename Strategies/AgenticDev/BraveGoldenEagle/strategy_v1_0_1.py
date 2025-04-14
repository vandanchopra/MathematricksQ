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
        
        # 9 major NYSE/NasdaqGS stocks
        self.tickers = ["AAPL", "MSFT", "AMZN", "GOOG", "JPM", "JNJ", "V", "TSLA", "NVDA"]
        self.symbols = [self.AddEquity(t, Resolution.Daily).Symbol for t in self.tickers]
        self.lookback = 63  # 3 months
        self.rebalance_days = 22  # ~monthly

        # RollingWindows for prices and volatility
        self.price_windows = {s: RollingWindow[float](self.lookback+1) for s in self.symbols}
        self.vol_windows = {s: RollingWindow[float](self.lookback) for s in self.symbols}

        # Schedule monthly rebalance after market open
        self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0], 30), self.Rebalance)
        
        self.last_price_update = None

    def OnData(self, data: Slice):
        # Update rolling windows with new close prices
        for symbol in self.symbols:
            if data.Bars.ContainsKey(symbol):
                price = float(data.Bars[symbol].Close)
                pw = self.price_windows[symbol]
                if pw.Count > 0:
                    prev_price = pw[0]
                    # Compute log-return for volatility
                    log_ret = np.log(price / prev_price)
                    self.vol_windows[symbol].Add(log_ret)
                pw.Add(price)
        self.last_price_update = self.Time

    def Rebalance(self):
        # Only proceed if all windows are ready
        if not all(self.price_windows[s].IsReady for s in self.symbols):
            self.Debug("Not enough price data yet for all symbols.")
            return
        if not all(self.vol_windows[s].IsReady for s in self.symbols):
            self.Debug("Not enough volatility data yet for all symbols.")
            return

        # Step 1: Compute mean volatility per symbol
        mean_vols = [np.std(list(self.vol_windows[s])) for s in self.symbols]
        vol_df = pd.DataFrame({'symbol': self.symbols, 'mean_vol': mean_vols}).set_index('symbol')

        # Step 2: KMeans++ clustering (n_clusters=3)
        kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
        clusters = kmeans.fit_predict(vol_df[['mean_vol']])
        vol_df['cluster'] = clusters

        # Step 3: Granger Causality Test on log returns
        # Build DataFrame of log returns (rows: time, cols: symbols)
        returns = {str(s): list(self.vol_windows[s]) for s in self.symbols}
        returns_df = pd.DataFrame(returns)
        returns_df.dropna(inplace=True)

        granger_results = []
        for i, col_x in enumerate(returns_df.columns):
            for j, col_y in enumerate(returns_df.columns):
                if i == j:
                    continue
                try:
                    # Test if x Granger-causes y (maxlag=2)
                    test_result = grangercausalitytests(returns_df[[col_y, col_x]], maxlag=2, verbose=False)
                    p_value = test_result[2][0]['ssr_ftest'][1]
                    if p_value < 0.05:
                        granger_results.append((col_x, col_y))
                except Exception as e:
                    self.Debug(f"GCT failed: {col_x}->{col_y}: {e}")
                    continue
        
        # Step 4: Select all stocks in Granger pairs
        selected_symbols = set()
        for s1, s2 in granger_results:
            # Convert string names back to Symbol objects
            for s in self.symbols:
                if str(s) == s1 or str(s) == s2:
                    selected_symbols.add(s)
        self.Log(f"Rebalance date {self.Time.date()}: selected {len(selected_symbols)} stocks: {[s.Value for s in selected_symbols]}")

        # Step 5: Portfolio update
        current_invested = set([x.Symbol for x in self.Portfolio.Values if x.Invested])
        # Liquidate not selected
        for s in current_invested:
            if s not in selected_symbols:
                self.Liquidate(s)
        # Equally weight positions
        n = len(selected_symbols)
        if n > 0:
            weight = 1.0 / n
            for s in selected_symbols:
                self.SetHoldings(s, weight)
        else:
            self.Log("No selected stocks; portfolio is in cash.")