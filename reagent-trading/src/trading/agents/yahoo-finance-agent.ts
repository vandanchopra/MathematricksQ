import { Agent } from './agent';
import { YahooFinanceService } from '../../services/yahoo-finance-service';

/**
 * Agent responsible for retrieving financial data from Yahoo Finance
 */
export class YahooFinanceAgent extends Agent {
  private yahooFinanceService: YahooFinanceService;

  /**
   * Initialize the Yahoo Finance agent
   */
  constructor() {
    super();
    this.yahooFinanceService = new YahooFinanceService();
  }

  /**
   * Execute the Yahoo Finance agent to retrieve financial data
   * @param input Input parameters for data retrieval
   * @returns Financial data
   */
  public async execute(input: any): Promise<any> {
    console.log('Retrieving financial data from Yahoo Finance...');

    try {
      const { action, symbol, period, interval, category, count, query, limit } = input;

      switch (action) {
        case 'getStockQuote':
          return await this.yahooFinanceService.getStockQuote(symbol);
        
        case 'getHistoricalData':
          return await this.yahooFinanceService.getHistoricalData(symbol, period, interval);
        
        case 'getCompanyInfo':
          return await this.yahooFinanceService.getCompanyInfo(symbol);
        
        case 'getMarketNews':
          return await this.yahooFinanceService.getMarketNews(category, count);
        
        case 'search':
          return await this.yahooFinanceService.search(query, limit);
        
        default:
          throw new Error(`Unknown action: ${action}`);
      }
    } catch (error) {
      console.error('Error in Yahoo Finance agent:', error);
      return null;
    }
  }

  /**
   * Get stock quote data
   * @param symbol Stock symbol
   * @returns Stock quote data
   */
  public async getStockQuote(symbol: string): Promise<any> {
    return this.execute({ action: 'getStockQuote', symbol });
  }

  /**
   * Get historical stock data
   * @param symbol Stock symbol
   * @param period Period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
   * @param interval Interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
   * @returns Historical stock data
   */
  public async getHistoricalData(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    return this.execute({ action: 'getHistoricalData', symbol, period, interval });
  }

  /**
   * Get company information
   * @param symbol Stock symbol
   * @returns Company information
   */
  public async getCompanyInfo(symbol: string): Promise<any> {
    return this.execute({ action: 'getCompanyInfo', symbol });
  }

  /**
   * Get market news
   * @param category News category (e.g., 'general', 'stocks', 'economy', 'crypto')
   * @param count Number of news items to retrieve
   * @returns Market news
   */
  public async getMarketNews(
    category: string = 'general',
    count: number = 10
  ): Promise<any> {
    return this.execute({ action: 'getMarketNews', category, count });
  }

  /**
   * Search for stocks, ETFs, mutual funds, etc.
   * @param query Search query
   * @param limit Maximum number of results to return
   * @returns Search results
   */
  public async search(query: string, limit: number = 10): Promise<any> {
    return this.execute({ action: 'search', query, limit });
  }
}
