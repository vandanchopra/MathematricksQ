import { PandasAIService } from '../src/services/pandas-ai-service';
import { DataAnalysisAgent } from '../src/trading/agents/data-analysis-agent';
import { ReAgent } from '../src/trading/reagent';

describe('Pandas AI Service Tests', () => {
  let pandasAIService: PandasAIService;
  
  beforeAll(() => {
    // Initialize the Pandas AI service with caching disabled for tests
    pandasAIService = new PandasAIService('http://localhost', 8003, false);
  });
  
  test('Load financial data', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              dataframe_id: 'df_123456'
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Load financial data
    const dataframeId = await pandasAIService.loadFinancialData('AAPL', '1y', '1d');
    
    // Check if dataframe ID was returned
    expect(dataframeId).toBe('df_123456');
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8003/call_tool',
      {
        name: 'load_financial_data',
        arguments: {
          symbol: 'AAPL',
          period: '1y',
          interval: '1d'
        }
      }
    );
  });
  
  test('Analyze DataFrame', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              analysis: 'This is the analysis result',
              statistics: {
                mean: 150.0,
                std: 10.0,
                min: 130.0,
                max: 170.0
              }
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Analyze DataFrame
    const result = await pandasAIService.analyzeDataFrame('df_123456', 'Analyze the trend');
    
    // Check if analysis result was returned
    expect(result).toBeDefined();
    expect(result.analysis).toBe('This is the analysis result');
    expect(result.statistics).toBeDefined();
    expect(result.statistics.mean).toBe(150.0);
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8003/call_tool',
      {
        name: 'analyze_dataframe',
        arguments: {
          dataframe_id: 'df_123456',
          query: 'Analyze the trend'
        }
      }
    );
  });
  
  test('Generate trading strategy', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              name: 'Momentum Strategy',
              description: 'A momentum-based trading strategy',
              entryConditions: ['Condition 1', 'Condition 2'],
              exitConditions: ['Condition 3', 'Condition 4'],
              indicators: [
                { name: 'RSI', parameters: { period: 14 } },
                { name: 'MACD', parameters: { fast: 12, slow: 26, signal: 9 } }
              ]
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Generate trading strategy
    const strategy = await pandasAIService.generateTradingStrategy('df_123456', 'momentum');
    
    // Check if strategy was returned
    expect(strategy).toBeDefined();
    expect(strategy.name).toBe('Momentum Strategy');
    expect(strategy.description).toBe('A momentum-based trading strategy');
    expect(strategy.entryConditions).toEqual(['Condition 1', 'Condition 2']);
    expect(strategy.exitConditions).toEqual(['Condition 3', 'Condition 4']);
    expect(strategy.indicators).toHaveLength(2);
    expect(strategy.indicators[0].name).toBe('RSI');
    expect(strategy.indicators[0].parameters.period).toBe(14);
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8003/call_tool',
      {
        name: 'generate_trading_strategy',
        arguments: {
          dataframe_id: 'df_123456',
          strategy_type: 'momentum'
        }
      }
    );
  });
});

