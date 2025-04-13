/**
 * Trading targets for strategy evaluation
 */
export interface TradingTargets {
  /**
   * Minimum Compound Annual Growth Rate
   */
  minCAGR: number;
  
  /**
   * Minimum Sharpe Ratio
   */
  minSharpeRatio: number;
  
  /**
   * Maximum Drawdown (as a decimal)
   */
  maxDrawdown: number;
  
  /**
   * Minimum Win Rate (as a decimal)
   */
  minWinRate: number;
  
  /**
   * Minimum Profit Factor
   */
  minProfitFactor: number;
}

/**
 * Strategy evaluation result
 */
export interface StrategyEvaluation {
  /**
   * Strategy ID
   */
  strategyId: string;
  
  /**
   * Strategy description
   */
  description: string;
  
  /**
   * Evaluation score (0-1)
   */
  score: number;
  
  /**
   * Performance metrics
   */
  metrics: {
    cagr: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
    totalTrades: number;
    averageProfit: number;
  };
}
