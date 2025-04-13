import { HuggingfaceService } from '../src/services/huggingface-service';
import { MLAgent } from '../src/trading/agents/ml-agent';
import { ReAgent } from '../src/trading/reagent';

describe('Huggingface Service Tests', () => {
  let huggingfaceService: HuggingfaceService;
  
  beforeAll(() => {
    // Initialize the Huggingface service with caching disabled for tests
    huggingfaceService = new HuggingfaceService('http://localhost', 8005, false);
  });
  
  test('Analyze sentiment', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              label: 'POSITIVE',
              score: 0.9876
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Analyze sentiment
    const result = await huggingfaceService.analyzeSentiment(
      'This is a great product, I love it!',
      'distilbert-base-uncased-finetuned-sst-2-english'
    );
    
    // Check if sentiment analysis result was returned
    expect(result).toBeDefined();
    expect(result.label).toBe('POSITIVE');
    expect(result.score).toBe(0.9876);
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8005/call_tool',
      {
        name: 'sentiment_analysis',
        arguments: {
          text: 'This is a great product, I love it!',
          model: 'distilbert-base-uncased-finetuned-sst-2-english',
          options: '{}'
        }
      }
    );
  });
  
  test('Forecast time series', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              forecast: [
                { ds: '2023-01-01', yhat: 100, yhat_lower: 95, yhat_upper: 105 },
                { ds: '2023-01-02', yhat: 102, yhat_lower: 97, yhat_upper: 107 },
                { ds: '2023-01-03', yhat: 104, yhat_lower: 99, yhat_upper: 109 }
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
    
    // Forecast time series
    const data = [
      { ds: '2022-12-29', y: 95 },
      { ds: '2022-12-30', y: 97 },
      { ds: '2022-12-31', y: 99 }
    ];
    
    const result = await huggingfaceService.forecastTimeSeries(
      data,
      'facebook/prophet',
      { periods: 3, frequency: 'D' }
    );
    
    // Check if forecast result was returned
    expect(result).toBeDefined();
    expect(result.forecast).toBeDefined();
    expect(result.forecast.length).toBe(3);
    expect(result.forecast[0].ds).toBe('2023-01-01');
    expect(result.forecast[0].yhat).toBe(100);
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8005/call_tool',
      {
        name: 'time_series_forecasting',
        arguments: {
          data: JSON.stringify(data),
          model: 'facebook/prophet',
          options: JSON.stringify({ periods: 3, frequency: 'D' })
        }
      }
    );
  });
  
  test('Detect anomalies', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              anomalies: [
                { ds: '2022-12-30', expected: 97, actual: 110, deviation: 13.4 }
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
    
    // Detect anomalies
    const data = [
      { ds: '2022-12-29', y: 95 },
      { ds: '2022-12-30', y: 110 },
      { ds: '2022-12-31', y: 99 }
    ];
    
    const result = await huggingfaceService.detectAnomalies(
      data,
      'facebook/prophet'
    );
    
    // Check if anomaly detection result was returned
    expect(result).toBeDefined();
    expect(result.anomalies).toBeDefined();
    expect(result.anomalies.length).toBe(1);
    expect(result.anomalies[0].ds).toBe('2022-12-30');
    expect(result.anomalies[0].actual).toBe(110);
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8005/call_tool',
      {
        name: 'anomaly_detection',
        arguments: {
          data: JSON.stringify(data),
          model: 'facebook/prophet',
          options: '{}'
        }
      }
    );
  });
});

