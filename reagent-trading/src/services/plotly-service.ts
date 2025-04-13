import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * Service for interacting with the Plotly MCP server
 */
export class PlotlyService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds
  private serverProcess: any;

  /**
   * Initialize the Plotly service
   * @param serverUrl URL of the Plotly MCP server
   * @param serverPort Port of the Plotly MCP server
   * @param cacheEnabled Whether to enable caching
   * @param cacheExpiration Cache expiration time in seconds
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8004,
    cacheEnabled: boolean = true,
    cacheExpiration: number = 3600 // 1 hour
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.cacheEnabled = cacheEnabled;
    this.cacheExpiration = cacheExpiration * 1000; // convert to milliseconds
    
    // Set up cache directory
    this.cachePath = path.join(process.cwd(), 'data', 'plotly', 'cache');
    if (this.cacheEnabled && !fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
  }

  /**
   * Start the Plotly MCP server
   * @returns Promise that resolves when the server is started
   */
  public async startServer(): Promise<boolean> {
    try {
      console.log('Starting Plotly MCP server...');
      
      // Check if server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('Plotly MCP server is already running');
          return true;
        }
      } catch (error) {
        // Server is not running, continue with starting it
      }
      
      // Start the server using Docker
      this.serverProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.plotly.yml'),
        'up',
        '-d'
      ]);
      
      // Wait for the server to start
      return new Promise((resolve) => {
        this.serverProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Plotly MCP server started successfully');
            
            // Wait for the server to be ready
            this.waitForServer(10, 1000)
              .then(() => resolve(true))
              .catch(() => resolve(false));
          } else {
            console.error(`Plotly MCP server failed to start with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error starting Plotly MCP server:', error);
      return false;
    }
  }

  /**
   * Stop the Plotly MCP server
   * @returns Promise that resolves when the server is stopped
   */
  public async stopServer(): Promise<boolean> {
    try {
      console.log('Stopping Plotly MCP server...');
      
      // Stop the server using Docker
      const stopProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.plotly.yml'),
        'down'
      ]);
      
      // Wait for the server to stop
      return new Promise((resolve) => {
        stopProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Plotly MCP server stopped successfully');
            resolve(true);
          } else {
            console.error(`Plotly MCP server failed to stop with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error stopping Plotly MCP server:', error);
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
          console.log('Plotly MCP server is ready');
          return;
        }
      } catch (error) {
        console.log(`Waiting for Plotly MCP server to be ready (${i + 1}/${maxRetries})...`);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    throw new Error('Plotly MCP server failed to start');
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
   * Create a line chart
   * @param data Data for the chart
   * @param title Chart title
   * @param xLabel X-axis label
   * @param yLabel Y-axis label
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createLineChart(
    data: any,
    title: string,
    xLabel: string,
    yLabel: string,
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating line chart: ${title}`);
      
      // Create cache key
      const cacheKey = `line_${title.replace(/\s+/g, '_')}_${xLabel.replace(/\s+/g, '_')}_${yLabel.replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached line chart');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'create_line_chart',
        arguments: {
          data: JSON.stringify(data),
          title,
          x_label: xLabel,
          y_label: yLabel,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.chart_url);
      }
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating line chart:', error);
      throw error;
    }
  }

  /**
   * Create a candlestick chart
   * @param data Data for the chart
   * @param title Chart title
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createCandlestickChart(
    data: any,
    title: string,
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating candlestick chart: ${title}`);
      
      // Create cache key
      const cacheKey = `candlestick_${title.replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached candlestick chart');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'create_candlestick_chart',
        arguments: {
          data: JSON.stringify(data),
          title,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.chart_url);
      }
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating candlestick chart:', error);
      throw error;
    }
  }

  /**
   * Create a bar chart
   * @param data Data for the chart
   * @param title Chart title
   * @param xLabel X-axis label
   * @param yLabel Y-axis label
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createBarChart(
    data: any,
    title: string,
    xLabel: string,
    yLabel: string,
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating bar chart: ${title}`);
      
      // Create cache key
      const cacheKey = `bar_${title.replace(/\s+/g, '_')}_${xLabel.replace(/\s+/g, '_')}_${yLabel.replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached bar chart');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'create_bar_chart',
        arguments: {
          data: JSON.stringify(data),
          title,
          x_label: xLabel,
          y_label: yLabel,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.chart_url);
      }
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating bar chart:', error);
      throw error;
    }
  }

  /**
   * Create a scatter plot
   * @param data Data for the chart
   * @param title Chart title
   * @param xLabel X-axis label
   * @param yLabel Y-axis label
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createScatterPlot(
    data: any,
    title: string,
    xLabel: string,
    yLabel: string,
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating scatter plot: ${title}`);
      
      // Create cache key
      const cacheKey = `scatter_${title.replace(/\s+/g, '_')}_${xLabel.replace(/\s+/g, '_')}_${yLabel.replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached scatter plot');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'create_scatter_plot',
        arguments: {
          data: JSON.stringify(data),
          title,
          x_label: xLabel,
          y_label: yLabel,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.chart_url);
      }
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating scatter plot:', error);
      throw error;
    }
  }

  /**
   * Create a histogram
   * @param data Data for the chart
   * @param title Chart title
   * @param xLabel X-axis label
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createHistogram(
    data: any,
    title: string,
    xLabel: string,
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating histogram: ${title}`);
      
      // Create cache key
      const cacheKey = `histogram_${title.replace(/\s+/g, '_')}_${xLabel.replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached histogram');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'create_histogram',
        arguments: {
          data: JSON.stringify(data),
          title,
          x_label: xLabel,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.chart_url);
      }
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating histogram:', error);
      throw error;
    }
  }

  /**
   * Create a heatmap
   * @param data Data for the chart
   * @param title Chart title
   * @param xLabels X-axis labels
   * @param yLabels Y-axis labels
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createHeatmap(
    data: any,
    title: string,
    xLabels: string[],
    yLabels: string[],
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating heatmap: ${title}`);
      
      // Create cache key
      const cacheKey = `heatmap_${title.replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached heatmap');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'create_heatmap',
        arguments: {
          data: JSON.stringify(data),
          title,
          x_labels: JSON.stringify(xLabels),
          y_labels: JSON.stringify(yLabels),
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.chart_url);
      }
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating heatmap:', error);
      throw error;
    }
  }

  /**
   * Create a dashboard with multiple charts
   * @param charts Array of charts to include in the dashboard
   * @param title Dashboard title
   * @param layout Layout configuration for the dashboard
   * @returns Dashboard URL or base64 image
   */
  public async createDashboard(
    charts: any[],
    title: string,
    layout: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating dashboard: ${title}`);
      
      // Prepare the request payload
      const payload = {
        name: 'create_dashboard',
        arguments: {
          charts: JSON.stringify(charts),
          title,
          layout: JSON.stringify(layout)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result.dashboard_url;
    } catch (error) {
      console.error('Error creating dashboard:', error);
      throw error;
    }
  }

  /**
   * Create a technical analysis chart
   * @param data Financial data for the chart
   * @param title Chart title
   * @param indicators Technical indicators to include
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createTechnicalChart(
    data: any,
    title: string,
    indicators: any[] = [],
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating technical analysis chart: ${title}`);
      
      // Create cache key
      const cacheKey = `technical_${title.replace(/\s+/g, '_')}_${indicators.map(i => i.name).join('_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached technical analysis chart');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'create_technical_chart',
        arguments: {
          data: JSON.stringify(data),
          title,
          indicators: JSON.stringify(indicators),
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, result.chart_url);
      }
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating technical analysis chart:', error);
      throw error;
    }
  }

  /**
   * Create a backtest results visualization
   * @param backtestResults Backtest results data
   * @param title Chart title
   * @param options Additional options for the chart
   * @returns Chart URL or base64 image
   */
  public async createBacktestVisualization(
    backtestResults: any,
    title: string,
    options: any = {}
  ): Promise<string> {
    try {
      console.log(`Creating backtest visualization: ${title}`);
      
      // Prepare the request payload
      const payload = {
        name: 'create_backtest_visualization',
        arguments: {
          backtest_results: JSON.stringify(backtestResults),
          title,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Plotly MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result.chart_url;
    } catch (error) {
      console.error('Error creating backtest visualization:', error);
      throw error;
    }
  }
}
