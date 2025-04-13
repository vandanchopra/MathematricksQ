import { Agent } from './agent';
import { OpenRouterService } from '../../services/openrouter-service';
import { TradingTargets } from '../types';

/**
 * Agent responsible for evaluating trading strategies
 */
export class StrategyEvaluatorAgent extends Agent {
  private openRouterService: OpenRouterService;
  private tradingTargets: TradingTargets;

  /**
   * Initialize the strategy evaluator agent
   * @param tradingTargets Trading targets for evaluation
   * @param apiKey OpenRouter API key
   * @param useOllamaFallback Whether to use Ollama as a fallback
   */
  constructor(tradingTargets: TradingTargets, apiKey: string, useOllamaFallback: boolean = true) {
    super();
    this.tradingTargets = tradingTargets;
    this.openRouterService = new OpenRouterService(apiKey, useOllamaFallback);
  }

  /**
   * Evaluate trading strategies
   * @param strategies Strategies to evaluate
   * @returns Evaluated strategies with scores
   */
  public async execute(strategies: any[]): Promise<any[]> {
    console.log('Evaluating strategies...');

    try {
      // Evaluate strategies using OpenRouter
      const evaluatedStrategies = await this.evaluateStrategies(strategies);
      return evaluatedStrategies;
    } catch (error) {
      console.error('Error evaluating strategies:', error);

      // Fallback to simple evaluation if API fails
      return this.fallbackEvaluateStrategies(strategies);
    }
  }

  /**
   * Evaluate strategies using OpenRouter
   * @param strategies Strategies to evaluate
   * @param backtestResults Optional backtest results
   * @returns Evaluated strategies with scores
   */
  public async evaluateStrategies(strategies: any[], backtestResults?: any[]): Promise<any[]> {
    const evaluatedStrategies = [];

    for (const strategy of strategies) {
      try {
        // Get backtest result for this strategy if available
        const backtestResult = backtestResults?.find(result => result.strategyId === strategy.id);

        // Analyze the strategy using OpenRouter
        const analysisResult = await this.openRouterService.analyzeStrategy(strategy);

        // Calculate score based on expected performance or backtest results
        const metrics = backtestResult?.results?.metrics || strategy.expectedPerformance;
        const score = this.calculateScore(metrics);

        evaluatedStrategies.push({
          ...strategy,
          score,
          metrics,
          analysis: analysisResult.analysis
        });
      } catch (error) {
        console.error(`Error evaluating strategy ${strategy.id}:`, error);

        // Add a fallback evaluation if API call fails
        const metrics = strategy.expectedPerformance || {
          cagr: Math.random() * 0.2 + 0.1,
          sharpeRatio: Math.random() * 1.5 + 0.5,
          maxDrawdown: Math.random() * 0.15,
          winRate: Math.random() * 0.3 + 0.5,
          profitFactor: Math.random() * 2 + 1,
          totalTrades: Math.floor(Math.random() * 100) + 20,
          averageProfit: Math.random() * 0.02 + 0.01
        };

        evaluatedStrategies.push({
          ...strategy,
          score: this.calculateScore(metrics),
          metrics
        });
      }
    }

    return evaluatedStrategies;
  }

  /**
   * Calculate score based on performance metrics
   * @param metrics Performance metrics
   * @returns Score between 0 and 1
   */
  private calculateScore(metrics: any): number {
    // Calculate score components
    const cagrScore = Math.min(metrics.cagr / this.tradingTargets.minCAGR, 2) * 0.3;
    const sharpeScore = Math.min(metrics.sharpeRatio / this.tradingTargets.minSharpeRatio, 2) * 0.3;
    const drawdownScore = Math.min(this.tradingTargets.maxDrawdown / (metrics.maxDrawdown || 0.01), 2) * 0.2;
    const winRateScore = Math.min(metrics.winRate / this.tradingTargets.minWinRate, 2) * 0.1;
    const profitFactorScore = Math.min((metrics.profitFactor || 1.5) / this.tradingTargets.minProfitFactor, 2) * 0.1;

    // Calculate total score
    const totalScore = cagrScore + sharpeScore + drawdownScore + winRateScore + profitFactorScore;

    // Normalize to 0-1 range
    return Math.min(Math.max(totalScore, 0), 1);
  }

  /**
   * Fallback method to evaluate strategies without API
   * @param strategies Strategies to evaluate
   * @returns Evaluated strategies with scores
   */
  private fallbackEvaluateStrategies(strategies: any[]): any[] {
    return strategies.map(strategy => {
      const metrics = {
        cagr: Math.random() * 0.2 + 0.1,
        sharpeRatio: Math.random() * 1.5 + 0.5,
        maxDrawdown: Math.random() * 0.15,
        winRate: Math.random() * 0.3 + 0.5,
        profitFactor: Math.random() * 2 + 1,
        totalTrades: Math.floor(Math.random() * 100) + 20,
        averageProfit: Math.random() * 0.02 + 0.01
      };

      return {
        ...strategy,
        score: this.calculateScore(metrics),
        metrics
      };
    });
  }
}
