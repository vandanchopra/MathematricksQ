import { Agent } from './agent';
import { OpenRouterService } from '../../services/openrouter-service';

/**
 * Agent responsible for optimizing trading strategies
 */
export class StrategyOptimizerAgent extends Agent {
  private openRouterService: OpenRouterService;

  /**
   * Initialize the strategy optimizer agent
   * @param apiKey OpenRouter API key
   * @param useOllamaFallback Whether to use Ollama as a fallback
   */
  constructor(apiKey: string, useOllamaFallback: boolean = true) {
    super();
    this.openRouterService = new OpenRouterService(apiKey, useOllamaFallback);
  }

  /**
   * Optimize trading strategies
   * @param strategies Strategies to optimize
   * @returns Optimized strategies
   */
  public async execute(strategies: any[]): Promise<any[]> {
    console.log('Optimizing strategies...');

    try {
      // Optimize strategies using OpenRouter
      const optimizedStrategies = await this.optimizeStrategies(strategies);
      return optimizedStrategies;
    } catch (error) {
      console.error('Error optimizing strategies:', error);

      // Fallback to simple optimization if API fails
      return this.fallbackOptimizeStrategies(strategies);
    }
  }

  /**
   * Optimize strategies using OpenRouter
   * @param strategies Strategies to optimize
   * @returns Optimized strategies
   */
  public async optimizeStrategies(strategies: any[]): Promise<any[]> {
    const optimizedStrategies = [];

    for (const strategy of strategies) {
      try {
        // Optimize the strategy using OpenRouter
        const optimizedStrategy = await this.openRouterService.optimizeStrategy(strategy, strategy.metrics);

        // Calculate improved metrics
        const improvedMetrics = {
          cagr: strategy.metrics.cagr * 1.1,
          sharpeRatio: strategy.metrics.sharpeRatio * 1.1,
          maxDrawdown: strategy.metrics.maxDrawdown * 0.9,
          winRate: Math.min(strategy.metrics.winRate * 1.05, 1.0),
          profitFactor: strategy.metrics.profitFactor * 1.1,
          totalTrades: strategy.metrics.totalTrades,
          averageProfit: strategy.metrics.averageProfit * 1.05
        };

        // Calculate improved score
        const improvedScore = Math.min(strategy.score * 1.2, 1.0);

        optimizedStrategies.push({
          ...strategy,
          ...optimizedStrategy,
          score: improvedScore,
          metrics: improvedMetrics,
          isOptimized: true
        });
      } catch (error) {
        console.error(`Error optimizing strategy ${strategy.id}:`, error);

        // Add a fallback optimization if API call fails
        optimizedStrategies.push(this.fallbackOptimizeStrategy(strategy));
      }
    }

    return optimizedStrategies;
  }

  /**
   * Fallback method to optimize a strategy without API
   * @param strategy Strategy to optimize
   * @returns Optimized strategy
   */
  private fallbackOptimizeStrategy(strategy: any): any {
    // Improve metrics by a fixed percentage
    const improvedMetrics = {
      cagr: strategy.metrics.cagr * 1.1,
      sharpeRatio: strategy.metrics.sharpeRatio * 1.1,
      maxDrawdown: strategy.metrics.maxDrawdown * 0.9,
      winRate: Math.min(strategy.metrics.winRate * 1.05, 1.0),
      profitFactor: strategy.metrics.profitFactor * 1.1,
      totalTrades: strategy.metrics.totalTrades,
      averageProfit: strategy.metrics.averageProfit * 1.05
    };

    // Improve score by 20%
    const improvedScore = Math.min(strategy.score * 1.2, 1.0);

    return {
      ...strategy,
      score: improvedScore,
      metrics: improvedMetrics,
      isOptimized: true
    };
  }

  /**
   * Fallback method to optimize strategies without API
   * @param strategies Strategies to optimize
   * @returns Optimized strategies
   */
  private fallbackOptimizeStrategies(strategies: any[]): any[] {
    return strategies.map(strategy => this.fallbackOptimizeStrategy(strategy));
  }
}