describe('ML Agent Tests', () => {
  let mlAgent: MLAgent;
  
  beforeAll(() => {
    // Initialize the ML agent
    mlAgent = new MLAgent();
    
    // Mock the HuggingfaceService methods
    mlAgent['huggingfaceService'] = {
      startServer: jest.fn().mockResolvedValue(true),
      stopServer: jest.fn().mockResolvedValue(true),
      analyzeSentiment: jest.fn().mockResolvedValue({
        label: 'POSITIVE',
        score: 0.9876
      }),
      classifyText: jest.fn().mockResolvedValue({
        label: 'BUSINESS',
        score: 0.8765
      }),
      generateText: jest.fn().mockResolvedValue({
        generated_text: 'This is a generated text.'
      }),
      summarizeText: jest.fn().mockResolvedValue({
        summary: 'This is a summary.'
      }),
      extractEntities: jest.fn().mockResolvedValue([
        { entity: 'PERSON', word: 'John Doe', score: 0.9876 },
        { entity: 'ORG', word: 'Acme Corp', score: 0.8765 }
      ]),
      answerQuestion: jest.fn().mockResolvedValue({
        answer: 'This is the answer.',
        score: 0.9876
      }),
      forecastTimeSeries: jest.fn().mockResolvedValue({
        forecast: [
          { ds: '2023-01-01', yhat: 100, yhat_lower: 95, yhat_upper: 105 },
          { ds: '2023-01-02', yhat: 102, yhat_lower: 97, yhat_upper: 107 },
          { ds: '2023-01-03', yhat: 104, yhat_lower: 99, yhat_upper: 109 }
        ]
      }),
      detectAnomalies: jest.fn().mockResolvedValue({
        anomalies: [
          { ds: '2022-12-30', expected: 97, actual: 110, deviation: 13.4 }
        ]
      }),
      clusterData: jest.fn().mockResolvedValue({
        clusters: {
          0: [{ symbol: 'AAPL' }, { symbol: 'MSFT' }],
          1: [{ symbol: 'GOOGL' }, { symbol: 'META' }],
          2: [{ symbol: 'AMZN' }, { symbol: 'NFLX' }]
        }
      })
    } as any;
    
    // Mock the YahooFinanceService methods
    mlAgent['yahooFinanceService'] = {
      getMarketNews: jest.fn().mockResolvedValue([
        {
          title: 'Stock Market News 1',
          summary: 'This is a summary of the first news article.',
          publisher: 'News Corp',
          link: 'https://example.com/news1',
          publishedAt: '2023-01-01'
        },
        {
          title: 'Stock Market News 2',
          summary: 'This is a summary of the second news article.',
          publisher: 'News Corp',
          link: 'https://example.com/news2',
          publishedAt: '2023-01-02'
        }
      ]),
      getHistoricalData: jest.fn().mockResolvedValue([
        {
          date: '2022-12-29',
          open: 95,
          high: 98,
          low: 94,
          close: 95,
          volume: 1000000
        },
        {
          date: '2022-12-30',
          open: 97,
          high: 100,
          low: 96,
          close: 97,
          volume: 1100000
        },
        {
          date: '2022-12-31',
          open: 99,
          high: 102,
          low: 98,
          close: 99,
          volume: 1200000
        }
      ])
    } as any;
  });
  
  test('Execute agent with sentiment analysis', async () => {
    // Execute the agent
    const result = await mlAgent.execute({
      task: 'sentiment_analysis',
      data: 'This is a great product, I love it!',
      model: 'distilbert-base-uncased-finetuned-sst-2-english'
    });
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.task).toBe('sentiment_analysis');
    expect(result.model).toBe('distilbert-base-uncased-finetuned-sst-2-english');
    expect(result.result).toBeDefined();
    expect(result.result.label).toBe('POSITIVE');
    expect(result.result.score).toBe(0.9876);
    
    // Check if service methods were called
    expect(mlAgent['huggingfaceService'].startServer).toHaveBeenCalled();
    expect(mlAgent['huggingfaceService'].analyzeSentiment).toHaveBeenCalledWith(
      'This is a great product, I love it!',
      'distilbert-base-uncased-finetuned-sst-2-english',
      undefined
    );
    expect(mlAgent['huggingfaceService'].stopServer).toHaveBeenCalled();
  });
  
  test('Analyze market news sentiment', async () => {
    // Analyze market news sentiment
    const result = await mlAgent.analyzeMarketNewsSentiment('AAPL', 2);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.aggregateSentiment).toBeDefined();
    expect(result.articles).toBeDefined();
    expect(result.articles.length).toBe(2);
    
    // Check if service methods were called
    expect(mlAgent['huggingfaceService'].startServer).toHaveBeenCalled();
    expect(mlAgent['yahooFinanceService'].getMarketNews).toHaveBeenCalledWith('AAPL', 2);
    expect(mlAgent['huggingfaceService'].analyzeSentiment).toHaveBeenCalled();
    expect(mlAgent['huggingfaceService'].stopServer).toHaveBeenCalled();
  });
  
  test('Forecast stock prices', async () => {
    // Forecast stock prices
    const result = await mlAgent.forecastStockPrices('AAPL', '1y', '1d', 30);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.historicalData).toBeDefined();
    expect(result.forecast).toBeDefined();
    expect(result.forecast.forecast).toBeDefined();
    expect(result.forecast.forecast.length).toBe(3);
    
    // Check if service methods were called
    expect(mlAgent['huggingfaceService'].startServer).toHaveBeenCalled();
    expect(mlAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(mlAgent['huggingfaceService'].forecastTimeSeries).toHaveBeenCalled();
    expect(mlAgent['huggingfaceService'].stopServer).toHaveBeenCalled();
  });
  
  test('Detect stock anomalies', async () => {
    // Detect stock anomalies
    const result = await mlAgent.detectStockAnomalies('AAPL', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.historicalData).toBeDefined();
    expect(result.anomalies).toBeDefined();
    expect(result.anomalies.anomalies).toBeDefined();
    expect(result.anomalies.anomalies.length).toBe(1);
    
    // Check if service methods were called
    expect(mlAgent['huggingfaceService'].startServer).toHaveBeenCalled();
    expect(mlAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(mlAgent['huggingfaceService'].detectAnomalies).toHaveBeenCalled();
    expect(mlAgent['huggingfaceService'].stopServer).toHaveBeenCalled();
  });
  
  test('Cluster stocks', async () => {
    // Cluster stocks
    const result = await mlAgent.clusterStocks(['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX'], '1y', '1d', 3);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbols).toEqual(['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX']);
    expect(result.clusters).toBeDefined();
    expect(result.clusters.clusters).toBeDefined();
    expect(Object.keys(result.clusters.clusters).length).toBe(3);
    
    // Check if service methods were called
    expect(mlAgent['huggingfaceService'].startServer).toHaveBeenCalled();
    expect(mlAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalled();
    expect(mlAgent['huggingfaceService'].clusterData).toHaveBeenCalled();
    expect(mlAgent['huggingfaceService'].stopServer).toHaveBeenCalled();
  });
});

