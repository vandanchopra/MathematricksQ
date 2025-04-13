import { TradingTargets } from './types';

/**
 * Default trading targets
 */
export const DEFAULT_TRADING_TARGETS: TradingTargets = {
  minCAGR: 0.15,          // 15% annual growth
  minSharpeRatio: 1.0,    // Sharpe ratio of at least 1.0
  maxDrawdown: 0.15,      // Maximum drawdown of 15%
  minWinRate: 0.55,       // Win rate of at least 55%
  minProfitFactor: 1.5    // Profit factor of at least 1.5
};

/**
 * Backtest configuration
 */
export const BACKTEST_CONFIG = {
  startDate: '2018-01-01',
  endDate: '2023-01-01',
  initialCapital: 100000,
  symbols: ['SPY', 'QQQ', 'AAPL', 'MSFT', 'AMZN', 'GOOGL'],
  timeframes: ['1D', '4H', '1H'],
  maxStrategies: 10,
  maxBacktests: 20,
  maxOptimizationRounds: 3
};

/**
 * Web search configuration
 */
export const WEB_SEARCH_CONFIG = {
  maxResults: 10,
  maxPages: 5,
  timeout: 30000,
  userAgent: 'ReAgent/1.0'
};

/**
 * System configuration
 */
export const SYSTEM_CONFIG = {
  logLevel: 'info',
  dataDir: './data',
  resultsDir: './results',
  strategiesDir: './strategies',
  maxConcurrentTasks: 4,
  autosaveInterval: 300000  // 5 minutes
};
