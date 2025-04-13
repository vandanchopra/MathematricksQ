import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * Service for interacting with the Pandas AI MCP server
 */
export class PandasAIService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds
  private serverProcess: any;

  /**
   * Initialize the Pandas AI service
   * @param serverUrl URL of the Pandas AI MCP server
   * @param serverPort Port of the Pandas AI MCP server
   * @param cacheEnabled Whether to enable caching
   * @param cacheExpiration Cache expiration time in seconds
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8003,
    cacheEnabled: boolean = true,
    cacheExpiration: number = 3600 // 1 hour
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.cacheEnabled = cacheEnabled;
    this.cacheExpiration = cacheExpiration * 1000; // convert to milliseconds
    
    // Set up cache directory
    this.cachePath = path.join(process.cwd(), 'data', 'pandas-ai', 'cache');
    if (this.cacheEnabled && !fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
  }

  /**
   * Start the Pandas AI MCP server
   * @returns Promise that resolves when the server is started
   */
  public async startServer(): Promise<boolean> {
    try {
      console.log('Starting Pandas AI MCP server...');
      
      // Check if server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('Pandas AI MCP server is already running');
          return true;
        }
      } catch (error) {
        // Server is not running, continue with starting it
      }
      
      // Start the server using Docker
      this.serverProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.pandas-ai.yml'),
        'up',
        '-d'
      ]);
      
      // Wait for the server to start
      return new Promise((resolve) => {
        this.serverProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Pandas AI MCP server started successfully');
            
            // Wait for the server to be ready
            this.waitForServer(10, 1000)
              .then(() => resolve(true))
              .catch(() => resolve(false));
          } else {
            console.error(`Pandas AI MCP server failed to start with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error starting Pandas AI MCP server:', error);
      return false;
    }
  }

  /**
   * Stop the Pandas AI MCP server
   * @returns Promise that resolves when the server is stopped
   */
  public async stopServer(): Promise<boolean> {
    try {
      console.log('Stopping Pandas AI MCP server...');
      
      // Stop the server using Docker
      const stopProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.pandas-ai.yml'),
        'down'
      ]);
      
      // Wait for the server to stop
      return new Promise((resolve) => {
        stopProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Pandas AI MCP server stopped successfully');
            resolve(true);
          } else {
            console.error(`Pandas AI MCP server failed to stop with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error stopping Pandas AI MCP server:', error);
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
          console.log('Pandas AI MCP server is ready');
          return;
        }
      } catch (error) {
        console.log(`Waiting for Pandas AI MCP server to be ready (${i + 1}/${maxRetries})...`);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    throw new Error('Pandas AI MCP server failed to start');
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
   * Load a CSV file into a pandas DataFrame
   * @param filePath Path to the CSV file
   * @param options Options for loading the CSV file
   * @returns DataFrame ID
   */
  public async loadCSV(filePath: string, options: any = {}): Promise<string> {
    try {
      console.log(`Loading CSV file: ${filePath}`);
      
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        throw new Error(`File not found: ${filePath}`);
      }
      
      // Read the file content
      const fileContent = fs.readFileSync(filePath, 'utf8');
      
      // Prepare the request payload
      const payload = {
        name: 'load_csv',
        arguments: {
          content: fileContent,
          ...options
        }
      };
      
      // Call the Pandas AI MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result.dataframe_id;
    } catch (error) {
      console.error('Error loading CSV file:', error);
      throw error;
    }
  }

  /**
   * Load financial data into a pandas DataFrame
   * @param symbol Stock symbol
   * @param period Period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
   * @param interval Interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
   * @returns DataFrame ID
   */
  public async loadFinancialData(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<string> {
    try {
      console.log(`Loading financial data for: ${symbol}`);
      
      // Create cache key
      const cacheKey = `financial_${symbol}_${period}_${interval}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached financial data');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'load_financial_data',
        arguments: {
          symbol,
          period,
          interval
        }
      };
      
      // Call the Pandas AI MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.dataframe_id);
      }
      
      return result.dataframe_id;
    } catch (error) {
      console.error('Error loading financial data:', error);
      throw error;
    }
  }

  /**
   * Analyze a DataFrame
   * @param dataframeId DataFrame ID
   * @param query Query to analyze the DataFrame
   * @returns Analysis result
   */
  public async analyzeDataFrame(dataframeId: string, query: string): Promise<any> {
    try {
      console.log(`Analyzing DataFrame: ${dataframeId}`);
      
      // Create cache key
      const cacheKey = `analyze_${dataframeId}_${query.replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached analysis result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'analyze_dataframe',
        arguments: {
          dataframe_id: dataframeId,
          query
        }
      };
      
      // Call the Pandas AI MCP server
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
      console.error('Error analyzing DataFrame:', error);
      throw error;
    }
  }

  /**
   * Get DataFrame information
   * @param dataframeId DataFrame ID
   * @returns DataFrame information
   */
  public async getDataFrameInfo(dataframeId: string): Promise<any> {
    try {
      console.log(`Getting DataFrame info: ${dataframeId}`);
      
      // Create cache key
      const cacheKey = `info_${dataframeId}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached DataFrame info');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'get_dataframe_info',
        arguments: {
          dataframe_id: dataframeId
        }
      };
      
      // Call the Pandas AI MCP server
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
      console.error('Error getting DataFrame info:', error);
      throw error;
    }
  }

  /**
   * Get DataFrame statistics
   * @param dataframeId DataFrame ID
   * @returns DataFrame statistics
   */
  public async getDataFrameStats(dataframeId: string): Promise<any> {
    try {
      console.log(`Getting DataFrame stats: ${dataframeId}`);
      
      // Create cache key
      const cacheKey = `stats_${dataframeId}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached DataFrame stats');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'get_dataframe_stats',
        arguments: {
          dataframe_id: dataframeId
        }
      };
      
      // Call the Pandas AI MCP server
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
      console.error('Error getting DataFrame stats:', error);
      throw error;
    }
  }

  /**
   * Run a custom pandas operation on a DataFrame
   * @param dataframeId DataFrame ID
   * @param operation Pandas operation to run
   * @returns Operation result
   */
  public async runPandasOperation(dataframeId: string, operation: string): Promise<any> {
    try {
      console.log(`Running pandas operation on DataFrame: ${dataframeId}`);
      
      // Prepare the request payload
      const payload = {
        name: 'run_pandas_operation',
        arguments: {
          dataframe_id: dataframeId,
          operation
        }
      };
      
      // Call the Pandas AI MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      return JSON.parse(response.data.content[0].text);
    } catch (error) {
      console.error('Error running pandas operation:', error);
      throw error;
    }
  }

  /**
   * Generate a trading strategy based on financial data analysis
   * @param dataframeId DataFrame ID
   * @param strategyType Type of strategy to generate
   * @returns Generated strategy
   */
  public async generateTradingStrategy(dataframeId: string, strategyType: string): Promise<any> {
    try {
      console.log(`Generating ${strategyType} trading strategy from DataFrame: ${dataframeId}`);
      
      // Prepare the request payload
      const payload = {
        name: 'generate_trading_strategy',
        arguments: {
          dataframe_id: dataframeId,
          strategy_type: strategyType
        }
      };
      
      // Call the Pandas AI MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      return JSON.parse(response.data.content[0].text);
    } catch (error) {
      console.error('Error generating trading strategy:', error);
      throw error;
    }
  }

  /**
   * Backtest a trading strategy on financial data
   * @param dataframeId DataFrame ID
   * @param strategy Trading strategy to backtest
   * @returns Backtest results
   */
  public async backtestStrategy(dataframeId: string, strategy: any): Promise<any> {
    try {
      console.log(`Backtesting strategy on DataFrame: ${dataframeId}`);
      
      // Prepare the request payload
      const payload = {
        name: 'backtest_strategy',
        arguments: {
          dataframe_id: dataframeId,
          strategy: JSON.stringify(strategy)
        }
      };
      
      // Call the Pandas AI MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      return JSON.parse(response.data.content[0].text);
    } catch (error) {
      console.error('Error backtesting strategy:', error);
      throw error;
    }
  }
}