describe('ReAgent Integration Tests', () => {
  let reagent: ReAgent;
  
  beforeAll(() => {
    // Initialize the ReAgent
    reagent = new ReAgent();
    
    // Mock the MLAgent methods
    reagent['mlAgent'] = {
      analyzeSentiment: jest.fn().mockResolvedValue({
        label: 'POSITIVE',
        score: 0.9876
      }),
      classifyText: jest.fn().mockResolvedValue({
        label: 'BUSINESS',
        score: 0.8765
      }),
      generateText: jest.fn().mockResolvedValue({
        generated_text: 'This is a generated text.'
      }),
      summarizeText: jest.fn().mockResolvedValue({
        summary: 'This is a summary.'
      }),
      extractEntities: jest.fn().mockResolvedValue([
        { entity: 'PERSON', word: 'John Doe', score: 0.9876 },
        { entity: 'ORG', word: 'Acme Corp', score: 0.8765 }
      ]),
      answerQuestion: jest.fn().mockResolvedValue({
        answer: 'This is the answer.',
        score: 0.9876
      }),
      analyzeMarketNewsSentiment: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        aggregateSentiment: {
          positive: 0.75,
          negative: 0.25
        },
        articles: [
          {
            article: {
              title: 'Stock Market News 1',
              publisher: 'News Corp',
              publishedAt: '2023-01-01'
            },
            sentiment: {
              label: 'POSITIVE',
              score: 0.9876
            }
          },
          {
            article: {
              title: 'Stock Market News 2',
              publisher: 'News Corp',
              publishedAt: '2023-01-02'
            },
            sentiment: {
              label: 'NEGATIVE',
              score: 0.8765
            }
          }
        ]
      }),
      forecastStockPrices: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        historicalData: [
          { ds: '2022-12-29', y: 95 },
          { ds: '2022-12-30', y: 97 },
          { ds: '2022-12-31', y: 99 }
        ],
        forecast: {
          forecast: [
            { ds: '2023-01-01', yhat: 100, yhat_lower: 95, yhat_upper: 105 },
            { ds: '2023-01-02', yhat: 102, yhat_lower: 97, yhat_upper: 107 },
            { ds: '2023-01-03', yhat: 104, yhat_lower: 99, yhat_upper: 109 }
          ]
        }
      }),
      detectStockAnomalies: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        historicalData: [
          { ds: '2022-12-29', y: 95 },
          { ds: '2022-12-30', y: 110 },
          { ds: '2022-12-31', y: 99 }
        ],
        anomalies: {
          anomalies: [
            { ds: '2022-12-30', expected: 97, actual: 110, deviation: 13.4 }
          ]
        }
      }),
      clusterStocks: jest.fn().mockResolvedValue({
        symbols: ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX'],
        clusters: {
          clusters: {
            0: [{ symbol: 'AAPL' }, { symbol: 'MSFT' }],
            1: [{ symbol: 'GOOGL' }, { symbol: 'META' }],
            2: [{ symbol: 'AMZN' }, { symbol: 'NFLX' }]
          }
        }
      })
    } as any;
  });
  
  test('Analyze sentiment', async () => {
    // Analyze sentiment
    const result = await reagent.analyzeSentiment('This is a great product, I love it!');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.label).toBe('POSITIVE');
    expect(result.score).toBe(0.9876);
    
    // Check if agent method was called
    expect(reagent['mlAgent'].analyzeSentiment).toHaveBeenCalledWith(
      'This is a great product, I love it!',
      undefined,
      undefined
    );
  });
  
  test('Analyze market news sentiment', async () => {
    // Analyze market news sentiment
    const result = await reagent.analyzeMarketNewsSentiment('AAPL', 2);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.aggregateSentiment).toBeDefined();
    expect(result.articles).toBeDefined();
    expect(result.articles.length).toBe(2);
    
    // Check if agent method was called
    expect(reagent['mlAgent'].analyzeMarketNewsSentiment).toHaveBeenCalledWith('AAPL', 2, undefined);
  });
  
  test('Forecast stock prices', async () => {
    // Forecast stock prices
    const result = await reagent.forecastStockPrices('AAPL', '1y', '1d', 30);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.historicalData).toBeDefined();
    expect(result.forecast).toBeDefined();
    expect(result.forecast.forecast).toBeDefined();
    expect(result.forecast.forecast.length).toBe(3);
    
    // Check if agent method was called
    expect(reagent['mlAgent'].forecastStockPrices).toHaveBeenCalledWith('AAPL', '1y', '1d', 30, undefined);
  });
  
  test('Detect stock anomalies', async () => {
    // Detect stock anomalies
    const result = await reagent.detectStockAnomalies('AAPL', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.historicalData).toBeDefined();
    expect(result.anomalies).toBeDefined();
    expect(result.anomalies.anomalies).toBeDefined();
    expect(result.anomalies.anomalies.length).toBe(1);
    
    // Check if agent method was called
    expect(reagent['mlAgent'].detectStockAnomalies).toHaveBeenCalledWith('AAPL', '1y', '1d', undefined);
  });
  
  test('Cluster stocks', async () => {
    // Cluster stocks
    const result = await reagent.clusterStocks(['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX'], '1y', '1d', 3);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbols).toEqual(['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX']);
    expect(result.clusters).toBeDefined();
    expect(result.clusters.clusters).toBeDefined();
    expect(Object.keys(result.clusters.clusters)).toHaveLength(3);
    
    // Check if agent method was called
    expect(reagent['mlAgent'].clusterStocks).toHaveBeenCalledWith(
      ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX'],
      '1y',
      '1d',
      3,
      undefined
    );
  });
});
