import { Agent } from './agent';
import { AlphaVantageService } from '../../services/alpha-vantage-service';

/**
 * Agent responsible for retrieving financial data from Alpha Vantage
 */
export class AlphaVantageAgent extends Agent {
  private alphaVantageService: AlphaVantageService;

  /**
   * Initialize the Alpha Vantage agent
   * @param apiKey Alpha Vantage API key
   */
  constructor(apiKey?: string) {
    super();
    this.alphaVantageService = new AlphaVantageService(
      'http://localhost',
      8002,
      apiKey || process.env.ALPHA_VANTAGE_API_KEY
    );
  }

  /**
   * Execute the Alpha Vantage agent to retrieve financial data
   * @param input Input parameters for data retrieval
   * @returns Financial data
   */
  public async execute(input: any): Promise<any> {
    console.log('Retrieving financial data from Alpha Vantage...');

    try {
      // Start the Alpha Vantage MCP server
      await this.alphaVantageService.startServer();

      const { action, symbol, interval, outputSize, indicator, timePeriod, seriesType, 
              fromCurrency, toCurrency, market, economicIndicator, maturity } = input;

      let result;
      switch (action) {
        case 'getTimeSeries':
          result = await this.alphaVantageService.getTimeSeries(symbol, interval, outputSize);
          break;
        
        case 'getTechnicalIndicator':
          result = await this.alphaVantageService.getTechnicalIndicator(symbol, indicator, interval, timePeriod, seriesType);
          break;
        
        case 'getSectorPerformance':
          result = await this.alphaVantageService.getSectorPerformance();
          break;
        
        case 'getForexData':
          result = await this.alphaVantageService.getForexData(fromCurrency, toCurrency, interval, outputSize);
          break;
        
        case 'getCryptoData':
          result = await this.alphaVantageService.getCryptoData(symbol, market, interval);
          break;
        
        case 'getEconomicIndicator':
          result = await this.alphaVantageService.getEconomicIndicator(economicIndicator, interval, maturity);
          break;
        
        case 'getCompanyOverview':
          result = await this.alphaVantageService.getCompanyOverview(symbol);
          break;
        
        case 'getEarnings':
          result = await this.alphaVantageService.getEarnings(symbol);
          break;
        
        case 'getIncomeStatement':
          result = await this.alphaVantageService.getIncomeStatement(symbol);
          break;
        
        case 'getBalanceSheet':
          result = await this.alphaVantageService.getBalanceSheet(symbol);
          break;
        
        case 'getCashFlow':
          result = await this.alphaVantageService.getCashFlow(symbol);
          break;
        
        case 'getGlobalMarketStatus':
          result = await this.alphaVantageService.getGlobalMarketStatus();
          break;
        
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      // Stop the Alpha Vantage MCP server
      await this.alphaVantageService.stopServer();

      return result;
    } catch (error) {
      console.error('Error in Alpha Vantage agent:', error);
      
      // Stop the Alpha Vantage MCP server
      await this.alphaVantageService.stopServer();
      
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Get time series data
   * @param symbol Stock symbol
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   * @param outputSize Output size ('compact' or 'full')
   * @returns Time series data
   */
  public async getTimeSeries(
    symbol: string,
    interval: string = 'daily',
    outputSize: string = 'compact'
  ): Promise<any> {
    return this.execute({ 
      action: 'getTimeSeries', 
      symbol, 
      interval, 
      outputSize 
    });
  }

  /**
   * Get technical indicator data
   * @param symbol Stock symbol
   * @param indicator Technical indicator (e.g., 'SMA', 'EMA', 'MACD', 'RSI', 'BBANDS', 'ADX', 'CCI', 'STOCH')
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   * @param timePeriod Time period
   * @param seriesType Series type (e.g., 'close', 'open', 'high', 'low')
   * @returns Technical indicator data
   */
  public async getTechnicalIndicator(
    symbol: string,
    indicator: string,
    interval: string = 'daily',
    timePeriod: number = 14,
    seriesType: string = 'close'
  ): Promise<any> {
    return this.execute({ 
      action: 'getTechnicalIndicator', 
      symbol, 
      indicator, 
      interval, 
      timePeriod, 
      seriesType 
    });
  }

  /**
   * Get sector performance data
   * @returns Sector performance data
   */
  public async getSectorPerformance(): Promise<any> {
    return this.execute({ action: 'getSectorPerformance' });
  }

  /**
   * Get forex data
   * @param fromCurrency From currency
   * @param toCurrency To currency
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   * @param outputSize Output size ('compact' or 'full')
   * @returns Forex data
   */
  public async getForexData(
    fromCurrency: string,
    toCurrency: string,
    interval: string = 'daily',
    outputSize: string = 'compact'
  ): Promise<any> {
    return this.execute({ 
      action: 'getForexData', 
      fromCurrency, 
      toCurrency, 
      interval, 
      outputSize 
    });
  }

  /**
   * Get crypto data
   * @param symbol Crypto symbol
   * @param market Market
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   * @returns Crypto data
   */
  public async getCryptoData(
    symbol: string,
    market: string = 'USD',
    interval: string = 'daily'
  ): Promise<any> {
    return this.execute({ 
      action: 'getCryptoData', 
      symbol, 
      market, 
      interval 
    });
  }

  /**
   * Get economic indicator data
   * @param economicIndicator Economic indicator (e.g., 'REAL_GDP', 'REAL_GDP_PER_CAPITA', 'TREASURY_YIELD', 'FEDERAL_FUNDS_RATE', 'CPI', 'INFLATION', 'RETAIL_SALES', 'DURABLES', 'UNEMPLOYMENT', 'NONFARM_PAYROLL')
   * @param interval Interval (e.g., 'annual', 'quarterly', 'monthly', 'daily')
   * @param maturity Maturity (for treasury yield, e.g., '3month', '5year', '10year', '30year')
   * @returns Economic indicator data
   */
  public async getEconomicIndicator(
    economicIndicator: string,
    interval: string = 'monthly',
    maturity: string = ''
  ): Promise<any> {
    return this.execute({ 
      action: 'getEconomicIndicator', 
      economicIndicator, 
      interval, 
      maturity 
    });
  }

  /**
   * Get company overview
   * @param symbol Stock symbol
   * @returns Company overview
   */
  public async getCompanyOverview(symbol: string): Promise<any> {
    return this.execute({ action: 'getCompanyOverview', symbol });
  }

  /**
   * Get earnings data
   * @param symbol Stock symbol
   * @returns Earnings data
   */
  public async getEarnings(symbol: string): Promise<any> {
    return this.execute({ action: 'getEarnings', symbol });
  }

  /**
   * Get income statement
   * @param symbol Stock symbol
   * @returns Income statement
   */
  public async getIncomeStatement(symbol: string): Promise<any> {
    return this.execute({ action: 'getIncomeStatement', symbol });
  }

  /**
   * Get balance sheet
   * @param symbol Stock symbol
   * @returns Balance sheet
   */
  public async getBalanceSheet(symbol: string): Promise<any> {
    return this.execute({ action: 'getBalanceSheet', symbol });
  }

  /**
   * Get cash flow
   * @param symbol Stock symbol
   * @returns Cash flow
   */
  public async getCashFlow(symbol: string): Promise<any> {
    return this.execute({ action: 'getCashFlow', symbol });
  }

  /**
   * Get global market status
   * @returns Global market status
   */
  public async getGlobalMarketStatus(): Promise<any> {
    return this.execute({ action: 'getGlobalMarketStatus' });
  }
}
