import { PlotlyService } from '../src/services/plotly-service';
import { VisualizationAgent } from '../src/trading/agents/visualization-agent';
import { ReAgent } from '../src/trading/reagent';

describe('Plotly Service Tests', () => {
  let plotlyService: PlotlyService;
  
  beforeAll(() => {
    // Initialize the Plotly service with caching disabled for tests
    plotlyService = new PlotlyService('http://localhost', 8004, false);
  });
  
  test('Create line chart', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              chart_url: 'http://example.com/chart/line123'
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Create line chart
    const data = [
      {
        x: ['2023-01-01', '2023-01-02', '2023-01-03'],
        y: [100, 105, 102],
        type: 'line',
        name: 'AAPL'
      }
    ];
    
    const chartUrl = await plotlyService.createLineChart(
      data,
      'AAPL Price History',
      'Date',
      'Price'
    );
    
    // Check if chart URL was returned
    expect(chartUrl).toBe('http://example.com/chart/line123');
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8004/call_tool',
      {
        name: 'create_line_chart',
        arguments: {
          data: JSON.stringify(data),
          title: 'AAPL Price History',
          x_label: 'Date',
          y_label: 'Price',
          options: '{}'
        }
      }
    );
  });
  
  test('Create candlestick chart', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              chart_url: 'http://example.com/chart/candlestick123'
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Create candlestick chart
    const data = {
      x: ['2023-01-01', '2023-01-02', '2023-01-03'],
      open: [100, 105, 102],
      high: [110, 108, 105],
      low: [98, 102, 100],
      close: [105, 102, 103],
      type: 'candlestick',
      name: 'AAPL'
    };
    
    const chartUrl = await plotlyService.createCandlestickChart(
      data,
      'AAPL Candlestick Chart'
    );
    
    // Check if chart URL was returned
    expect(chartUrl).toBe('http://example.com/chart/candlestick123');
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8004/call_tool',
      {
        name: 'create_candlestick_chart',
        arguments: {
          data: JSON.stringify(data),
          title: 'AAPL Candlestick Chart',
          options: '{}'
        }
      }
    );
  });
  
  test('Create technical chart', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              chart_url: 'http://example.com/chart/technical123'
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Create technical chart
    const data = [
      {
        date: '2023-01-01',
        open: 100,
        high: 110,
        low: 98,
        close: 105,
        volume: 1000000
      },
      {
        date: '2023-01-02',
        open: 105,
        high: 108,
        low: 102,
        close: 102,
        volume: 900000
      },
      {
        date: '2023-01-03',
        open: 102,
        high: 105,
        low: 100,
        close: 103,
        volume: 1200000
      }
    ];
    
    const indicators = [
      { name: 'RSI', parameters: { period: 14 } },
      { name: 'MACD', parameters: { fast: 12, slow: 26, signal: 9 } }
    ];
    
    const chartUrl = await plotlyService.createTechnicalChart(
      data,
      'AAPL Technical Analysis',
      indicators
    );
    
    // Check if chart URL was returned
    expect(chartUrl).toBe('http://example.com/chart/technical123');
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8004/call_tool',
      {
        name: 'create_technical_chart',
        arguments: {
          data: JSON.stringify(data),
          title: 'AAPL Technical Analysis',
          indicators: JSON.stringify(indicators),
          options: '{}'
        }
      }
    );
  });
});