describe('Data Analysis Agent Tests', () => {
  let dataAnalysisAgent: DataAnalysisAgent;
  
  beforeAll(() => {
    // Initialize the Data Analysis agent
    dataAnalysisAgent = new DataAnalysisAgent();
    
    // Mock the PandasAIService methods
    dataAnalysisAgent['pandasAIService'] = {
      startServer: jest.fn().mockResolvedValue(true),
      stopServer: jest.fn().mockResolvedValue(true),
      loadFinancialData: jest.fn().mockResolvedValue('df_123456'),
      getDataFrameInfo: jest.fn().mockResolvedValue({
        columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'],
        shape: [252, 6]
      }),
      getDataFrameStats: jest.fn().mockResolvedValue({
        Close: {
          mean: 150.0,
          std: 10.0,
          min: 130.0,
          max: 170.0
        }
      }),
      analyzeDataFrame: jest.fn().mockResolvedValue({
        analysis: 'This is the analysis result'
      }),
      generateTradingStrategy: jest.fn().mockResolvedValue({
        name: 'Momentum Strategy',
        description: 'A momentum-based trading strategy',
        entryConditions: ['Condition 1', 'Condition 2'],
        exitConditions: ['Condition 3', 'Condition 4'],
        indicators: [
          { name: 'RSI', parameters: { period: 14 } },
          { name: 'MACD', parameters: { fast: 12, slow: 26, signal: 9 } }
        ]
      }),
      backtestStrategy: jest.fn().mockResolvedValue({
        totalReturn: 25.5,
        annualReturn: 15.2,
        sharpeRatio: 1.2,
        maxDrawdown: 12.3,
        winRate: 65.0
      })
    } as any;
    
    // Mock the YahooFinanceService methods
    dataAnalysisAgent['yahooFinanceService'] = {
      getStockQuote: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        regularMarketPrice: 150.0,
        regularMarketChange: 2.5,
        regularMarketChangePercent: 1.67
      }),
      getCompanyInfo: jest.fn().mockResolvedValue({
        longName: 'Apple Inc.',
        industry: 'Consumer Electronics',
        sector: 'Technology'
      })
    } as any;
  });
  
  test('Analyze financial data', async () => {
    // Analyze financial data
    const result = await dataAnalysisAgent.analyzeFinancialData('AAPL', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.period).toBe('1y');
    expect(result.interval).toBe('1d');
    expect(result.dataframeId).toBe('df_123456');
    expect(result.dataframeInfo).toBeDefined();
    expect(result.dataframeStats).toBeDefined();
    expect(result.stockQuote).toBeDefined();
    expect(result.companyInfo).toBeDefined();
    
    // Check if service methods were called
    expect(dataAnalysisAgent['pandasAIService'].startServer).toHaveBeenCalled();
    expect(dataAnalysisAgent['pandasAIService'].loadFinancialData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(dataAnalysisAgent['pandasAIService'].getDataFrameInfo).toHaveBeenCalledWith('df_123456');
    expect(dataAnalysisAgent['pandasAIService'].getDataFrameStats).toHaveBeenCalledWith('df_123456');
    expect(dataAnalysisAgent['yahooFinanceService'].getStockQuote).toHaveBeenCalledWith('AAPL');
    expect(dataAnalysisAgent['yahooFinanceService'].getCompanyInfo).toHaveBeenCalledWith('AAPL');
    expect(dataAnalysisAgent['pandasAIService'].stopServer).toHaveBeenCalled();
  });
  
  test('Run analysis query', async () => {
    // Run analysis query
    const result = await dataAnalysisAgent.runAnalysisQuery('AAPL', 'Analyze the trend', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.query).toBe('Analyze the trend');
    expect(result.analysisResult).toBeDefined();
    expect(result.analysisResult.analysis).toBe('This is the analysis result');
    
    // Check if service methods were called
    expect(dataAnalysisAgent['pandasAIService'].startServer).toHaveBeenCalled();
    expect(dataAnalysisAgent['pandasAIService'].loadFinancialData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(dataAnalysisAgent['pandasAIService'].analyzeDataFrame).toHaveBeenCalledWith('df_123456', 'Analyze the trend');
    expect(dataAnalysisAgent['pandasAIService'].stopServer).toHaveBeenCalled();
  });
  
  test('Generate trading strategy', async () => {
    // Generate trading strategy
    const result = await dataAnalysisAgent.generateTradingStrategy('AAPL', 'momentum', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.strategyType).toBe('momentum');
    expect(result.strategy).toBeDefined();
    expect(result.strategy.name).toBe('Momentum Strategy');
    expect(result.backtestResults).toBeDefined();
    expect(result.backtestResults.totalReturn).toBe(25.5);
    
    // Check if service methods were called
    expect(dataAnalysisAgent['pandasAIService'].startServer).toHaveBeenCalled();
    expect(dataAnalysisAgent['pandasAIService'].loadFinancialData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(dataAnalysisAgent['pandasAIService'].generateTradingStrategy).toHaveBeenCalledWith('df_123456', 'momentum');
    expect(dataAnalysisAgent['pandasAIService'].backtestStrategy).toHaveBeenCalled();
    expect(dataAnalysisAgent['pandasAIService'].stopServer).toHaveBeenCalled();
  });
});

describe('ReAgent Integration Tests', () => {
  let reagent: ReAgent;
  
  beforeAll(() => {
    // Initialize the ReAgent
    reagent = new ReAgent();
    
    // Mock the DataAnalysisAgent methods
    reagent['dataAnalysisAgent'] = {
      analyzeFinancialData: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        period: '1y',
        interval: '1d',
        dataframeId: 'df_123456',
        dataframeInfo: {
          columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'],
          shape: [252, 6]
        },
        dataframeStats: {
          Close: {
            mean: 150.0,
            std: 10.0,
            min: 130.0,
            max: 170.0
          }
        },
        stockQuote: {
          symbol: 'AAPL',
          regularMarketPrice: 150.0,
          regularMarketChange: 2.5,
          regularMarketChangePercent: 1.67
        }
      }),
      runAnalysisQuery: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        query: 'Analyze the trend',
        analysisResult: {
          analysis: 'This is the analysis result'
        }
      }),
      generateTradingStrategy: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        strategyType: 'momentum',
        strategy: {
          name: 'Momentum Strategy',
          description: 'A momentum-based trading strategy',
          entryConditions: ['Condition 1', 'Condition 2'],
          exitConditions: ['Condition 3', 'Condition 4'],
          indicators: [
            { name: 'RSI', parameters: { period: 14 } },
            { name: 'MACD', parameters: { fast: 12, slow: 26, signal: 9 } }
          ]
        },
        backtestResults: {
          totalReturn: 25.5,
          annualReturn: 15.2,
          sharpeRatio: 1.2,
          maxDrawdown: 12.3,
          winRate: 65.0
        }
      }),
      compareSymbols: jest.fn().mockResolvedValue({
        symbols: ['AAPL', 'MSFT'],
        period: '1y',
        interval: '1d',
        individualResults: {
          AAPL: {
            dataframeId: 'df_123456',
            dataframeStats: {
              Close: {
                mean: 150.0,
                std: 10.0,
                min: 130.0,
                max: 170.0
              }
            },
            stockQuote: {
              regularMarketPrice: 150.0,
              regularMarketChange: 2.5,
              regularMarketChangePercent: 1.67
            }
          },
          MSFT: {
            dataframeId: 'df_789012',
            dataframeStats: {
              Close: {
                mean: 250.0,
                std: 15.0,
                min: 220.0,
                max: 280.0
              }
            },
            stockQuote: {
              regularMarketPrice: 250.0,
              regularMarketChange: 3.5,
              regularMarketChangePercent: 1.42
            }
          }
        },
        comparisonAnalysis: 'This is the comparison analysis'
      })
    } as any;
  });
  
  test('Analyze financial data', async () => {
    // Analyze financial data
    const result = await reagent.analyzeFinancialData('AAPL', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.dataframeInfo).toBeDefined();
    expect(result.dataframeStats).toBeDefined();
    expect(result.stockQuote).toBeDefined();
    
    // Check if agent method was called
    expect(reagent['dataAnalysisAgent'].analyzeFinancialData).toHaveBeenCalledWith('AAPL', '1y', '1d');
  });
  
  test('Run analysis query', async () => {
    // Run analysis query
    const result = await reagent.runAnalysisQuery('AAPL', 'Analyze the trend', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.query).toBe('Analyze the trend');
    expect(result.analysisResult).toBeDefined();
    
    // Check if agent method was called
    expect(reagent['dataAnalysisAgent'].runAnalysisQuery).toHaveBeenCalledWith('AAPL', 'Analyze the trend', '1y', '1d');
  });
  
  test('Generate data-driven strategy', async () => {
    // Generate data-driven strategy
    const result = await reagent.generateDataDrivenStrategy('AAPL', 'momentum', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.strategyType).toBe('momentum');
    expect(result.strategy).toBeDefined();
    expect(result.backtestResults).toBeDefined();
    
    // Check if agent method was called
    expect(reagent['dataAnalysisAgent'].generateTradingStrategy).toHaveBeenCalledWith('AAPL', 'momentum', '1y', '1d');
  });
  
  test('Compare symbols', async () => {
    // Compare symbols
    const result = await reagent.compareSymbols(['AAPL', 'MSFT'], '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbols).toEqual(['AAPL', 'MSFT']);
    expect(result.individualResults).toBeDefined();
    expect(result.individualResults.AAPL).toBeDefined();
    expect(result.individualResults.MSFT).toBeDefined();
    expect(result.comparisonAnalysis).toBeDefined();
    
    // Check if agent method was called
    expect(reagent['dataAnalysisAgent'].compareSymbols).toHaveBeenCalledWith(['AAPL', 'MSFT'], '1y', '1d');
  });
});
