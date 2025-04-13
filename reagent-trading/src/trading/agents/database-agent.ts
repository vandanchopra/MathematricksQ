import { Agent } from './agent';
import { PostgreSQLService } from '../../services/postgresql-service';
import { YahooFinanceService } from '../../services/yahoo-finance-service';
import * as path from 'path';

/**
 * Agent responsible for database operations
 */
export class DatabaseAgent extends Agent {
  private postgresqlService: PostgreSQLService;
  private yahooFinanceService: YahooFinanceService;

  /**
   * Initialize the database agent
   */
  constructor() {
    super();
    this.postgresqlService = new PostgreSQLService();
    this.yahooFinanceService = new YahooFinanceService();
  }

  /**
   * Execute the database agent
   * @param input Input parameters for database operations
   * @returns Database operation results
   */
  public async execute(input: any): Promise<any> {
    console.log('Executing database operations...');

    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      // Extract parameters from input
      const { operation, tableName, data, condition, query, params, filePath, options } = input;

      // Execute the appropriate operation
      let result;
      switch (operation) {
        case 'execute_query':
          result = await this.postgresqlService.executeQuery(query, params);
          break;
        case 'create_table':
          result = await this.postgresqlService.createTable(tableName, data);
          break;
        case 'insert_data':
          result = await this.postgresqlService.insertData(tableName, data);
          break;
        case 'update_data':
          result = await this.postgresqlService.updateData(tableName, data, condition);
          break;
        case 'delete_data':
          result = await this.postgresqlService.deleteData(tableName, condition);
          break;
        case 'get_table_schema':
          result = await this.postgresqlService.getTableSchema(tableName);
          break;
        case 'list_tables':
          result = await this.postgresqlService.listTables();
          break;
        case 'import_from_csv':
          result = await this.postgresqlService.importFromCSV(tableName, filePath, options);
          break;
        case 'export_to_csv':
          result = await this.postgresqlService.exportToCSV(tableName, filePath, condition);
          break;
        case 'create_backup':
          result = await this.postgresqlService.createBackup(filePath);
          break;
        case 'restore_backup':
          result = await this.postgresqlService.restoreBackup(filePath);
          break;
        default:
          throw new Error(`Unsupported operation: ${operation}`);
      }

      return {
        operation,
        result
      };
    } catch (error) {
      console.error('Error in database agent:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Execute a SQL query
   * @param query SQL query to execute
   * @param params Parameters for the query
   * @returns Query results
   */
  public async executeQuery(query: string, params: any[] = []): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Executing SQL query: ${query.substring(0, 100)}...`);
      const result = await this.postgresqlService.executeQuery(query, params);

      return result;
    } catch (error) {
      console.error('Error executing SQL query:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Create a table
   * @param tableName Name of the table to create
   * @param columns Columns for the table
   * @returns Result of the operation
   */
  public async createTable(tableName: string, columns: any[]): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Creating table: ${tableName}`);
      const result = await this.postgresqlService.createTable(tableName, columns);

      return result;
    } catch (error) {
      console.error('Error creating table:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Insert data into a table
   * @param tableName Name of the table to insert into
   * @param data Data to insert
   * @returns Result of the operation
   */
  public async insertData(tableName: string, data: any[]): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Inserting data into table: ${tableName}`);
      const result = await this.postgresqlService.insertData(tableName, data);

      return result;
    } catch (error) {
      console.error('Error inserting data:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Update data in a table
   * @param tableName Name of the table to update
   * @param data Data to update
   * @param condition Condition for the update
   * @returns Result of the operation
   */
  public async updateData(tableName: string, data: any, condition: string): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Updating data in table: ${tableName}`);
      const result = await this.postgresqlService.updateData(tableName, data, condition);

      return result;
    } catch (error) {
      console.error('Error updating data:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Delete data from a table
   * @param tableName Name of the table to delete from
   * @param condition Condition for the delete
   * @returns Result of the operation
   */
  public async deleteData(tableName: string, condition: string): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Deleting data from table: ${tableName}`);
      const result = await this.postgresqlService.deleteData(tableName, condition);

      return result;
    } catch (error) {
      console.error('Error deleting data:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Get table schema
   * @param tableName Name of the table to get schema for
   * @returns Table schema
   */
  public async getTableSchema(tableName: string): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Getting schema for table: ${tableName}`);
      const result = await this.postgresqlService.getTableSchema(tableName);

      return result;
    } catch (error) {
      console.error('Error getting table schema:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * List tables in the database
   * @returns List of tables
   */
  public async listTables(): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log('Listing tables in the database');
      const result = await this.postgresqlService.listTables();

      return result;
    } catch (error) {
      console.error('Error listing tables:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Import data from a CSV file
   * @param tableName Name of the table to import into
   * @param filePath Path to the CSV file
   * @param options Options for the import
   * @returns Result of the operation
   */
  public async importFromCSV(tableName: string, filePath: string, options: any = {}): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Importing data from CSV file: ${filePath} into table: ${tableName}`);
      const result = await this.postgresqlService.importFromCSV(tableName, filePath, options);

      return result;
    } catch (error) {
      console.error('Error importing from CSV:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Export data to a CSV file
   * @param tableName Name of the table to export from
   * @param filePath Path to the CSV file
   * @param condition Condition for the export
   * @returns Result of the operation
   */
  public async exportToCSV(tableName: string, filePath: string, condition: string = ''): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Exporting data from table: ${tableName} to CSV file: ${filePath}`);
      const result = await this.postgresqlService.exportToCSV(tableName, filePath, condition);

      return result;
    } catch (error) {
      console.error('Error exporting to CSV:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Create a database backup
   * @param backupPath Path to the backup file
   * @returns Result of the operation
   */
  public async createBackup(backupPath: string): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Creating database backup: ${backupPath}`);
      const result = await this.postgresqlService.createBackup(backupPath);

      return result;
    } catch (error) {
      console.error('Error creating backup:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Restore a database from a backup
   * @param backupPath Path to the backup file
   * @returns Result of the operation
   */
  public async restoreBackup(backupPath: string): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      console.log(`Restoring database from backup: ${backupPath}`);
      const result = await this.postgresqlService.restoreBackup(backupPath);

      return result;
    } catch (error) {
      console.error('Error restoring backup:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Store historical data for a symbol
   * @param symbol Stock symbol
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @returns Result of the operation
   */
  public async storeHistoricalData(symbol: string, period: string = '1y', interval: string = '1d'): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      // Get historical data for the symbol
      const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);
      console.log(`Got ${historicalData.length} historical data points for ${symbol}`);

      // Create the historical_data table if it doesn't exist
      const createTableQuery = `
        CREATE TABLE IF NOT EXISTS historical_data (
          id SERIAL PRIMARY KEY,
          symbol VARCHAR(20) NOT NULL,
          date DATE NOT NULL,
          open NUMERIC NOT NULL,
          high NUMERIC NOT NULL,
          low NUMERIC NOT NULL,
          close NUMERIC NOT NULL,
          volume BIGINT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(symbol, date)
        )
      `;
      await this.postgresqlService.executeQuery(createTableQuery);

      // Create index on symbol and date if it doesn't exist
      const createIndexQuery = `
        CREATE INDEX IF NOT EXISTS idx_historical_data_symbol_date ON historical_data(symbol, date)
      `;
      await this.postgresqlService.executeQuery(createIndexQuery);

      // Prepare data for insertion
      const data = historicalData.map((item: any) => ({
        symbol,
        date: item.date,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume
      }));

      // Insert data into the table
      const insertQuery = `
        INSERT INTO historical_data (symbol, date, open, high, low, close, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, date) DO UPDATE SET
          open = EXCLUDED.open,
          high = EXCLUDED.high,
          low = EXCLUDED.low,
          close = EXCLUDED.close,
          volume = EXCLUDED.volume
      `;

      let insertedCount = 0;
      for (const item of data) {
        try {
          await this.postgresqlService.executeQuery(insertQuery, [
            item.symbol,
            item.date,
            item.open,
            item.high,
            item.low,
            item.close,
            item.volume
          ]);
          insertedCount++;
        } catch (error) {
          console.error(`Error inserting data for ${item.symbol} on ${item.date}:`, error);
        }
      }

      return {
        symbol,
        period,
        interval,
        totalPoints: historicalData.length,
        insertedCount
      };
    } catch (error) {
      console.error('Error storing historical data:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Get historical data for a symbol from the database
   * @param symbol Stock symbol
   * @param startDate Start date (YYYY-MM-DD)
   * @param endDate End date (YYYY-MM-DD)
   * @returns Historical data
   */
  public async getHistoricalData(symbol: string, startDate?: string, endDate?: string): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      // Build the query
      let query = 'SELECT * FROM historical_data WHERE symbol = $1';
      const params: any[] = [symbol];

      if (startDate) {
        query += ' AND date >= $2';
        params.push(startDate);
      }

      if (endDate) {
        query += ` AND date <= $${params.length + 1}`;
        params.push(endDate);
      }

      query += ' ORDER BY date ASC';

      // Execute the query
      const result = await this.postgresqlService.executeQuery(query, params);

      return result;
    } catch (error) {
      console.error('Error getting historical data:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Store strategy results
   * @param strategyName Name of the strategy
   * @param symbol Stock symbol
   * @param results Strategy results
   * @returns Result of the operation
   */
  public async storeStrategyResults(strategyName: string, symbol: string, results: any): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      // Create the strategy_results table if it doesn't exist
      const createTableQuery = `
        CREATE TABLE IF NOT EXISTS strategy_results (
          id SERIAL PRIMARY KEY,
          strategy_name VARCHAR(100) NOT NULL,
          symbol VARCHAR(20) NOT NULL,
          start_date DATE NOT NULL,
          end_date DATE NOT NULL,
          total_return NUMERIC NOT NULL,
          annual_return NUMERIC NOT NULL,
          sharpe_ratio NUMERIC NOT NULL,
          max_drawdown NUMERIC NOT NULL,
          win_rate NUMERIC NOT NULL,
          trade_count INTEGER NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `;
      await this.postgresqlService.executeQuery(createTableQuery);

      // Create the strategy_trades table if it doesn't exist
      const createTradesTableQuery = `
        CREATE TABLE IF NOT EXISTS strategy_trades (
          id SERIAL PRIMARY KEY,
          strategy_result_id INTEGER NOT NULL,
          date DATE NOT NULL,
          type VARCHAR(10) NOT NULL,
          price NUMERIC NOT NULL,
          shares NUMERIC NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (strategy_result_id) REFERENCES strategy_results(id) ON DELETE CASCADE
        )
      `;
      await this.postgresqlService.executeQuery(createTradesTableQuery);

      // Insert strategy results
      const insertResultsQuery = `
        INSERT INTO strategy_results (
          strategy_name, symbol, start_date, end_date, total_return, annual_return,
          sharpe_ratio, max_drawdown, win_rate, trade_count
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id
      `;

      const resultParams = [
        strategyName,
        symbol,
        results.startDate,
        results.endDate,
        results.totalReturn,
        results.annualReturn,
        results.sharpeRatio,
        results.maxDrawdown,
        results.winRate,
        results.trades.length
      ];

      const resultInsert = await this.postgresqlService.executeQuery(insertResultsQuery, resultParams);
      const strategyResultId = resultInsert[0].id;

      // Insert trades
      const insertTradeQuery = `
        INSERT INTO strategy_trades (
          strategy_result_id, date, type, price, shares
        )
        VALUES ($1, $2, $3, $4, $5)
      `;

      for (const trade of results.trades) {
        await this.postgresqlService.executeQuery(insertTradeQuery, [
          strategyResultId,
          trade.date,
          trade.type,
          trade.price,
          trade.shares
        ]);
      }

      return {
        strategyName,
        symbol,
        strategyResultId,
        tradeCount: results.trades.length
      };
    } catch (error) {
      console.error('Error storing strategy results:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }

  /**
   * Get strategy results
   * @param strategyName Name of the strategy (optional)
   * @param symbol Stock symbol (optional)
   * @returns Strategy results
   */
  public async getStrategyResults(strategyName?: string, symbol?: string): Promise<any> {
    try {
      // Start the PostgreSQL MCP server
      await this.postgresqlService.startServer();

      // Build the query
      let query = 'SELECT * FROM strategy_results';
      const params: any[] = [];

      if (strategyName || symbol) {
        query += ' WHERE';
      }

      if (strategyName) {
        query += ' strategy_name = $1';
        params.push(strategyName);
      }

      if (symbol) {
        if (strategyName) {
          query += ' AND';
        }
        query += ` symbol = $${params.length + 1}`;
        params.push(symbol);
      }

      query += ' ORDER BY created_at DESC';

      // Execute the query
      const results = await this.postgresqlService.executeQuery(query, params);

      // Get trades for each result
      for (const result of results) {
        const tradesQuery = 'SELECT * FROM strategy_trades WHERE strategy_result_id = $1 ORDER BY date ASC';
        const trades = await this.postgresqlService.executeQuery(tradesQuery, [result.id]);
        result.trades = trades;
      }

      return results;
    } catch (error) {
      console.error('Error getting strategy results:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the PostgreSQL MCP server
      await this.postgresqlService.stopServer();
    }
  }
}
