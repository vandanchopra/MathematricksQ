import { Agent } from './agent';

/**
 * Agent responsible for backtesting trading strategies
 */
export class BacktestAgent extends Agent {
  /**
   * Run a backtest for a given strategy
   * @param strategy The strategy to backtest
   * @returns Backtest results
   */
  public async runBacktest(strategy: any): Promise<any> {
    console.log(`Running backtest for strategy: ${strategy.name}`);
    
    // Simulate backtest results
    return {
      strategyId: strategy.id,
      results: {
        equity: this.generateEquityCurve(),
        trades: this.generateTrades(),
        metrics: {
          cagr: Math.random() * 0.2 + 0.1,
          sharpeRatio: Math.random() * 1.5 + 0.5,
          maxDrawdown: Math.random() * 0.15,
          winRate: Math.random() * 0.3 + 0.5,
          profitFactor: Math.random() * 2 + 1,
          totalTrades: Math.floor(Math.random() * 100) + 20,
          averageProfit: Math.random() * 0.02 + 0.01
        }
      }
    };
  }
  
  /**
   * Generate a simulated equity curve
   * @returns Array of equity values
   */
  private generateEquityCurve(): number[] {
    const days = 365;
    const equity = [100000]; // Start with $100,000
    
    for (let i = 1; i < days; i++) {
      // Random daily return between -1% and +1.5%
      const dailyReturn = (Math.random() * 0.025) - 0.01;
      equity.push(equity[i-1] * (1 + dailyReturn));
    }
    
    return equity;
  }
  
  /**
   * Generate simulated trades
   * @returns Array of trade objects
   */
  private generateTrades(): any[] {
    const numTrades = Math.floor(Math.random() * 50) + 20;
    const trades = [];
    
    for (let i = 0; i < numTrades; i++) {
      const isWin = Math.random() > 0.4; // 60% win rate
      
      trades.push({
        id: `trade_${i}`,
        entryDate: this.randomDate(new Date('2022-01-01'), new Date('2022-12-31')),
        exitDate: this.randomDate(new Date('2022-01-15'), new Date('2023-01-15')),
        symbol: ['SPY', 'QQQ', 'AAPL', 'MSFT'][Math.floor(Math.random() * 4)],
        direction: Math.random() > 0.5 ? 'long' : 'short',
        entryPrice: Math.random() * 200 + 100,
        exitPrice: 0, // Will be calculated
        quantity: Math.floor(Math.random() * 100) + 10,
        pnl: 0, // Will be calculated
        pnlPercent: isWin ? Math.random() * 0.05 + 0.01 : -(Math.random() * 0.03 + 0.01)
      });
      
      // Calculate exit price and PnL
      const trade = trades[i];
      const multiplier = trade.direction === 'long' ? 1 : -1;
      trade.exitPrice = trade.entryPrice * (1 + (trade.pnlPercent * multiplier));
      trade.pnl = (trade.exitPrice - trade.entryPrice) * trade.quantity * multiplier;
    }
    
    return trades;
  }
  
  /**
   * Generate a random date between two dates
   * @param start Start date
   * @param end End date
   * @returns Random date
   */
  private randomDate(start: Date, end: Date): string {
    const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
    return date.toISOString().split('T')[0];
  }
}
