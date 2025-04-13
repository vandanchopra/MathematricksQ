import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * Service for interacting with the PostgreSQL MCP server
 */
export class PostgreSQLService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds
  private serverProcess: any;

  /**
   * Initialize the PostgreSQL service
   * @param serverUrl URL of the PostgreSQL MCP server
   * @param serverPort Port of the PostgreSQL MCP server
   * @param cacheEnabled Whether to enable caching
   * @param cacheExpiration Cache expiration time in seconds
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8006,
    cacheEnabled: boolean = true,
    cacheExpiration: number = 3600 // 1 hour
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.cacheEnabled = cacheEnabled;
    this.cacheExpiration = cacheExpiration * 1000; // convert to milliseconds
    
    // Set up cache directory
    this.cachePath = path.join(process.cwd(), 'data', 'postgresql', 'cache');
    if (this.cacheEnabled && !fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
  }

  /**
   * Start the PostgreSQL MCP server
   * @returns Promise that resolves when the server is started
   */
  public async startServer(): Promise<boolean> {
    try {
      console.log('Starting PostgreSQL MCP server...');
      
      // Check if server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('PostgreSQL MCP server is already running');
          return true;
        }
      } catch (error) {
        // Server is not running, continue with starting it
      }
      
      // Start the server using Docker
      this.serverProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.postgresql.yml'),
        'up',
        '-d'
      ]);
      
      // Wait for the server to start
      return new Promise((resolve) => {
        this.serverProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('PostgreSQL MCP server started successfully');
            
            // Wait for the server to be ready
            this.waitForServer(10, 1000)
              .then(() => resolve(true))
              .catch(() => resolve(false));
          } else {
            console.error(`PostgreSQL MCP server failed to start with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error starting PostgreSQL MCP server:', error);
      return false;
    }
  }

  /**
   * Stop the PostgreSQL MCP server
   * @returns Promise that resolves when the server is stopped
   */
  public async stopServer(): Promise<boolean> {
    try {
      console.log('Stopping PostgreSQL MCP server...');
      
      // Stop the server using Docker
      const stopProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.postgresql.yml'),
        'down'
      ]);
      
      // Wait for the server to stop
      return new Promise((resolve) => {
        stopProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('PostgreSQL MCP server stopped successfully');
            resolve(true);
          } else {
            console.error(`PostgreSQL MCP server failed to stop with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error stopping PostgreSQL MCP server:', error);
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
          console.log('PostgreSQL MCP server is ready');
          return;
        }
      } catch (error) {
        console.log(`Waiting for PostgreSQL MCP server to be ready (${i + 1}/${maxRetries})...`);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    throw new Error('PostgreSQL MCP server failed to start');
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
   * Execute a SQL query
   * @param query SQL query to execute
   * @param params Parameters for the query
   * @returns Query results
   */
  public async executeQuery(query: string, params: any[] = []): Promise<any> {
    try {
      console.log(`Executing SQL query: ${query.substring(0, 100)}...`);
      
      // Create cache key
      const cacheKey = `query_${query.replace(/\s+/g, '_').substring(0, 50)}_${JSON.stringify(params).replace(/\W/g, '')}`;
      
      // Check cache first if enabled and query is a SELECT
      if (this.cacheEnabled && query.trim().toUpperCase().startsWith('SELECT')) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached query result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'execute_query',
        arguments: {
          query,
          params: JSON.stringify(params)
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Cache the response if enabled and query is a SELECT
      if (this.cacheEnabled && query.trim().toUpperCase().startsWith('SELECT')) {
        this.saveToCache(cacheKey, result);
      }
      
      return result;
    } catch (error) {
      console.error('Error executing SQL query:', error);
      throw error;
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
      console.log(`Creating table: ${tableName}`);
      
      // Prepare the request payload
      const payload = {
        name: 'create_table',
        arguments: {
          table_name: tableName,
          columns: JSON.stringify(columns)
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error creating table:', error);
      throw error;
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
      console.log(`Inserting data into table: ${tableName}`);
      
      // Prepare the request payload
      const payload = {
        name: 'insert_data',
        arguments: {
          table_name: tableName,
          data: JSON.stringify(data)
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error inserting data:', error);
      throw error;
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
      console.log(`Updating data in table: ${tableName}`);
      
      // Prepare the request payload
      const payload = {
        name: 'update_data',
        arguments: {
          table_name: tableName,
          data: JSON.stringify(data),
          condition
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error updating data:', error);
      throw error;
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
      console.log(`Deleting data from table: ${tableName}`);
      
      // Prepare the request payload
      const payload = {
        name: 'delete_data',
        arguments: {
          table_name: tableName,
          condition
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error deleting data:', error);
      throw error;
    }
  }

  /**
   * Get table schema
   * @param tableName Name of the table to get schema for
   * @returns Table schema
   */
  public async getTableSchema(tableName: string): Promise<any> {
    try {
      console.log(`Getting schema for table: ${tableName}`);
      
      // Create cache key
      const cacheKey = `schema_${tableName}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached schema');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'get_table_schema',
        arguments: {
          table_name: tableName
        }
      };
      
      // Call the PostgreSQL MCP server
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
      console.error('Error getting table schema:', error);
      throw error;
    }
  }

  /**
   * List tables in the database
   * @returns List of tables
   */
  public async listTables(): Promise<any> {
    try {
      console.log('Listing tables in the database');
      
      // Create cache key
      const cacheKey = 'list_tables';
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached table list');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'list_tables',
        arguments: {}
      };
      
      // Call the PostgreSQL MCP server
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
      console.error('Error listing tables:', error);
      throw error;
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
      console.log(`Importing data from CSV file: ${filePath} into table: ${tableName}`);
      
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        throw new Error(`File not found: ${filePath}`);
      }
      
      // Read the file content
      const fileContent = fs.readFileSync(filePath, 'utf8');
      
      // Prepare the request payload
      const payload = {
        name: 'import_from_csv',
        arguments: {
          table_name: tableName,
          csv_content: fileContent,
          options: JSON.stringify(options)
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error importing from CSV:', error);
      throw error;
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
      console.log(`Exporting data from table: ${tableName} to CSV file: ${filePath}`);
      
      // Prepare the request payload
      const payload = {
        name: 'export_to_csv',
        arguments: {
          table_name: tableName,
          condition
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Write the CSV content to the file
      if (result.csv_content) {
        fs.writeFileSync(filePath, result.csv_content);
      }
      
      return result;
    } catch (error) {
      console.error('Error exporting to CSV:', error);
      throw error;
    }
  }

  /**
   * Create a database backup
   * @param backupPath Path to the backup file
   * @returns Result of the operation
   */
  public async createBackup(backupPath: string): Promise<any> {
    try {
      console.log(`Creating database backup: ${backupPath}`);
      
      // Prepare the request payload
      const payload = {
        name: 'create_backup',
        arguments: {}
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      // Write the backup content to the file
      if (result.backup_content) {
        fs.writeFileSync(backupPath, result.backup_content);
      }
      
      return result;
    } catch (error) {
      console.error('Error creating backup:', error);
      throw error;
    }
  }

  /**
   * Restore a database from a backup
   * @param backupPath Path to the backup file
   * @returns Result of the operation
   */
  public async restoreBackup(backupPath: string): Promise<any> {
    try {
      console.log(`Restoring database from backup: ${backupPath}`);
      
      // Check if file exists
      if (!fs.existsSync(backupPath)) {
        throw new Error(`File not found: ${backupPath}`);
      }
      
      // Read the file content
      const fileContent = fs.readFileSync(backupPath, 'utf8');
      
      // Prepare the request payload
      const payload = {
        name: 'restore_backup',
        arguments: {
          backup_content: fileContent
        }
      };
      
      // Call the PostgreSQL MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error restoring backup:', error);
      throw error;
    }
  }
}
