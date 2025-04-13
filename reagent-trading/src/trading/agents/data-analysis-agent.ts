import { Agent } from './agent';
import { PandasAIService } from '../../services/pandas-ai-service';
import { YahooFinanceService } from '../../services/yahoo-finance-service';

/**
 * Agent responsible for analyzing financial data
 */
export class DataAnalysisAgent extends Agent {
  private pandasAIService: PandasAIService;
  private yahooFinanceService: YahooFinanceService;

  /**
   * Initialize the data analysis agent
   */
  constructor() {
    super();
    this.pandasAIService = new PandasAIService();
    this.yahooFinanceService = new YahooFinanceService();
  }

  /**
   * Execute the data analysis agent
   * @param input Input parameters for data analysis
   * @returns Analysis results
   */
  public async execute(input: any): Promise<any> {
    console.log('Analyzing financial data...');

    try {
      // Start the Pandas AI MCP server
      await this.pandasAIService.startServer();

      // Extract parameters from input
      const { symbol, period = '1y', interval = '1d', query } = input;

      // Load financial data
      const dataframeId = await this.pandasAIService.loadFinancialData(symbol, period, interval);
      console.log(`Loaded financial data for ${symbol} into DataFrame: ${dataframeId}`);

      // Get DataFrame information
      const dataframeInfo = await this.pandasAIService.getDataFrameInfo(dataframeId);
      console.log('DataFrame information:', dataframeInfo);

      // Get DataFrame statistics
      const dataframeStats = await this.pandasAIService.getDataFrameStats(dataframeId);
      console.log('DataFrame statistics:', dataframeStats);

      // Analyze the DataFrame
      let analysisResult;
      if (query) {
        analysisResult = await this.pandasAIService.analyzeDataFrame(dataframeId, query);
        console.log('Analysis result:', analysisResult);
      }

      // Get stock quote for additional context
      const stockQuote = await this.yahooFinanceService.getStockQuote(symbol);
      console.log('Stock quote:', stockQuote);

      // Get company information for additional context
      const companyInfo = await this.yahooFinanceService.getCompanyInfo(symbol);
      console.log('Company information:', companyInfo);

      return {
        symbol,
        period,
        interval,
        dataframeId,
        dataframeInfo,
        dataframeStats,
        analysisResult,
        stockQuote,
        companyInfo
      };
    } catch (error) {
      console.error('Error in data analysis agent:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Pandas AI MCP server
      await this.pandasAIService.stopServer();
    }
  }

  /**
   * Analyze financial data for a specific symbol
   * @param symbol Stock symbol
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @returns Analysis results
   */
  public async analyzeFinancialData(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    return this.execute({ symbol, period, interval });
  }

  /**
   * Run a custom analysis query on financial data
   * @param symbol Stock symbol
   * @param query Analysis query
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @returns Analysis results
   */
  public async runAnalysisQuery(
    symbol: string,
    query: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    return this.execute({ symbol, period, interval, query });
  }

  /**
   * Generate a trading strategy based on financial data analysis
   * @param symbol Stock symbol
   * @param strategyType Type of strategy to generate
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @returns Generated strategy
   */
  public async generateTradingStrategy(
    symbol: string,
    strategyType: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    try {
      // Start the Pandas AI MCP server
      await this.pandasAIService.startServer();

      // Load financial data
      const dataframeId = await this.pandasAIService.loadFinancialData(symbol, period, interval);
      console.log(`Loaded financial data for ${symbol} into DataFrame: ${dataframeId}`);

      // Generate trading strategy
      const strategy = await this.pandasAIService.generateTradingStrategy(dataframeId, strategyType);
      console.log('Generated trading strategy:', strategy);

      // Backtest the strategy
      const backtestResults = await this.pandasAIService.backtestStrategy(dataframeId, strategy);
      console.log('Backtest results:', backtestResults);

      return {
        symbol,
        period,
        interval,
        strategyType,
        strategy,
        backtestResults
      };
    } catch (error) {
      console.error('Error generating trading strategy:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Pandas AI MCP server
      await this.pandasAIService.stopServer();
    }
  }

  /**
   * Analyze multiple symbols for comparison
   * @param symbols Array of stock symbols
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @returns Comparison results
   */
  public async compareSymbols(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    try {
      // Start the Pandas AI MCP server
      await this.pandasAIService.startServer();

      const results: Record<string, any> = {};

      // Analyze each symbol
      for (const symbol of symbols) {
        try {
          // Load financial data
          const dataframeId = await this.pandasAIService.loadFinancialData(symbol, period, interval);
          console.log(`Loaded financial data for ${symbol} into DataFrame: ${dataframeId}`);

          // Get DataFrame statistics
          const dataframeStats = await this.pandasAIService.getDataFrameStats(dataframeId);
          console.log(`Statistics for ${symbol}:`, dataframeStats);

          // Get stock quote
          const stockQuote = await this.yahooFinanceService.getStockQuote(symbol);

          // Add to results
          results[symbol] = {
            dataframeId,
            dataframeStats,
            stockQuote
          };
        } catch (error) {
          console.error(`Error analyzing ${symbol}:`, error);
          results[symbol] = {
            error: error instanceof Error ? error.message : String(error)
          };
        }
      }

      // Run comparison analysis
      const comparisonQuery = `Compare the performance of ${symbols.join(', ')} over the given period`;
      const comparisonAnalysis = await this.pandasAIService.analyzeDataFrame(
        Object.values(results).map((result: any) => result.dataframeId).join(','),
        comparisonQuery
      );

      return {
        symbols,
        period,
        interval,
        individualResults: results,
        comparisonAnalysis
      };
    } catch (error) {
      console.error('Error comparing symbols:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Pandas AI MCP server
      await this.pandasAIService.stopServer();
    }
  }
}
