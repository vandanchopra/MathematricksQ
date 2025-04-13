import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * Service for interacting with the Academic Search MCP server
 */
export class AcademicSearchService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds
  private serverProcess: any;

  /**
   * Initialize the Academic Search service
   * @param serverUrl URL of the Academic Search MCP server
   * @param serverPort Port of the Academic Search MCP server
   * @param cacheEnabled Whether to enable caching
   * @param cacheExpiration Cache expiration time in seconds
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8002,
    cacheEnabled: boolean = true,
    cacheExpiration: number = 3600 // 1 hour
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.cacheEnabled = cacheEnabled;
    this.cacheExpiration = cacheExpiration * 1000; // convert to milliseconds

    // Set up cache directory
    this.cachePath = path.join(process.cwd(), 'data', 'academic-search', 'cache');
    if (this.cacheEnabled && !fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
  }

  /**
   * Start the Academic Search MCP server
   * @returns Promise that resolves when the server is started
   */
  public async startServer(): Promise<boolean> {
    try {
      console.log('Starting Academic Search MCP server...');

      // Check if server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('Academic Search MCP server is already running');
          return true;
        }
      } catch (error) {
        // Server is not running, continue with starting it
      }

      // Start the server using Docker
      this.serverProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.academic-search.yml'),
        'up',
        '-d'
      ]);

      // Wait for the server to start
      return new Promise((resolve) => {
        this.serverProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Academic Search MCP server started successfully');

            // Wait for the server to be ready
            this.waitForServer(10, 1000)
              .then(() => resolve(true))
              .catch(() => resolve(false));
          } else {
            console.error(`Academic Search MCP server failed to start with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error starting Academic Search MCP server:', error);
      return false;
    }
  }

  /**
   * Stop the Academic Search MCP server
   * @returns Promise that resolves when the server is stopped
   */
  public async stopServer(): Promise<boolean> {
    try {
      console.log('Stopping Academic Search MCP server...');

      // Stop the server using Docker
      const stopProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.academic-search.yml'),
        'down'
      ]);

      // Wait for the server to stop
      return new Promise((resolve) => {
        stopProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Academic Search MCP server stopped successfully');
            resolve(true);
          } else {
            console.error(`Academic Search MCP server failed to stop with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error stopping Academic Search MCP server:', error);
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
          console.log('Academic Search MCP server is ready');
          return;
        }
      } catch (error) {
        console.log(`Waiting for Academic Search MCP server to be ready (${i + 1}/${maxRetries})...`);
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    throw new Error('Academic Search MCP server failed to start');
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
   * Search for academic papers
   * @param query Search query
   * @param maxResults Maximum number of results to return
   * @param sources Sources to search (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @param dateFrom Start date for search (YYYY-MM-DD)
   * @param dateTo End date for search (YYYY-MM-DD)
   * @returns Search results
   */
  public async searchPapers(
    query: string,
    maxResults: number = 10,
    sources: string[] = ['arxiv', 'pubmed', 'semanticscholar'],
    dateFrom?: string,
    dateTo?: string
  ): Promise<any[]> {
    try {
      console.log(`Searching for papers: ${query}`);

      // Create cache key
      const cacheKey = `search_${query.replace(/\s+/g, '_')}_${maxResults}_${sources.join('_')}_${dateFrom || ''}_${dateTo || ''}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached search results');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload: any = {
        name: 'search_papers',
        arguments: {
          query,
          max_results: maxResults,
          sources
        }
      };

      // Add optional parameters if provided
      if (dateFrom) {
        payload.arguments.date_from = dateFrom;
      }

      if (dateTo) {
        payload.arguments.date_to = dateTo;
      }

      // Call the Academic Search MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const papers = JSON.parse(response.data.content[0].text);

      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, papers);
      }

      return papers;
    } catch (error) {
      console.error('Error searching for papers:', error);
      return [];
    }
  }

  /**
   * Get paper details
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @returns Paper details
   */
  public async getPaperDetails(paperId: string, source: string): Promise<any> {
    try {
      console.log(`Getting paper details: ${paperId} from ${source}`);

      // Create cache key
      const cacheKey = `paper_${source}_${paperId}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached paper details');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_paper_details',
        arguments: {
          paper_id: paperId,
          source
        }
      };

      // Call the Academic Search MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const paperDetails = JSON.parse(response.data.content[0].text);

      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, paperDetails);
      }

      return paperDetails;
    } catch (error) {
      console.error('Error getting paper details:', error);
      return null;
    }
  }

  /**
   * Download a paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @returns Whether the download was successful
   */
  public async downloadPaper(paperId: string, source: string): Promise<boolean> {
    try {
      console.log(`Downloading paper: ${paperId} from ${source}`);

      // Prepare the request payload
      const payload = {
        name: 'download_paper',
        arguments: {
          paper_id: paperId,
          source
        }
      };

      // Call the Academic Search MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const result = JSON.parse(response.data.content[0].text);

      return result.success;
    } catch (error) {
      console.error('Error downloading paper:', error);
      return false;
    }
  }

  /**
   * Read a paper's content
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @returns Paper content
   */
  public async readPaper(paperId: string, source: string): Promise<string | null> {
    try {
      console.log(`Reading paper: ${paperId} from ${source}`);

      // Create cache key
      const cacheKey = `content_${source}_${paperId}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached paper content');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'read_paper',
        arguments: {
          paper_id: paperId,
          source
        }
      };

      // Call the Academic Search MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const content = response.data.content[0].text;

      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, content);
      }

      return content;
    } catch (error) {
      console.error('Error reading paper:', error);
      return null;
    }
  }

  /**
   * Get citations for a paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @param maxResults Maximum number of results to return
   * @returns Citations for the paper
   */
  public async getCitations(
    paperId: string,
    source: string,
    maxResults: number = 10
  ): Promise<any[]> {
    try {
      console.log(`Getting citations for paper: ${paperId} from ${source}`);

      // Create cache key
      const cacheKey = `citations_${source}_${paperId}_${maxResults}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached citations');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_citations',
        arguments: {
          paper_id: paperId,
          source,
          max_results: maxResults
        }
      };

      // Call the Academic Search MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const citations = JSON.parse(response.data.content[0].text);

      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, citations);
      }

      return citations;
    } catch (error) {
      console.error('Error getting citations:', error);
      return [];
    }
  }

  /**
   * Get references for a paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @param maxResults Maximum number of results to return
   * @returns References for the paper
   */
  public async getReferences(
    paperId: string,
    source: string,
    maxResults: number = 10
  ): Promise<any[]> {
    try {
      console.log(`Getting references for paper: ${paperId} from ${source}`);

      // Create cache key
      const cacheKey = `references_${source}_${paperId}_${maxResults}`;

      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached references');
          return cachedData;
        }
      }

      // Prepare the request payload
      const payload = {
        name: 'get_references',
        arguments: {
          paper_id: paperId,
          source,
          max_results: maxResults
        }
      };

      // Call the Academic Search MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const references = JSON.parse(response.data.content[0].text);

      // Cache the response if enabled
      if (this.cacheEnabled) {
        this.saveToCache(cacheKey, references);
      }

      return references;
    } catch (error) {
      console.error('Error getting references:', error);
      return [];
    }
  }

  /**
   * Search for trading strategy papers
   * @param strategyType Type of trading strategy
   * @param maxResults Maximum number of results to return
   * @param sources Sources to search (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @returns Search results
   */
  public async searchTradingStrategyPapers(
    strategyType: string,
    maxResults: number = 10,
    sources: string[] = ['arxiv', 'pubmed', 'semanticscholar']
  ): Promise<any[]> {
    // Create a query for trading strategy papers
    const query = `"trading strategy" AND "${strategyType}"`;

    // Search for papers
    return this.searchPapers(query, maxResults, sources);
  }
}
