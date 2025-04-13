import { Agent } from './agent';
import { PlotlyService } from '../../services/plotly-service';
import { YahooFinanceService } from '../../services/yahoo-finance-service';

/**
 * Agent responsible for creating visualizations of financial data
 */
export class VisualizationAgent extends Agent {
  private plotlyService: PlotlyService;
  private yahooFinanceService: YahooFinanceService;

  /**
   * Initialize the visualization agent
   */
  constructor() {
    super();
    this.plotlyService = new PlotlyService();
    this.yahooFinanceService = new YahooFinanceService();
  }

  /**
   * Execute the visualization agent
   * @param input Input parameters for visualization
   * @returns Visualization results
   */
  public async execute(input: any): Promise<any> {
    console.log('Creating visualizations...');

    try {
      // Start the Plotly MCP server
      await this.plotlyService.startServer();

      // Extract parameters from input
      const { symbol, chartType, period = '1y', interval = '1d', title, indicators = [] } = input;

      // Get historical data
      const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);
      console.log(`Got historical data for ${symbol}: ${historicalData.length} data points`);

      // Create visualization based on chart type
      let chartUrl;
      switch (chartType) {
        case 'line':
          chartUrl = await this.createLineChart(historicalData, symbol, title);
          break;
        case 'candlestick':
          chartUrl = await this.createCandlestickChart(historicalData, symbol, title);
          break;
        case 'technical':
          chartUrl = await this.createTechnicalChart(historicalData, symbol, title, indicators);
          break;
        default:
          throw new Error(`Unsupported chart type: ${chartType}`);
      }

      return {
        symbol,
        chartType,
        period,
        interval,
        chartUrl
      };
    } catch (error) {
      console.error('Error in visualization agent:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Plotly MCP server
      await this.plotlyService.stopServer();
    }
  }

  /**
   * Create a line chart for a stock
   * @param historicalData Historical price data
   * @param symbol Stock symbol
   * @param customTitle Custom title for the chart
   * @returns Chart URL
   */
  private async createLineChart(
    historicalData: any[],
    symbol: string,
    customTitle?: string
  ): Promise<string> {
    // Prepare data for the chart
    const dates = historicalData.map(item => item.date);
    const prices = historicalData.map(item => item.close);

    const data = {
      x: dates,
      y: prices,
      type: 'line',
      name: symbol
    };

    // Create the chart
    return await this.plotlyService.createLineChart(
      [data],
      customTitle || `${symbol} Price History`,
      'Date',
      'Price'
    );
  }

  /**
   * Create a candlestick chart for a stock
   * @param historicalData Historical price data
   * @param symbol Stock symbol
   * @param customTitle Custom title for the chart
   * @returns Chart URL
   */
  private async createCandlestickChart(
    historicalData: any[],
    symbol: string,
    customTitle?: string
  ): Promise<string> {
    // Prepare data for the chart
    const data = {
      x: historicalData.map(item => item.date),
      open: historicalData.map(item => item.open),
      high: historicalData.map(item => item.high),
      low: historicalData.map(item => item.low),
      close: historicalData.map(item => item.close),
      type: 'candlestick',
      name: symbol
    };

    // Create the chart
    return await this.plotlyService.createCandlestickChart(
      data,
      customTitle || `${symbol} Candlestick Chart`
    );
  }

  /**
   * Create a technical analysis chart for a stock
   * @param historicalData Historical price data
   * @param symbol Stock symbol
   * @param customTitle Custom title for the chart
   * @param indicators Technical indicators to include
   * @returns Chart URL
   */
  private async createTechnicalChart(
    historicalData: any[],
    symbol: string,
    customTitle?: string,
    indicators: any[] = []
  ): Promise<string> {
    // Create the chart
    return await this.plotlyService.createTechnicalChart(
      historicalData,
      customTitle || `${symbol} Technical Analysis`,
      indicators
    );
  }