describe('Visualization Agent Tests', () => {
  let visualizationAgent: VisualizationAgent;
  
  beforeAll(() => {
    // Initialize the Visualization agent
    visualizationAgent = new VisualizationAgent();
    
    // Mock the PlotlyService methods
    visualizationAgent['plotlyService'] = {
      startServer: jest.fn().mockResolvedValue(true),
      stopServer: jest.fn().mockResolvedValue(true),
      createLineChart: jest.fn().mockResolvedValue('http://example.com/chart/line123'),
      createCandlestickChart: jest.fn().mockResolvedValue('http://example.com/chart/candlestick123'),
      createTechnicalChart: jest.fn().mockResolvedValue('http://example.com/chart/technical123'),
      createComparisonChart: jest.fn().mockResolvedValue('http://example.com/chart/comparison123'),
      createCorrelationHeatmap: jest.fn().mockResolvedValue('http://example.com/chart/heatmap123'),
      createReturnsHistogram: jest.fn().mockResolvedValue('http://example.com/chart/histogram123'),
      createBacktestVisualization: jest.fn().mockResolvedValue('http://example.com/chart/backtest123'),
      createDashboard: jest.fn().mockResolvedValue('http://example.com/dashboard123')
    } as any;
    
    // Mock the YahooFinanceService methods
    visualizationAgent['yahooFinanceService'] = {
      getHistoricalData: jest.fn().mockResolvedValue([
        {
          date: '2023-01-01',
          open: 100,
          high: 110,
          low: 98,
          close: 105,
          volume: 1000000
        },
        {
          date: '2023-01-02',
          open: 105,
          high: 108,
          low: 102,
          close: 102,
          volume: 900000
        },
        {
          date: '2023-01-03',
          open: 102,
          high: 105,
          low: 100,
          close: 103,
          volume: 1200000
        }
      ])
    } as any;
  });
  
  test('Execute agent with line chart', async () => {
    // Execute the agent
    const result = await visualizationAgent.execute({
      symbol: 'AAPL',
      chartType: 'line',
      period: '1y',
      interval: '1d',
      title: 'AAPL Price History'
    });
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.chartType).toBe('line');
    expect(result.period).toBe('1y');
    expect(result.interval).toBe('1d');
    expect(result.chartUrl).toBe('http://example.com/chart/line123');
    
    // Check if service methods were called
    expect(visualizationAgent['plotlyService'].startServer).toHaveBeenCalled();
    expect(visualizationAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(visualizationAgent['plotlyService'].createLineChart).toHaveBeenCalled();
    expect(visualizationAgent['plotlyService'].stopServer).toHaveBeenCalled();
  });
  
  test('Execute agent with candlestick chart', async () => {
    // Execute the agent
    const result = await visualizationAgent.execute({
      symbol: 'AAPL',
      chartType: 'candlestick',
      period: '1y',
      interval: '1d',
      title: 'AAPL Candlestick Chart'
    });
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.chartType).toBe('candlestick');
    expect(result.chartUrl).toBe('http://example.com/chart/candlestick123');
    
    // Check if service methods were called
    expect(visualizationAgent['plotlyService'].createCandlestickChart).toHaveBeenCalled();
  });
  
  test('Create comparison chart', async () => {
    // Create comparison chart
    const result = await visualizationAgent.createComparisonChart(
      ['AAPL', 'MSFT'],
      '1y',
      '1d',
      'Price Comparison'
    );
    
    // Check if chart URL was returned
    expect(result).toBe('http://example.com/chart/comparison123');
    
    // Check if service methods were called
    expect(visualizationAgent['plotlyService'].startServer).toHaveBeenCalled();
    expect(visualizationAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(visualizationAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalledWith('MSFT', '1y', '1d');
    expect(visualizationAgent['plotlyService'].createLineChart).toHaveBeenCalled();
    expect(visualizationAgent['plotlyService'].stopServer).toHaveBeenCalled();
  });
  
  test('Create correlation heatmap', async () => {
    // Create correlation heatmap
    const result = await visualizationAgent.createCorrelationHeatmap(
      ['AAPL', 'MSFT', 'GOOGL'],
      '1y',
      '1d',
      'Correlation Heatmap'
    );
    
    // Check if chart URL was returned
    expect(result).toBe('http://example.com/chart/heatmap123');
    
    // Check if service methods were called
    expect(visualizationAgent['plotlyService'].createHeatmap).toHaveBeenCalled();
  });
});

describe('ReAgent Integration Tests', () => {
  let reagent: ReAgent;
  
  beforeAll(() => {
    // Initialize the ReAgent
    reagent = new ReAgent();
    
    // Mock the VisualizationAgent methods
    reagent['visualizationAgent'] = {
      execute: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        chartType: 'line',
        period: '1y',
        interval: '1d',
        chartUrl: 'http://example.com/chart/line123'
      }),
      createComparisonChart: jest.fn().mockResolvedValue('http://example.com/chart/comparison123'),
      createCorrelationHeatmap: jest.fn().mockResolvedValue('http://example.com/chart/heatmap123'),
      createReturnsHistogram: jest.fn().mockResolvedValue('http://example.com/chart/histogram123'),
      createBacktestVisualization: jest.fn().mockResolvedValue('http://example.com/chart/backtest123'),
      createDashboard: jest.fn().mockResolvedValue('http://example.com/dashboard123')
    } as any;
  });
  
  test('Create chart', async () => {
    // Create chart
    const result = await reagent.createChart('AAPL', 'line', '1y', '1d', 'AAPL Price History');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.chartType).toBe('line');
    expect(result.chartUrl).toBe('http://example.com/chart/line123');
    
    // Check if agent method was called
    expect(reagent['visualizationAgent'].execute).toHaveBeenCalledWith({
      symbol: 'AAPL',
      chartType: 'line',
      period: '1y',
      interval: '1d',
      title: 'AAPL Price History',
      indicators: []
    });
  });
  
  test('Create comparison chart', async () => {
    // Create comparison chart
    const result = await reagent.createComparisonChart(['AAPL', 'MSFT'], '1y', '1d', 'Price Comparison');
    
    // Check if chart URL was returned
    expect(result).toBe('http://example.com/chart/comparison123');
    
    // Check if agent method was called
    expect(reagent['visualizationAgent'].createComparisonChart).toHaveBeenCalledWith(
      ['AAPL', 'MSFT'],
      '1y',
      '1d',
      'Price Comparison'
    );
  });
  
  test('Create correlation heatmap', async () => {
    // Create correlation heatmap
    const result = await reagent.createCorrelationHeatmap(['AAPL', 'MSFT', 'GOOGL'], '1y', '1d', 'Correlation Heatmap');
    
    // Check if chart URL was returned
    expect(result).toBe('http://example.com/chart/heatmap123');
    
    // Check if agent method was called
    expect(reagent['visualizationAgent'].createCorrelationHeatmap).toHaveBeenCalledWith(
      ['AAPL', 'MSFT', 'GOOGL'],
      '1y',
      '1d',
      'Correlation Heatmap'
    );
  });
  
  test('Create returns histogram', async () => {
    // Create returns histogram
    const result = await reagent.createReturnsHistogram('AAPL', '1y', '1d', 'Returns Histogram');
    
    // Check if chart URL was returned
    expect(result).toBe('http://example.com/chart/histogram123');
    
    // Check if agent method was called
    expect(reagent['visualizationAgent'].createReturnsHistogram).toHaveBeenCalledWith(
      'AAPL',
      '1y',
      '1d',
      'Returns Histogram'
    );
  });
  
  test('Create backtest visualization', async () => {
    // Create backtest visualization
    const backtestResults = {
      totalReturn: 25.5,
      annualReturn: 15.2,
      sharpeRatio: 1.2,
      maxDrawdown: 12.3,
      winRate: 65.0,
      trades: [
        { date: '2023-01-01', type: 'buy', price: 100, shares: 10 },
        { date: '2023-01-15', type: 'sell', price: 110, shares: 10 }
      ]
    };
    
    const result = await reagent.createBacktestVisualization(backtestResults, 'Backtest Results');
    
    // Check if chart URL was returned
    expect(result).toBe('http://example.com/chart/backtest123');
    
    // Check if agent method was called
    expect(reagent['visualizationAgent'].createBacktestVisualization).toHaveBeenCalledWith(
      backtestResults,
      'Backtest Results'
    );
  });
  
  test('Create dashboard', async () => {
    // Create dashboard
    const charts = [
      { id: 'chart1', url: 'http://example.com/chart/line123' },
      { id: 'chart2', url: 'http://example.com/chart/candlestick123' }
    ];
    
    const result = await reagent.createDashboard(charts, 'Trading Dashboard');
    
    // Check if dashboard URL was returned
    expect(result).toBe('http://example.com/dashboard123');
    
    // Check if agent method was called
    expect(reagent['visualizationAgent'].createDashboard).toHaveBeenCalledWith(
      charts,
      'Trading Dashboard'
    );
  });
});
