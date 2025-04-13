import { PostgreSQLService } from '../src/services/postgresql-service';
import { DatabaseAgent } from '../src/trading/agents/database-agent';
import { ReAgent } from '../src/trading/reagent';

describe('PostgreSQL Service Tests', () => {
  let postgresqlService: PostgreSQLService;
  
  beforeAll(() => {
    // Initialize the PostgreSQL service with caching disabled for tests
    postgresqlService = new PostgreSQLService('http://localhost', 8006, false);
  });
  
  test('Execute query', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify([
              { id: 1, name: 'Test 1' },
              { id: 2, name: 'Test 2' }
            ])
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Execute query
    const result = await postgresqlService.executeQuery(
      'SELECT * FROM test_table WHERE id = $1',
      [1]
    );
    
    // Check if query result was returned
    expect(result).toBeDefined();
    expect(result.length).toBe(2);
    expect(result[0].id).toBe(1);
    expect(result[0].name).toBe('Test 1');
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8006/call_tool',
      {
        name: 'execute_query',
        arguments: {
          query: 'SELECT * FROM test_table WHERE id = $1',
          params: '[1]'
        }
      }
    );
  });
  
  test('Create table', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              success: true,
              message: 'Table created successfully'
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Create table
    const columns = [
      { name: 'id', type: 'SERIAL', primary_key: true },
      { name: 'name', type: 'VARCHAR(100)', not_null: true },
      { name: 'created_at', type: 'TIMESTAMP', default: 'CURRENT_TIMESTAMP' }
    ];
    
    const result = await postgresqlService.createTable('test_table', columns);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.message).toBe('Table created successfully');
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8006/call_tool',
      {
        name: 'create_table',
        arguments: {
          table_name: 'test_table',
          columns: JSON.stringify(columns)
        }
      }
    );
  });
  
  test('Insert data', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              success: true,
              message: 'Data inserted successfully',
              rows_affected: 2
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Insert data
    const data = [
      { name: 'Test 1' },
      { name: 'Test 2' }
    ];
    
    const result = await postgresqlService.insertData('test_table', data);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.message).toBe('Data inserted successfully');
    expect(result.rows_affected).toBe(2);
    
    // Check if axios.post was called with the correct arguments
    expect(global.axios.post).toHaveBeenCalledWith(
      'http://localhost:8006/call_tool',
      {
        name: 'insert_data',
        arguments: {
          table_name: 'test_table',
          data: JSON.stringify(data)
        }
      }
    );
  });
});

