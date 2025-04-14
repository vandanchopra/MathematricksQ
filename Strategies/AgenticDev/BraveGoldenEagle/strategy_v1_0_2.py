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
        
        # 9 major NYSE/NASDAQGS stocks (tickers and mapping)
        self.tickers = ["AAPL", "MSFT", "AMZN", "GOOG", "JPM", "JNJ", "V", "TSLA", "NVDA"]
        self.symbols = [self.AddEquity(t, Resolution.Daily).Symbol for t in self.tickers]
        self.ticker_to_symbol = {s.Value: s for s in self.symbols}
        
        self.lookback = 63  # ~3 months
        self.rebalance_days = 22  # ~monthly
        
        # RollingWindows for close prices (to compute log returns)
        self.price_windows = {t: RollingWindow[float](self.lookback+1) for t in self.tickers}
        
        # Schedule monthly rebalance
        self.Schedule.On(
            self.DateRules.MonthStart(self.symbols[0]), 
            self.TimeRules.AfterMarketOpen(self.symbols[0], 30), 
            self.Rebalance
        )
    
    def OnData(self, data: Slice):
        # Update price rolling windows
        for t, sym in zip(self.tickers, self.symbols):
            if data.Bars.ContainsKey(sym):
                self.price_windows[t].Add(float(data.Bars[sym].Close))
    
    def Rebalance(self):
        # Only proceed if all windows are ready
        if not all(w.IsReady for w in self.price_windows.values()):
            self.Debug("Not enough price data yet for all symbols.")
            return
        
        # Step 1: Compute log returns and mean volatility
        returns_dict = {}
        mean_vols = []
        for t in self.tickers:
            pw = self.price_windows[t]
            prices = list(pw)[::-1]  # Oldest to newest
            prices = np.array(prices)
            log_returns = np.diff(np.log(prices))
            returns_dict[t] = log_returns
            mean_vols.append(np.std(log_returns))
        
        # KMeans++ clustering (n_clusters=3)
        vol_df = pd.DataFrame({'ticker': self.tickers, 'mean_vol': mean_vols}).set_index('ticker')
        kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
        vol_df['cluster'] = kmeans.fit_predict(vol_df[['mean_vol']])
        
        # Step 2: Granger Causality Test
        # Create DataFrame of log returns (rows: time, cols: tickers)
        returns_df = pd.DataFrame(returns_dict)
        returns_df.dropna(inplace=True)  # Remove rows with any NaN
        
        granger_results = []
        maxlag = 2
        # Only run GCT if enough data points for lags
        if len(returns_df) > maxlag * 10:
            for x in self.tickers:
                for y in self.tickers:
                    if x == y:
                        continue
                    try:
                        # Test if x Granger-causes y
                        # Per statsmodels: test returns_df[[y, x]]
                        test_result = grangercausalitytests(returns_df[[y, x]], maxlag=maxlag, verbose=False)
                        # Take p-value for lag 2
                        p_value = test_result[2][0]['ssr_ftest'][1]
                        if p_value < 0.05:
                            granger_results.append( (x, y) )
                    except Exception as e:
                        self.Debug(f"GCT failed: {x}->{y}: {e}")
                        continue
        else:
            self.Debug(f"Not enough data for Granger causality (len={len(returns_df)}).")
        
        # Step 3: Select all stocks in Granger pairs
        selected_tickers = set()
        for x, y in granger_results:
            selected_tickers.add(x)
            selected_tickers.add(y)
        selected_symbols = [self.ticker_to_symbol[t] for t in selected_tickers]
        
        self.Log(f"Rebalance {self.Time.date()}: {len(selected_symbols)} selected: {[s.Value for s in selected_symbols]}")
        
        # Step 4: Portfolio update
        current_invested = set([kv.Key for kv in self.Portfolio.Values if kv.Invested])
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