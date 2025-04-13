import { Agent } from './agent';
import { OpenRouterService } from '../../services/openrouter-service';
import { YahooFinanceService } from '../../services/yahoo-finance-service';

/**
 * Agent responsible for generating trading strategies
 */
export class StrategyGeneratorAgent extends Agent {
  private openRouterService: OpenRouterService;
  private yahooFinanceService: YahooFinanceService;

  /**
   * Initialize the strategy generator agent
   * @param apiKey OpenRouter API key
   * @param useOllamaFallback Whether to use Ollama as a fallback
   */
  constructor(apiKey: string, useOllamaFallback: boolean = true) {
    super();
    this.openRouterService = new OpenRouterService(apiKey, useOllamaFallback);
    this.yahooFinanceService = new YahooFinanceService();
  }

  /**
   * Generate trading strategies
   * @param input Input parameters for strategy generation
   * @returns Generated strategies
   */
  public async execute(input: any): Promise<any[]> {
    console.log('Generating strategies...');

    try {
      // Extract parameters from input
      const { symbols = ['SPY', 'AAPL', 'MSFT', 'AMZN', 'GOOGL'], period = '1y', interval = '1d' } = input || {};

      // Get market data for the specified symbols
      const marketData = await this.getMarketData(symbols, period, interval);

      // Generate strategies using OpenRouter with market data
      const strategies = await this.generateStrategies(marketData);

      // If we got strategies, return them
      if (strategies && strategies.length > 0) {
        return strategies;
      } else {
        console.log('No strategies generated, falling back to predefined strategies');
        return this.getFallbackStrategies();
      }
    } catch (error) {
      console.error('Error generating strategies:', error);

      // Fallback to predefined strategies if API fails
      console.log('Using fallback strategies due to API error');
      return this.getFallbackStrategies();
    }
  }

  /**
   * Generate strategies using OpenRouter
   * @param marketData Market data for strategy generation
   * @returns Generated strategies
   */
  public async generateStrategies(marketData?: any): Promise<any[]> {
    const strategyTypes = ['trend-following', 'mean-reversion', 'breakout', 'momentum'];
    const assetClasses = ['equities', 'forex', 'crypto'];

    const strategies = [];

    // Generate 2 strategies
    for (let i = 0; i < 2; i++) {
      const type = strategyTypes[Math.floor(Math.random() * strategyTypes.length)];
      const asset = assetClasses[Math.floor(Math.random() * assetClasses.length)];

      try {
        // Generate strategy with market data if available
        const strategy = marketData
          ? await this.openRouterService.generateStrategyWithMarketData(type, asset, marketData)
          : await this.openRouterService.generateStrategy(type, asset);

        // Add required fields for the system
        const processedStrategy = {
          id: `strategy_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          name: strategy.name,
          description: strategy.description,
          parameters: strategy.indicators.reduce((params: any, indicator: any) => {
            return { ...params, ...indicator.parameters };
          }, {}),
          entryConditions: strategy.entryConditions,
          exitConditions: strategy.exitConditions,
          riskManagement: strategy.riskManagement,
          indicators: strategy.indicators,
          timeframes: strategy.timeframes,
          expectedPerformance: strategy.expectedPerformance,
          marketDataUsed: marketData ? Object.keys(marketData) : []
        };

        strategies.push(processedStrategy);
      } catch (error) {
        console.error(`Error generating strategy ${i+1}:`, error);
        // Add a fallback strategy if API call fails
        strategies.push(this.getFallbackStrategies()[i % 2]);
      }
    }

    return strategies;
  }

  /**
   * Get market data for the specified symbols
   * @param symbols Array of stock symbols
   * @param period Period for historical data
   * @param interval Interval for historical data
   * @returns Market data for the specified symbols
   */
  private async getMarketData(symbols: string[], period: string, interval: string): Promise<any> {
    const marketData: any = {};

    for (const symbol of symbols) {
      try {
        // Get stock quote
        const quote = await this.yahooFinanceService.getStockQuote(symbol);

        // Get historical data
        const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);

        // Get company info
        const companyInfo = await this.yahooFinanceService.getCompanyInfo(symbol);

        // Add data to market data object
        marketData[symbol] = {
          quote,
          historicalData,
          companyInfo
        };
      } catch (error) {
        console.error(`Error getting market data for ${symbol}:`, error);
      }
    }

    return marketData;
  }

  /**
   * Get fallback strategies in case API calls fail
   * @returns Fallback strategies
   */
  private getFallbackStrategies(): any[] {
    return [
      {
        id: `strategy_${Date.now()}_1`,
        name: 'SMA Crossover',
        description: 'Simple Moving Average Crossover Strategy',
        parameters: { fastPeriod: 20, slowPeriod: 50 },
        entryConditions: ['Fast SMA crosses above Slow SMA'],
        exitConditions: ['Fast SMA crosses below Slow SMA'],
        riskManagement: ['2% risk per trade', 'Stop loss at 5%'],
        indicators: [
          { name: 'SMA', parameters: { period: 20 } },
          { name: 'SMA', parameters: { period: 50 } }
        ],
        timeframes: ['1D', '4H'],
        expectedPerformance: {
          cagr: 0.15,
          sharpeRatio: 1.2,
          maxDrawdown: 0.12,
          winRate: 0.55
        }
      },
      {
        id: `strategy_${Date.now()}_2`,
        name: 'RSI Strategy',
        description: 'Relative Strength Index Strategy',
        parameters: { rsiPeriod: 14, overbought: 70, oversold: 30 },
        entryConditions: ['RSI crosses below oversold level (30)'],
        exitConditions: ['RSI crosses above overbought level (70)'],
        riskManagement: ['1.5% risk per trade', 'Trailing stop at 8%'],
        indicators: [
          { name: 'RSI', parameters: { period: 14 } }
        ],
        timeframes: ['1D', '1H'],
        expectedPerformance: {
          cagr: 0.12,
          sharpeRatio: 1.0,
          maxDrawdown: 0.15,
          winRate: 0.52
        }
      }
    ];
  }
}