describe('Database Agent Tests', () => {
  let databaseAgent: DatabaseAgent;
  
  beforeAll(() => {
    // Initialize the Database agent
    databaseAgent = new DatabaseAgent();
    
    // Mock the PostgreSQLService methods
    databaseAgent['postgresqlService'] = {
      startServer: jest.fn().mockResolvedValue(true),
      stopServer: jest.fn().mockResolvedValue(true),
      executeQuery: jest.fn().mockResolvedValue([
        { id: 1, name: 'Test 1' },
        { id: 2, name: 'Test 2' }
      ]),
      createTable: jest.fn().mockResolvedValue({
        success: true,
        message: 'Table created successfully'
      }),
      insertData: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data inserted successfully',
        rows_affected: 2
      }),
      updateData: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data updated successfully',
        rows_affected: 1
      }),
      deleteData: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data deleted successfully',
        rows_affected: 1
      }),
      getTableSchema: jest.fn().mockResolvedValue([
        { column_name: 'id', data_type: 'integer', is_nullable: 'NO', column_default: "nextval('test_table_id_seq'::regclass)" },
        { column_name: 'name', data_type: 'character varying', is_nullable: 'NO', column_default: null },
        { column_name: 'created_at', data_type: 'timestamp without time zone', is_nullable: 'YES', column_default: 'CURRENT_TIMESTAMP' }
      ]),
      listTables: jest.fn().mockResolvedValue([
        { table_name: 'test_table' },
        { table_name: 'historical_data' }
      ]),
      importFromCSV: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data imported successfully',
        rows_affected: 10
      }),
      exportToCSV: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data exported successfully',
        csv_content: 'id,name,created_at\n1,Test 1,2023-01-01\n2,Test 2,2023-01-02'
      }),
      createBackup: jest.fn().mockResolvedValue({
        success: true,
        message: 'Backup created successfully',
        backup_content: 'backup content'
      }),
      restoreBackup: jest.fn().mockResolvedValue({
        success: true,
        message: 'Backup restored successfully'
      })
    } as any;
    
    // Mock the YahooFinanceService methods
    databaseAgent['yahooFinanceService'] = {
      getHistoricalData: jest.fn().mockResolvedValue([
        {
          date: '2023-01-01',
          open: 100,
          high: 110,
          low: 95,
          close: 105,
          volume: 1000000
        },
        {
          date: '2023-01-02',
          open: 105,
          high: 115,
          low: 100,
          close: 110,
          volume: 1100000
        }
      ])
    } as any;
  });
  
  test('Execute agent with query', async () => {
    // Execute the agent
    const result = await databaseAgent.execute({
      operation: 'execute_query',
      query: 'SELECT * FROM test_table WHERE id = $1',
      params: [1]
    });
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.operation).toBe('execute_query');
    expect(result.result).toBeDefined();
    expect(result.result.length).toBe(2);
    expect(result.result[0].id).toBe(1);
    expect(result.result[0].name).toBe('Test 1');
    
    // Check if service methods were called
    expect(databaseAgent['postgresqlService'].startServer).toHaveBeenCalled();
    expect(databaseAgent['postgresqlService'].executeQuery).toHaveBeenCalledWith(
      'SELECT * FROM test_table WHERE id = $1',
      [1]
    );
    expect(databaseAgent['postgresqlService'].stopServer).toHaveBeenCalled();
  });
  
  test('Execute query', async () => {
    // Execute query
    const result = await databaseAgent.executeQuery(
      'SELECT * FROM test_table WHERE id = $1',
      [1]
    );
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.length).toBe(2);
    expect(result[0].id).toBe(1);
    expect(result[0].name).toBe('Test 1');
    
    // Check if service methods were called
    expect(databaseAgent['postgresqlService'].startServer).toHaveBeenCalled();
    expect(databaseAgent['postgresqlService'].executeQuery).toHaveBeenCalledWith(
      'SELECT * FROM test_table WHERE id = $1',
      [1]
    );
    expect(databaseAgent['postgresqlService'].stopServer).toHaveBeenCalled();
  });
  
  test('Store historical data', async () => {
    // Store historical data
    const result = await databaseAgent.storeHistoricalData('AAPL', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.period).toBe('1y');
    expect(result.interval).toBe('1d');
    expect(result.totalPoints).toBe(2);
    expect(result.insertedCount).toBe(2);
    
    // Check if service methods were called
    expect(databaseAgent['postgresqlService'].startServer).toHaveBeenCalled();
    expect(databaseAgent['yahooFinanceService'].getHistoricalData).toHaveBeenCalledWith('AAPL', '1y', '1d');
    expect(databaseAgent['postgresqlService'].executeQuery).toHaveBeenCalled();
    expect(databaseAgent['postgresqlService'].stopServer).toHaveBeenCalled();
  });
});

