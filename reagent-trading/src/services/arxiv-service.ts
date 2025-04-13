import axios from 'axios';
import { spawn } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';

const sleep = promisify(setTimeout);

/**
 * Service for interacting with the ArXiv MCP server
 */
export class ArxivService {
  private serverProcess: any;
  private serverUrl: string;
  private serverPort: number;
  private isServerRunning: boolean = false;
  private storagePath: string;

  /**
   * Initialize the ArXiv service
   * @param serverUrl URL of the ArXiv MCP server
   * @param serverPort Port of the ArXiv MCP server
   * @param storagePath Path to store downloaded papers
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8000,
    storagePath: string = path.join(process.cwd(), 'data', 'papers')
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.storagePath = storagePath;

    // Create storage directory if it doesn't exist
    if (!fs.existsSync(this.storagePath)) {
      fs.mkdirSync(this.storagePath, { recursive: true });
    }
  }

  /**
   * Start the ArXiv MCP server
   */
  public async startServer(): Promise<void> {
    if (this.isServerRunning) {
      console.log('ArXiv MCP server is already running');
      return;
    }

    try {
      console.log('Starting ArXiv MCP server...');

      // Check if the server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('ArXiv MCP server is already running');
          this.isServerRunning = true;
          return;
        }
      } catch (error) {
        // Server is not running, continue with startup
      }

      // Start the server using the arxiv-mcp-server command
      this.serverProcess = spawn('arxiv-mcp-server', [
        '--storage-path', this.storagePath
      ]);

      this.serverProcess.stdout.on('data', (data: Buffer) => {
        console.log(`ArXiv MCP server: ${data.toString()}`);
      });

      this.serverProcess.stderr.on('data', (data: Buffer) => {
        console.error(`ArXiv MCP server error: ${data.toString()}`);
      });

      this.serverProcess.on('close', (code: number) => {
        console.log(`ArXiv MCP server exited with code ${code}`);
        this.isServerRunning = false;
      });

      // Wait for the server to start
      await sleep(2000);
      this.isServerRunning = true;
      console.log('ArXiv MCP server started successfully');
    } catch (error) {
      console.error('Failed to start ArXiv MCP server:', error);
      throw error;
    }
  }

  /**
   * Stop the ArXiv MCP server
   */
  public async stopServer(): Promise<void> {
    if (!this.isServerRunning || !this.serverProcess) {
      console.log('ArXiv MCP server is not running');
      return;
    }

    try {
      console.log('Stopping ArXiv MCP server...');
      this.serverProcess.kill();
      this.isServerRunning = false;
      console.log('ArXiv MCP server stopped successfully');
    } catch (error) {
      console.error('Failed to stop ArXiv MCP server:', error);
      throw error;
    }
  }

  /**
   * Search for papers on ArXiv
   * @param query Search query
   * @param maxResults Maximum number of results to return
   * @param dateFrom Start date for filtering papers
   * @param dateTo End date for filtering papers
   * @param categories Categories to filter papers by
   * @returns Search results
   */
  public async searchPapers(
    query: string,
    maxResults: number = 10,
    dateFrom?: string,
    dateTo?: string,
    categories?: string[]
  ): Promise<any[]> {
    try {
      console.log(`Searching ArXiv for: ${query}`);

      // Prepare the request payload
      const payload: any = {
        name: 'search_papers',
        arguments: {
          query,
          max_results: maxResults
        }
      };

      // Add optional parameters if provided
      if (dateFrom) {
        payload.arguments.date_from = dateFrom;
      }

      if (dateTo) {
        payload.arguments.date_to = dateTo;
      }

      if (categories && categories.length > 0) {
        payload.arguments.categories = categories;
      }

      // Call the ArXiv MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      return result.papers;
    } catch (error) {
      console.error('Error searching ArXiv:', error);
      return [];
    }
  }

  /**
   * Download a paper from ArXiv
   * @param paperId ArXiv paper ID
   * @returns Success status
   */
  public async downloadPaper(paperId: string): Promise<boolean> {
    try {
      console.log(`Downloading paper: ${paperId}`);

      // Prepare the request payload
      const payload = {
        name: 'download_paper',
        arguments: {
          paper_id: paperId
        }
      };

      // Call the ArXiv MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Check if the download was successful
      return response.data.content[0].text.includes('successfully downloaded');
    } catch (error) {
      console.error(`Error downloading paper ${paperId}:`, error);
      return false;
    }
  }

  /**
   * List downloaded papers
   * @returns List of downloaded papers
   */
  public async listPapers(): Promise<any[]> {
    try {
      console.log('Listing downloaded papers');

      // Prepare the request payload
      const payload = {
        name: 'list_papers',
        arguments: {}
      };

      // Call the ArXiv MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      return result.papers;
    } catch (error) {
      console.error('Error listing papers:', error);
      return [];
    }
  }

  /**
   * Read a paper from ArXiv
   * @param paperId ArXiv paper ID
   * @returns Paper content
   */
  public async readPaper(paperId: string): Promise<string> {
    try {
      console.log(`Reading paper: ${paperId}`);

      // Prepare the request payload
      const payload = {
        name: 'read_paper',
        arguments: {
          paper_id: paperId
        }
      };

      // Call the ArXiv MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );

      // Return the paper content
      return response.data.content[0].text;
    } catch (error) {
      console.error(`Error reading paper ${paperId}:`, error);
      return '';
    }
  }

  /**
   * Analyze a paper using the deep research analysis prompt
   * @param paperId ArXiv paper ID
   * @returns Analysis of the paper
   */
  public async analyzePaper(paperId: string): Promise<string> {
    try {
      console.log(`Analyzing paper: ${paperId}`);

      // Prepare the request payload
      const payload = {
        name: 'deep-paper-analysis',
        arguments: {
          paper_id: paperId
        }
      };

      // Call the ArXiv MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/get_prompt`,
        payload
      );

      // Return the analysis
      return response.data.content;
    } catch (error) {
      console.error(`Error analyzing paper ${paperId}:`, error);
      return '';
    }
  }

  /**
   * Search for trading strategy papers
   * @param strategyType Type of trading strategy to search for
   * @param maxResults Maximum number of results to return
   * @returns Search results
   */
  public async searchTradingStrategyPapers(
    strategyType: string,
    maxResults: number = 5
  ): Promise<any[]> {
    const query = `"trading strategy" AND "${strategyType}"`;
    const categories = ['q-fin.TR', 'q-fin.PM', 'q-fin.ST'];

    return this.searchPapers(query, maxResults, undefined, undefined, categories);
  }
}
