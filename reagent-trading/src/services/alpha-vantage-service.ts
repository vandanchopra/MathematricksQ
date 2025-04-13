import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * Service for interacting with the Alpha Vantage MCP server
 */
export class AlphaVantageService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds
  private serverProcess: any;
  private apiKey: string;

  /**
   * Initialize the Alpha Vantage service
   * @param serverUrl URL of the Alpha Vantage MCP server
   * @param serverPort Port of the Alpha Vantage MCP server
   * @param apiKey Alpha Vantage API key
   * @param cacheEnabled Whether to enable caching
   * @param cacheExpiration Cache expiration time in seconds
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8002,
    apiKey: string = process.env.ALPHA_VANTAGE_API_KEY || '',
    cacheEnabled: boolean = true,
    cacheExpiration: number = 3600 // 1 hour
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.apiKey = apiKey;
    this.cacheEnabled = cacheEnabled;
    this.cacheExpiration = cacheExpiration * 1000; // convert to milliseconds
    
    // Set up cache directory
    this.cachePath = path.join(process.cwd(), 'data', 'alpha-vantage', 'cache');
    if (this.cacheEnabled && !fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
  }

  /**
   * Start the Alpha Vantage MCP server
   * @returns Promise that resolves when the server is started
   */
  public async startServer(): Promise<boolean> {
    try {
      console.log('Starting Alpha Vantage MCP server...');
      
      // Check if server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('Alpha Vantage MCP server is already running');
          return true;
        }
      } catch (error) {
        // Server is not running, continue with starting it
      }
      
      // Start the server using Docker
      this.serverProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.alpha-vantage.yml'),
        'up',
        '-d'
      ]);
      
      // Wait for the server to start
      return new Promise((resolve) => {
        this.serverProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Alpha Vantage MCP server started successfully');
            
            // Wait for the server to be ready
            this.waitForServer(10, 1000)
              .then(() => resolve(true))
              .catch(() => resolve(false));
          } else {
            console.error(`Alpha Vantage MCP server failed to start with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error starting Alpha Vantage MCP server:', error);
      return false;
    }
  }

  /**
   * Stop the Alpha Vantage MCP server
   * @returns Promise that resolves when the server is stopped
   */
  public async stopServer(): Promise<boolean> {
    try {
      console.log('Stopping Alpha Vantage MCP server...');
      
      // Stop the server using Docker
      const stopProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.alpha-vantage.yml'),
        'down'
      ]);
      
      // Wait for the server to stop
      return new Promise((resolve) => {
        stopProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Alpha Vantage MCP server stopped successfully');
            resolve(true);
          } else {
            console.error(`Alpha Vantage MCP server failed to stop with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error stopping Alpha Vantage MCP server:', error);
      return false;
    }
  }

  /**
   * Wait for the server to be ready
   * @param maxRetries Maximum number of retries
   * @param delay Delay between retries in milliseconds
   * @returns Promise that resolves when the server is ready
   */
  private async waitForServer(maxRetries: number, delay: number): Promise<void> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('Alpha Vantage MCP server is ready');
          return;
        }
      } catch (error) {
        console.log(`Waiting for Alpha Vantage MCP server to be ready (${i + 1}/${maxRetries})...`);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    throw new Error('Alpha Vantage MCP server failed to start');
  }

  /**
   * Get data from cache
   * @param key Cache key
   * @returns Cached data or null if not found or expired
   */
  private getFromCache(key: string): any {
    try {
      const cacheFile = path.join(this.cachePath, `${key}.json`);
      
      // Check if cache file exists
      if (!fs.existsSync(cacheFile)) {
        return null;
      }
      
      // Read cache file
      const cacheData = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
      
      // Check if cache is expired
      if (Date.now() - cacheData.timestamp > this.cacheExpiration) {
        // Cache is expired, delete the file
        fs.unlinkSync(cacheFile);
        return null;
      }
      
      return cacheData.data;
    } catch (error) {
      console.error('Error reading from cache:', error);
      return null;
    }
  }

  /**
   * Save data to cache
   * @param key Cache key
   * @param data Data to cache
   */
  private saveToCache(key: string, data: any): void {
    try {
      const cacheFile = path.join(this.cachePath, `${key}.json`);
      
      // Create cache object with timestamp
      const cacheData = {
        timestamp: Date.now(),
        data: data
      };
      
      // Write to cache file
      fs.writeFileSync(cacheFile, JSON.stringify(cacheData, null, 2));
    } catch (error) {
      console.error('Error saving to cache:', error);
    }
  }

  /**
   * Call the Alpha Vantage MCP server
   * @param functionName Function name
   * @param params Function parameters
   * @returns Response data
   */
  private async callServer(functionName: string, params: any = {}): Promise<any> {
    try {
      // Add API key to parameters
      const allParams = { ...params, apikey: this.apiKey };
      
      // Create cache key
      const cacheKey = `${functionName}_${JSON.stringify(allParams)}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log(`Using cached data for ${functionName}`);
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: functionName,
        arguments: allParams
      };
      
      // Call the Alpha Vantage MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result);
      }
      
      return result;
    } catch (error) {
      console.error(`Error calling Alpha Vantage MCP server (${functionName}):`, error);
      throw error;
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
    console.log(`Getting time series data for: ${symbol} (${interval})`);
    
    // Map interval to function name
    let functionName: string;
    switch (interval) {
      case '1min':
        functionName = 'TIME_SERIES_INTRADAY';
        break;
      case '5min':
        functionName = 'TIME_SERIES_INTRADAY';
        break;
      case '15min':
        functionName = 'TIME_SERIES_INTRADAY';
        break;
      case '30min':
        functionName = 'TIME_SERIES_INTRADAY';
        break;
      case '60min':
        functionName = 'TIME_SERIES_INTRADAY';
        break;
      case 'daily':
        functionName = 'TIME_SERIES_DAILY';
        break;
      case 'weekly':
        functionName = 'TIME_SERIES_WEEKLY';
        break;
      case 'monthly':
        functionName = 'TIME_SERIES_MONTHLY';
        break;
      default:
        functionName = 'TIME_SERIES_DAILY';
    }
    
    // Prepare parameters
    const params: any = {
      symbol,
      outputsize: outputSize
    };
    
    // Add interval parameter for intraday data
    if (functionName === 'TIME_SERIES_INTRADAY') {
      params.interval = interval;
    }
    
    return this.callServer(functionName, params);
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
    console.log(`Getting ${indicator} data for: ${symbol} (${interval}, period: ${timePeriod})`);
    
    // Map indicator to function name
    const functionName = `${indicator}`;
    
    // Prepare parameters
    const params: any = {
      symbol,
      interval,
      time_period: timePeriod,
      series_type: seriesType
    };
    
    return this.callServer(functionName, params);
  }

  /**
   * Get sector performance data
   * @returns Sector performance data
   */
  public async getSectorPerformance(): Promise<any> {
    console.log('Getting sector performance data');
    
    return this.callServer('SECTOR');
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
    console.log(`Getting forex data for: ${fromCurrency}/${toCurrency} (${interval})`);
    
    // Map interval to function name
    let functionName: string;
    switch (interval) {
      case '1min':
        functionName = 'FX_INTRADAY';
        break;
      case '5min':
        functionName = 'FX_INTRADAY';
        break;
      case '15min':
        functionName = 'FX_INTRADAY';
        break;
      case '30min':
        functionName = 'FX_INTRADAY';
        break;
      case '60min':
        functionName = 'FX_INTRADAY';
        break;
      case 'daily':
        functionName = 'FX_DAILY';
        break;
      case 'weekly':
        functionName = 'FX_WEEKLY';
        break;
      case 'monthly':
        functionName = 'FX_MONTHLY';
        break;
      default:
        functionName = 'FX_DAILY';
    }
    
    // Prepare parameters
    const params: any = {
      from_currency: fromCurrency,
      to_currency: toCurrency,
      outputsize: outputSize
    };
    
    // Add interval parameter for intraday data
    if (functionName === 'FX_INTRADAY') {
      params.interval = interval;
    }
    
    return this.callServer(functionName, params);
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
    console.log(`Getting crypto data for: ${symbol}/${market} (${interval})`);
    
    // Map interval to function name
    let functionName: string;
    switch (interval) {
      case '1min':
        functionName = 'CRYPTO_INTRADAY';
        break;
      case '5min':
        functionName = 'CRYPTO_INTRADAY';
        break;
      case '15min':
        functionName = 'CRYPTO_INTRADAY';
        break;
      case '30min':
        functionName = 'CRYPTO_INTRADAY';
        break;
      case '60min':
        functionName = 'CRYPTO_INTRADAY';
        break;
      case 'daily':
        functionName = 'DIGITAL_CURRENCY_DAILY';
        break;
      case 'weekly':
        functionName = 'DIGITAL_CURRENCY_WEEKLY';
        break;
      case 'monthly':
        functionName = 'DIGITAL_CURRENCY_MONTHLY';
        break;
      default:
        functionName = 'DIGITAL_CURRENCY_DAILY';
    }
    
    // Prepare parameters
    const params: any = {
      symbol,
      market
    };
    
    // Add interval parameter for intraday data
    if (functionName === 'CRYPTO_INTRADAY') {
      params.interval = interval;
    }
    
    return this.callServer(functionName, params);
  }

  /**
   * Get economic indicator data
   * @param indicator Economic indicator (e.g., 'REAL_GDP', 'REAL_GDP_PER_CAPITA', 'TREASURY_YIELD', 'FEDERAL_FUNDS_RATE', 'CPI', 'INFLATION', 'RETAIL_SALES', 'DURABLES', 'UNEMPLOYMENT', 'NONFARM_PAYROLL')
   * @param interval Interval (e.g., 'annual', 'quarterly', 'monthly', 'daily')
   * @param maturity Maturity (for treasury yield, e.g., '3month', '5year', '10year', '30year')
   * @returns Economic indicator data
   */
  public async getEconomicIndicator(
    indicator: string,
    interval: string = 'monthly',
    maturity: string = ''
  ): Promise<any> {
    console.log(`Getting economic indicator data for: ${indicator} (${interval})`);
    
    // Prepare parameters
    const params: any = {
      function: indicator,
      interval
    };
    
    // Add maturity parameter for treasury yield
    if (indicator === 'TREASURY_YIELD' && maturity) {
      params.maturity = maturity;
    }
    
    return this.callServer('ECONOMIC', params);
  }

  /**
   * Get company overview
   * @param symbol Stock symbol
   * @returns Company overview
   */
  public async getCompanyOverview(symbol: string): Promise<any> {
    console.log(`Getting company overview for: ${symbol}`);
    
    return this.callServer('OVERVIEW', { symbol });
  }

  /**
   * Get earnings data
   * @param symbol Stock symbol
   * @returns Earnings data
   */
  public async getEarnings(symbol: string): Promise<any> {
    console.log(`Getting earnings data for: ${symbol}`);
    
    return this.callServer('EARNINGS', { symbol });
  }

  /**
   * Get income statement
   * @param symbol Stock symbol
   * @returns Income statement
   */
  public async getIncomeStatement(symbol: string): Promise<any> {
    console.log(`Getting income statement for: ${symbol}`);
    
    return this.callServer('INCOME_STATEMENT', { symbol });
  }

  /**
   * Get balance sheet
   * @param symbol Stock symbol
   * @returns Balance sheet
   */
  public async getBalanceSheet(symbol: string): Promise<any> {
    console.log(`Getting balance sheet for: ${symbol}`);
    
    return this.callServer('BALANCE_SHEET', { symbol });
  }

  /**
   * Get cash flow
   * @param symbol Stock symbol
   * @returns Cash flow
   */
  public async getCashFlow(symbol: string): Promise<any> {
    console.log(`Getting cash flow for: ${symbol}`);
    
    return this.callServer('CASH_FLOW', { symbol });
  }

  /**
   * Get global market status
   * @returns Global market status
   */
  public async getGlobalMarketStatus(): Promise<any> {
    console.log('Getting global market status');
    
    return this.callServer('GLOBAL_MARKET_STATUS');
  }
}
