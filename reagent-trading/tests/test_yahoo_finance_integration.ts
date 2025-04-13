import { YahooFinanceService } from '../src/services/yahoo-finance-service';
import { YahooFinanceAgent } from '../src/trading/agents/yahoo-finance-agent';
import { ReAgent } from '../src/trading/reagent';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

describe('Yahoo Finance Service Tests', () => {
  let yahooFinanceService: YahooFinanceService;
  
  beforeAll(() => {
    // Initialize the Yahoo Finance service with caching disabled for tests
    yahooFinanceService = new YahooFinanceService('http://localhost', 8001, false);
  });
  
  test('Get stock quote', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              symbol: 'AAPL',
              regularMarketPrice: 150.0,
              regularMarketChange: 2.5,
              regularMarketChangePercent: 1.67,
              regularMarketPreviousClose: 147.5,
              regularMarketOpen: 148.0,
              regularMarketDayLow: 147.8,
              regularMarketDayHigh: 151.2,
              regularMarketVolume: 75000000
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Get stock quote
    const quote = await yahooFinanceService.getStockQuote('AAPL');
    
    // Check if quote was retrieved
    expect(quote).toBeDefined();
    expect(quote.symbol).toBe('AAPL');
    expect(quote.regularMarketPrice).toBe(150.0);
    expect(quote.regularMarketChange).toBe(2.5);
    expect(quote.regularMarketChangePercent).toBe(1.67);
  });
  
  test('Get historical data', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify([
              {
                date: '2023-01-01',
                open: 140.0,
                high: 145.0,
                low: 139.0,
                close: 142.5,
                volume: 65000000
              },
              {
                date: '2023-01-02',
                open: 142.5,
                high: 148.0,
                low: 142.0,
                close: 147.0,
                volume: 70000000
              }
            ])
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Get historical data
    const data = await yahooFinanceService.getHistoricalData('AAPL', '1mo', '1d');
    
    // Check if data was retrieved
    expect(data).toBeDefined();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBe(2);
    expect(data[0].date).toBe('2023-01-01');
    expect(data[0].open).toBe(140.0);
    expect(data[1].date).toBe('2023-01-02');
    expect(data[1].close).toBe(147.0);
  });
});

describe('Yahoo Finance Agent Tests', () => {
  let yahooFinanceAgent: YahooFinanceAgent;
  
  beforeAll(() => {
    // Initialize the Yahoo Finance agent
    yahooFinanceAgent = new YahooFinanceAgent();
    
    // Mock the YahooFinanceService methods
    yahooFinanceAgent['yahooFinanceService'] = {
      getStockQuote: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        regularMarketPrice: 150.0
      }),
      getHistoricalData: jest.fn().mockResolvedValue([
        {
          date: '2023-01-01',
          open: 140.0,
          close: 142.5
        }
      ]),
      getCompanyInfo: jest.fn().mockResolvedValue({
        longName: 'Apple Inc.',
        symbol: 'AAPL',
        industry: 'Consumer Electronics'
      }),
      getMarketNews: jest.fn().mockResolvedValue([
        {
          title: 'Market News 1',
          published: '2023-01-01'
        }
      ]),
      search: jest.fn().mockResolvedValue([
        {
          shortname: 'Apple Inc.',
          symbol: 'AAPL'
        }
      ])
    } as any;
  });
  
  test('Get stock quote', async () => {
    // Get stock quote
    const quote = await yahooFinanceAgent.getStockQuote('AAPL');
    
    // Check if quote was retrieved
    expect(quote).toBeDefined();
    expect(quote.symbol).toBe('AAPL');
    expect(quote.regularMarketPrice).toBe(150.0);
    
    // Check if service method was called
    expect(yahooFinanceAgent['yahooFinanceService'].getStockQuote).toHaveBeenCalledWith('AAPL');
  });
  
  test('Get historical data', async () => {
    // Get historical data
    const data = await yahooFinanceAgent.getHistoricalData('AAPL', '1mo', '1d');
    
    // Check if data was retrieved
    expect(data).toBeDefined();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBe(1);
    expect(data[0].date).toBe('2023-01-01');
    expect(data[0].open).toBe(140.0);
    
    // Check if service method was called
    expect(yahooFinanceAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalledWith('AAPL', '1mo', '1d');
  });
});

describe('ReAgent Integration Tests', () => {
  let reagent: ReAgent;
  
  beforeAll(() => {
    // Initialize the ReAgent
    reagent = new ReAgent();
    
    // Mock the YahooFinanceAgent methods
    reagent['yahooFinanceAgent'] = {
      getStockQuote: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        regularMarketPrice: 150.0
      }),
      getHistoricalData: jest.fn().mockResolvedValue([
        {
          date: '2023-01-01',
          open: 140.0,
          close: 142.5
        }
      ]),
      getCompanyInfo: jest.fn().mockResolvedValue({
        longName: 'Apple Inc.',
        symbol: 'AAPL',
        industry: 'Consumer Electronics'
      }),
      getMarketNews: jest.fn().mockResolvedValue([
        {
          title: 'Market News 1',
          published: '2023-01-01'
        }
      ]),
      search: jest.fn().mockResolvedValue([
        {
          shortname: 'Apple Inc.',
          symbol: 'AAPL'
        }
      ])
    } as any;
  });
  
  test('Get stock quote', async () => {
    // Get stock quote
    const quote = await reagent.getStockQuote('AAPL');
    
    // Check if quote was retrieved
    expect(quote).toBeDefined();
    expect(quote.symbol).toBe('AAPL');
    expect(quote.regularMarketPrice).toBe(150.0);
    
    // Check if agent method was called
    expect(reagent['yahooFinanceAgent'].getStockQuote).toHaveBeenCalledWith('AAPL');
  });
  
  test('Get historical data', async () => {
    // Get historical data
    const data = await reagent.getHistoricalData('AAPL', '1mo', '1d');
    
    // Check if data was retrieved
    expect(data).toBeDefined();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBe(1);
    expect(data[0].date).toBe('2023-01-01');
    expect(data[0].open).toBe(140.0);
    
    // Check if agent method was called
    expect(reagent['yahooFinanceAgent'].getHistoricalData).toHaveBeenCalledWith('AAPL', '1mo', '1d');
  });
});