  /**
   * Create a price comparison chart for multiple stocks
   * @param symbols Array of stock symbols
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @param customTitle Custom title for the chart
   * @returns Chart URL
   */
  public async createComparisonChart(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d',
    customTitle?: string
  ): Promise<string> {
    try {
      // Start the Plotly MCP server
      await this.plotlyService.startServer();

      // Get historical data for each symbol
      const seriesData = [];
      for (const symbol of symbols) {
        try {
          const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);

          // Normalize prices to percentage change from first day
          const firstPrice = historicalData[0].close;
          const normalizedPrices = historicalData.map((item: any) => ({
            date: item.date,
            value: ((item.close - firstPrice) / firstPrice) * 100
          }));

          seriesData.push({
            x: normalizedPrices.map((item: any) => item.date),
            y: normalizedPrices.map((item: any) => item.value),
            type: 'line',
            name: symbol
          });
        } catch (error) {
          console.error(`Error getting data for ${symbol}:`, error);
        }
      }

      // Create the chart
      return await this.plotlyService.createLineChart(
        seriesData,
        customTitle || `Price Comparison (% Change)`,
        'Date',
        'Percentage Change (%)'
      );
    } catch (error) {
      console.error('Error creating comparison chart:', error);
      throw error;
    } finally {
      // Stop the Plotly MCP server
      await this.plotlyService.stopServer();
    }
  }

  /**
   * Create a correlation heatmap for multiple stocks
   * @param symbols Array of stock symbols
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @param customTitle Custom title for the chart
   * @returns Chart URL
   */
  public async createCorrelationHeatmap(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d',
    customTitle?: string
  ): Promise<string> {
    try {
      // Start the Plotly MCP server
      await this.plotlyService.startServer();

      // Get historical data for each symbol
      const symbolData: Record<string, number[]> = {};
      const dates: string[] = [];

      for (const symbol of symbols) {
        try {
          const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);

          // Calculate daily returns
          const returns = [];
          for (let i = 1; i < historicalData.length; i++) {
            const prevClose = historicalData[i - 1].close;
            const currClose = historicalData[i].close;
            returns.push((currClose - prevClose) / prevClose);
          }

          symbolData[symbol] = returns;

          // Store dates for the first symbol
          if (dates.length === 0) {
            dates.push(...historicalData.slice(1).map((item: any) => item.date));
          }
        } catch (error) {
          console.error(`Error getting data for ${symbol}:`, error);
        }
      }

      // Calculate correlation matrix
      const correlationMatrix = [];
      for (const symbol1 of symbols) {
        const row = [];
        for (const symbol2 of symbols) {
          if (symbolData[symbol1] && symbolData[symbol2]) {
            const correlation = this.calculateCorrelation(symbolData[symbol1], symbolData[symbol2]);
            row.push(correlation);
          } else {
            row.push(0);
          }
        }
        correlationMatrix.push(row);
      }

      // Create the heatmap
      return await this.plotlyService.createHeatmap(
        correlationMatrix,
        customTitle || 'Correlation Heatmap',
        symbols,
        symbols
      );
    } catch (error) {
      console.error('Error creating correlation heatmap:', error);
      throw error;
    } finally {
      // Stop the Plotly MCP server
      await this.plotlyService.stopServer();
    }
  }

  /**
   * Calculate correlation between two arrays
   * @param array1 First array
   * @param array2 Second array
   * @returns Correlation coefficient
   */
  private calculateCorrelation(array1: number[], array2: number[]): number {
    // Make sure arrays are the same length
    const length = Math.min(array1.length, array2.length);

    // Calculate means
    const mean1 = array1.slice(0, length).reduce((sum, val) => sum + val, 0) / length;
    const mean2 = array2.slice(0, length).reduce((sum, val) => sum + val, 0) / length;

    // Calculate covariance and variances
    let covariance = 0;
    let variance1 = 0;
    let variance2 = 0;

    for (let i = 0; i < length; i++) {
      const diff1 = array1[i] - mean1;
      const diff2 = array2[i] - mean2;

      covariance += diff1 * diff2;
      variance1 += diff1 * diff1;
      variance2 += diff2 * diff2;
    }

    // Calculate correlation
    return covariance / (Math.sqrt(variance1) * Math.sqrt(variance2));
  }

  /**
   * Create a returns distribution histogram
   * @param symbol Stock symbol
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @param customTitle Custom title for the chart
   * @returns Chart URL
   */
  public async createReturnsHistogram(
    symbol: string,
    period: string = '1y',
    interval: string = '1d',
    customTitle?: string
  ): Promise<string> {
    try {
      // Start the Plotly MCP server
      await this.plotlyService.startServer();

      // Get historical data
      const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);

      // Calculate returns
      const returns = [];
      for (let i = 1; i < historicalData.length; i++) {
        const prevClose = historicalData[i - 1].close;
        const currClose = historicalData[i].close;
        returns.push((currClose - prevClose) / prevClose * 100); // Convert to percentage
      }

      // Create the histogram
      return await this.plotlyService.createHistogram(
        returns,
        customTitle || `${symbol} Returns Distribution`,
        'Returns (%)'
      );
    } catch (error) {
      console.error('Error creating returns histogram:', error);
      throw error;
    } finally {
      // Stop the Plotly MCP server
      await this.plotlyService.stopServer();
    }
  }

  /**
   * Create a backtest results visualization
   * @param backtestResults Backtest results data
   * @param customTitle Custom title for the chart
   * @returns Chart URL
   */
  public async createBacktestVisualization(
    backtestResults: any,
    customTitle?: string
  ): Promise<string> {
    try {
      // Start the Plotly MCP server
      await this.plotlyService.startServer();

      // Create the visualization
      return await this.plotlyService.createBacktestVisualization(
        backtestResults,
        customTitle || 'Backtest Results'
      );
    } catch (error) {
      console.error('Error creating backtest visualization:', error);
      throw error;
    } finally {
      // Stop the Plotly MCP server
      await this.plotlyService.stopServer();
    }
  }

  /**
   * Create a dashboard with multiple charts
   * @param charts Array of charts to include in the dashboard
   * @param customTitle Custom title for the dashboard
   * @returns Dashboard URL
   */
  public async createDashboard(
    charts: any[],
    customTitle?: string
  ): Promise<string> {
    try {
      // Start the Plotly MCP server
      await this.plotlyService.startServer();

      // Create the dashboard
      return await this.plotlyService.createDashboard(
        charts,
        customTitle || 'Trading Dashboard'
      );
    } catch (error) {
      console.error('Error creating dashboard:', error);
      throw error;
    } finally {
      // Stop the Plotly MCP server
      await this.plotlyService.stopServer();
    }
  }
}
