import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Service for interacting with the Yahoo Finance MCP server
 */
export class YahooFinanceService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds

  /**
   * Initialize the Yahoo Finance service
   * @param serverUrl URL of the Yahoo Finance MCP server
   * @param serverPort Port of the Yahoo Finance MCP server
   * @param cacheEnabled Whether to enable caching
   * @param cacheExpiration Cache expiration time in seconds
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8001,
    cacheEnabled: boolean = true,
    cacheExpiration: number = 3600 // 1 hour
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.cacheEnabled = cacheEnabled;
    this.cacheExpiration = cacheExpiration * 1000; // convert to milliseconds
    
    // Set up cache directory
    this.cachePath = path.join(process.cwd(), 'data', 'yahoo-finance', 'cache');
    if (this.cacheEnabled && !fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
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
   * Get stock quote data
   * @param symbol Stock symbol
   * @returns Stock quote data
   */
  public async getStockQuote(symbol: string): Promise<any> {
    try {
      console.log(`Getting stock quote for: ${symbol}`);
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(`quote_${symbol}`);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload: any = {
        name: 'get_stock_quote',
        arguments: {
          symbol: symbol
        }
      };
      
      // Call the Yahoo Finance MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const data = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(`quote_${symbol}`, data);
      }
      
      return data;
    } catch (error) {
      console.error('Error getting stock quote:', error);
      return null;
    }
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
    try {
      console.log(`Getting historical data for: ${symbol}`);
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(`history_${symbol}_${period}_${interval}`);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload: any = {
        name: 'get_historical_data',
        arguments: {
          symbol: symbol,
          period: period,
          interval: interval
        }
      };
      
      // Call the Yahoo Finance MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const data = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(`history_${symbol}_${period}_${interval}`, data);
      }
      
      return data;
    } catch (error) {
      console.error('Error getting historical data:', error);
      return null;
    }
  }

  /**
   * Get company information
   * @param symbol Stock symbol
   * @returns Company information
   */
  public async getCompanyInfo(symbol: string): Promise<any> {
    try {
      console.log(`Getting company info for: ${symbol}`);
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(`company_${symbol}`);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload: any = {
        name: 'get_company_info',
        arguments: {
          symbol: symbol
        }
      };
      
      // Call the Yahoo Finance MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const data = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(`company_${symbol}`, data);
      }
      
      return data;
    } catch (error) {
      console.error('Error getting company info:', error);
      return null;
    }
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
    try {
      console.log(`Getting market news for category: ${category}`);
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(`news_${category}_${count}`);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload: any = {
        name: 'get_market_news',
        arguments: {
          category: category,
          count: count
        }
      };
      
      // Call the Yahoo Finance MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const data = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(`news_${category}_${count}`, data);
      }
      
      return data;
    } catch (error) {
      console.error('Error getting market news:', error);
      return null;
    }
  }

  /**
   * Search for stocks, ETFs, mutual funds, etc.
   * @param query Search query
   * @param limit Maximum number of results to return
   * @returns Search results
   */
  public async search(query: string, limit: number = 10): Promise<any> {
    try {
      console.log(`Searching for: ${query}`);
      
      // Prepare the request payload
      const payload: any = {
        name: 'search',
        arguments: {
          query: query,
          limit: limit
        }
      };
      
      // Call the Yahoo Finance MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      return JSON.parse(response.data.content[0].text);
    } catch (error) {
      console.error('Error searching:', error);
      return null;
    }
  }
}