describe('ReAgent Integration Tests', () => {
  let reagent: ReAgent;
  
  beforeAll(() => {
    // Initialize the ReAgent
    reagent = new ReAgent();
    
    // Mock the DatabaseAgent methods
    reagent['databaseAgent'] = {
      executeQuery: jest.fn().mockResolvedValue([
        { id: 1, name: 'Test 1' },
        { id: 2, name: 'Test 2' }
      ]),
      createTable: jest.fn().mockResolvedValue({
        success: true,
        message: 'Table created successfully'
      }),
      insertData: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data inserted successfully',
        rows_affected: 2
      }),
      updateData: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data updated successfully',
        rows_affected: 1
      }),
      deleteData: jest.fn().mockResolvedValue({
        success: true,
        message: 'Data deleted successfully',
        rows_affected: 1
      }),
      getTableSchema: jest.fn().mockResolvedValue([
        { column_name: 'id', data_type: 'integer', is_nullable: 'NO', column_default: "nextval('test_table_id_seq'::regclass)" },
        { column_name: 'name', data_type: 'character varying', is_nullable: 'NO', column_default: null },
        { column_name: 'created_at', data_type: 'timestamp without time zone', is_nullable: 'YES', column_default: 'CURRENT_TIMESTAMP' }
      ]),
      listTables: jest.fn().mockResolvedValue([
        { table_name: 'test_table' },
        { table_name: 'historical_data' }
      ]),
      storeHistoricalData: jest.fn().mockResolvedValue({
        symbol: 'AAPL',
        period: '1y',
        interval: '1d',
        totalPoints: 252,
        insertedCount: 252
      }),
      getHistoricalData: jest.fn().mockResolvedValue([
        {
          symbol: 'AAPL',
          date: '2023-01-01',
          open: 100,
          high: 110,
          low: 95,
          close: 105,
          volume: 1000000
        },
        {
          symbol: 'AAPL',
          date: '2023-01-02',
          open: 105,
          high: 115,
          low: 100,
          close: 110,
          volume: 1100000
        }
      ]),
      storeStrategyResults: jest.fn().mockResolvedValue({
        strategyName: 'Test Strategy',
        symbol: 'AAPL',
        strategyResultId: 1,
        tradeCount: 10
      }),
      getStrategyResults: jest.fn().mockResolvedValue([
        {
          id: 1,
          strategy_name: 'Test Strategy',
          symbol: 'AAPL',
          start_date: '2023-01-01',
          end_date: '2023-12-31',
          total_return: 25.5,
          annual_return: 25.5,
          sharpe_ratio: 1.2,
          max_drawdown: 10.5,
          win_rate: 65.0,
          trade_count: 10,
          trades: [
            {
              id: 1,
              strategy_result_id: 1,
              date: '2023-01-15',
              type: 'buy',
              price: 110.0,
              shares: 10
            },
            {
              id: 2,
              strategy_result_id: 1,
              date: '2023-02-15',
              type: 'sell',
              price: 120.0,
              shares: 10
            }
          ]
        }
      ])
    } as any;
  });
  
  test('Execute query', async () => {
    // Execute query
    const result = await reagent.executeQuery(
      'SELECT * FROM test_table WHERE id = $1',
      [1]
    );
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.length).toBe(2);
    expect(result[0].id).toBe(1);
    expect(result[0].name).toBe('Test 1');
    
    // Check if agent method was called
    expect(reagent['databaseAgent'].executeQuery).toHaveBeenCalledWith(
      'SELECT * FROM test_table WHERE id = $1',
      [1]
    );
  });
  
  test('List tables', async () => {
    // List tables
    const result = await reagent.listTables();
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.length).toBe(2);
    expect(result[0].table_name).toBe('test_table');
    expect(result[1].table_name).toBe('historical_data');
    
    // Check if agent method was called
    expect(reagent['databaseAgent'].listTables).toHaveBeenCalled();
  });
  
  test('Store historical data', async () => {
    // Store historical data
    const result = await reagent.storeHistoricalData('AAPL', '1y', '1d');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.symbol).toBe('AAPL');
    expect(result.period).toBe('1y');
    expect(result.interval).toBe('1d');
    expect(result.totalPoints).toBe(252);
    expect(result.insertedCount).toBe(252);
    
    // Check if agent method was called
    expect(reagent['databaseAgent'].storeHistoricalData).toHaveBeenCalledWith('AAPL', '1y', '1d');
  });
  
  test('Get historical data from DB', async () => {
    // Get historical data from DB
    const result = await reagent.getHistoricalDataFromDB('AAPL', '2023-01-01', '2023-01-02');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.length).toBe(2);
    expect(result[0].symbol).toBe('AAPL');
    expect(result[0].date).toBe('2023-01-01');
    expect(result[0].close).toBe(105);
    
    // Check if agent method was called
    expect(reagent['databaseAgent'].getHistoricalData).toHaveBeenCalledWith('AAPL', '2023-01-01', '2023-01-02');
  });
  
  test('Store strategy results', async () => {
    // Store strategy results
    const strategyResults = {
      startDate: '2023-01-01',
      endDate: '2023-12-31',
      totalReturn: 25.5,
      annualReturn: 25.5,
      sharpeRatio: 1.2,
      maxDrawdown: 10.5,
      winRate: 65.0,
      trades: [
        {
          date: '2023-01-15',
          type: 'buy',
          price: 110.0,
          shares: 10
        },
        {
          date: '2023-02-15',
          type: 'sell',
          price: 120.0,
          shares: 10
        }
      ]
    };
    
    const result = await reagent.storeStrategyResults('Test Strategy', 'AAPL', strategyResults);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.strategyName).toBe('Test Strategy');
    expect(result.symbol).toBe('AAPL');
    expect(result.strategyResultId).toBe(1);
    expect(result.tradeCount).toBe(10);
    
    // Check if agent method was called
    expect(reagent['databaseAgent'].storeStrategyResults).toHaveBeenCalledWith('Test Strategy', 'AAPL', strategyResults);
  });
  
  test('Get strategy results', async () => {
    // Get strategy results
    const result = await reagent.getStrategyResults('Test Strategy', 'AAPL');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.length).toBe(1);
    expect(result[0].strategy_name).toBe('Test Strategy');
    expect(result[0].symbol).toBe('AAPL');
    expect(result[0].total_return).toBe(25.5);
    expect(result[0].trades.length).toBe(2);
    
    // Check if agent method was called
    expect(reagent['databaseAgent'].getStrategyResults).toHaveBeenCalledWith('Test Strategy', 'AAPL');
  });
});
