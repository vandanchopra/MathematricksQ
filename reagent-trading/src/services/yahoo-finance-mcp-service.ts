import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * Service for interacting with the Yahoo Finance MCP server
 */
export class YahooFinanceMCPService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds
  private serverProcess: any;

  /**
   * Initialize the Yahoo Finance MCP service
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
   * Start the Yahoo Finance MCP server
   * @returns Promise that resolves when the server is started
   */
  public async startServer(): Promise<boolean> {
    try {
      console.log('Starting Yahoo Finance MCP server...');

      // Check if server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('Yahoo Finance MCP server is already running');
          return true;
        }
      } catch (error) {
        // Server is not running, continue with starting it
      }

      // Start the server using Docker
      this.serverProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.yahoo-finance.yml'),
        'up',
        '-d'
      ]);

      // Wait for the server to start
      return new Promise((resolve) => {
        this.serverProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Yahoo Finance MCP server started successfully');

            // Wait for the server to be ready
            this.waitForServer(10, 1000)
              .then(() => resolve(true))
              .catch(() => resolve(false));
          } else {
            console.error(`Yahoo Finance MCP server failed to start with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error starting Yahoo Finance MCP server:', error);
      return false;
    }
  }

  /**
   * Stop the Yahoo Finance MCP server
   * @returns Promise that resolves when the server is stopped
   */
  public async stopServer(): Promise<boolean> {
    try {
      console.log('Stopping Yahoo Finance MCP server...');

      // Stop the server using Docker
      const stopProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.yahoo-finance.yml'),
        'down'
      ]);

      // Wait for the server to stop
      return new Promise((resolve) => {
        stopProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Yahoo Finance MCP server stopped successfully');
            resolve(true);
          } else {
            console.error(`Yahoo Finance MCP server failed to stop with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error stopping Yahoo Finance MCP server:', error);
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
          console.log('Yahoo Finance MCP server is ready');
          return;
        }
      } catch (error) {
        console.log(`Waiting for Yahoo Finance MCP server to be ready (${i + 1}/${maxRetries})...`);
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    throw new Error('Yahoo Finance MCP server failed to start');
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
   * Get stock quote
   * @param symbol Stock symbol
   * @returns Stock quote data
   */
  public async getStockQuote(symbol: string): Promise<any> {
    try {
      console.log(`Getting stock quote for: ${symbol}`);

      // Create cache key
      const cacheKey = `quote_${symbol}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached stock quote');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_stock_quote',
        arguments: {
          symbol
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting stock quote:', error);
      throw error;
    }
  }

  /**
   * Get historical data
   * @param symbol Stock symbol
   * @param period Period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
   * @param interval Interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
   * @returns Historical data
   */
  public async getHistoricalData(symbol: string, period: string = '1y', interval: string = '1d'): Promise<any> {
    try {
      console.log(`Getting historical data for: ${symbol} (${period}, ${interval})`);

      // Create cache key
      const cacheKey = `historical_${symbol}_${period}_${interval}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached historical data');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_historical_data',
        arguments: {
          symbol,
          period,
          interval
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting historical data:', error);
      throw error;
    }
  }

  /**
   * Get company information
   * @param symbol Stock symbol
   * @returns Company information
   */
  public async getCompanyInfo(symbol: string): Promise<any> {
    try {
      console.log(`Getting company information for: ${symbol}`);

      // Create cache key
      const cacheKey = `company_${symbol}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached company information');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_company_info',
        arguments: {
          symbol
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting company information:', error);
      throw error;
    }
  }

  /**
   * Get market news
   * @param category News category (e.g., 'general', 'stocks', 'economy', 'forex', 'crypto')
   * @param count Number of news items to return
   * @returns Market news
   */
  public async getMarketNews(category: string = 'general', count: number = 10): Promise<any> {
    try {
      console.log(`Getting market news for category: ${category} (${count} items)`);

      // Create cache key
      const cacheKey = `news_${category}_${count}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached market news');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_market_news',
        arguments: {
          category,
          count: count.toString()
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting market news:', error);
      throw error;
    }
  }

  /**
   * Get stock options data
   * @param symbol Stock symbol
   * @param expirationDate Expiration date (YYYY-MM-DD)
   * @returns Options data
   */
  public async getOptionsData(symbol: string, expirationDate?: string): Promise<any> {
    try {
      console.log(`Getting options data for: ${symbol}${expirationDate ? ` (expiration: ${expirationDate})` : ''}`);

      // Create cache key
      const cacheKey = `options_${symbol}${expirationDate ? `_${expirationDate}` : ''}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached options data');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_options_data',
        arguments: {
          symbol,
          expiration_date: expirationDate || ''
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting options data:', error);
      throw error;
    }
  }

  /**
   * Get earnings calendar
   * @param startDate Start date (YYYY-MM-DD)
   * @param endDate End date (YYYY-MM-DD)
   * @returns Earnings calendar
   */
  public async getEarningsCalendar(startDate?: string, endDate?: string): Promise<any> {
    try {
      console.log(`Getting earnings calendar${startDate ? ` from ${startDate}` : ''}${endDate ? ` to ${endDate}` : ''}`);

      // Create cache key
      const cacheKey = `earnings${startDate ? `_${startDate}` : ''}${endDate ? `_${endDate}` : ''}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached earnings calendar');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_earnings_calendar',
        arguments: {
          start_date: startDate || '',
          end_date: endDate || ''
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting earnings calendar:', error);
      throw error;
    }
  }

  /**
   * Get market summary
   * @returns Market summary
   */
  public async getMarketSummary(): Promise<any> {
    try {
      console.log('Getting market summary');

      // Create cache key
      const cacheKey = `market_summary`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached market summary');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_market_summary',
        arguments: {}
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting market summary:', error);
      throw error;
    }
  }

  /**
   * Get trending tickers
   * @param region Region (e.g., 'US', 'CA', 'FR', 'DE', 'IT', 'ES', 'GB', 'IN')
   * @param count Number of trending tickers to return
   * @returns Trending tickers
   */
  public async getTrendingTickers(region: string = 'US', count: number = 10): Promise<any> {
    try {
      console.log(`Getting trending tickers for region: ${region} (${count} items)`);

      // Create cache key
      const cacheKey = `trending_${region}_${count}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached trending tickers');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_trending_tickers',
        arguments: {
          region,
          count: count.toString()
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting trending tickers:', error);
      throw error;
    }
  }

  /**
   * Search for financial instruments
   * @param query Search query
   * @param limit Maximum number of results to return
   * @returns Search results
   */
  public async searchFinancial(query: string, limit: number = 10): Promise<any> {
    try {
      console.log(`Searching for financial instruments: ${query} (limit: ${limit})`);

      // Create cache key
      const cacheKey = `search_${query.replace(/\s+/g, '_')}_${limit}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached search results');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'search_financial',
        arguments: {
          query,
          limit: limit.toString()
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error searching for financial instruments:', error);
      throw error;
    }
  }

  /**
   * Get sector performance
   * @param timeRange Time range (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max')
   * @returns Sector performance
   */
  public async getSectorPerformance(timeRange: string = '1d'): Promise<any> {
    try {
      console.log(`Getting sector performance for time range: ${timeRange}`);

      // Create cache key
      const cacheKey = `sectors_${timeRange}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached sector performance');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_sector_performance',
        arguments: {
          time_range: timeRange
        }
      };

      // Call the Yahoo Finance MCP server
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
      console.error('Error getting sector performance:', error);
      throw error;
    }
  }
}
