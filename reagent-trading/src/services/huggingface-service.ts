import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * Service for interacting with the Huggingface MCP server
 */
export class HuggingfaceService {
  private serverUrl: string;
  private serverPort: number;
  private cachePath: string;
  private cacheEnabled: boolean;
  private cacheExpiration: number; // in milliseconds
  private serverProcess: any;

  /**
   * Initialize the Huggingface service
   * @param serverUrl URL of the Huggingface MCP server
   * @param serverPort Port of the Huggingface MCP server
   * @param cacheEnabled Whether to enable caching
   * @param cacheExpiration Cache expiration time in seconds
   */
  constructor(
    serverUrl: string = 'http://localhost',
    serverPort: number = 8005,
    cacheEnabled: boolean = true,
    cacheExpiration: number = 3600 // 1 hour
  ) {
    this.serverUrl = serverUrl;
    this.serverPort = serverPort;
    this.cacheEnabled = cacheEnabled;
    this.cacheExpiration = cacheExpiration * 1000; // convert to milliseconds
    
    // Set up cache directory
    this.cachePath = path.join(process.cwd(), 'data', 'huggingface', 'cache');
    if (this.cacheEnabled && !fs.existsSync(this.cachePath)) {
      fs.mkdirSync(this.cachePath, { recursive: true });
    }
  }

  /**
   * Start the Huggingface MCP server
   * @returns Promise that resolves when the server is started
   */
  public async startServer(): Promise<boolean> {
    try {
      console.log('Starting Huggingface MCP server...');
      
      // Check if server is already running
      try {
        const response = await axios.get(`${this.serverUrl}:${this.serverPort}/health`);
        if (response.status === 200) {
          console.log('Huggingface MCP server is already running');
          return true;
        }
      } catch (error) {
        // Server is not running, continue with starting it
      }
      
      // Start the server using Docker
      this.serverProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.huggingface.yml'),
        'up',
        '-d'
      ]);
      
      // Wait for the server to start
      return new Promise((resolve) => {
        this.serverProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Huggingface MCP server started successfully');
            
            // Wait for the server to be ready
            this.waitForServer(10, 1000)
              .then(() => resolve(true))
              .catch(() => resolve(false));
          } else {
            console.error(`Huggingface MCP server failed to start with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error starting Huggingface MCP server:', error);
      return false;
    }
  }

  /**
   * Stop the Huggingface MCP server
   * @returns Promise that resolves when the server is stopped
   */
  public async stopServer(): Promise<boolean> {
    try {
      console.log('Stopping Huggingface MCP server...');
      
      // Stop the server using Docker
      const stopProcess = spawn('docker-compose', [
        '-f',
        path.join(process.cwd(), 'docker', 'docker-compose.huggingface.yml'),
        'down'
      ]);
      
      // Wait for the server to stop
      return new Promise((resolve) => {
        stopProcess.on('close', (code: number) => {
          if (code === 0) {
            console.log('Huggingface MCP server stopped successfully');
            resolve(true);
          } else {
            console.error(`Huggingface MCP server failed to stop with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Error stopping Huggingface MCP server:', error);
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
          console.log('Huggingface MCP server is ready');
          return;
        }
      } catch (error) {
        console.log(`Waiting for Huggingface MCP server to be ready (${i + 1}/${maxRetries})...`);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    throw new Error('Huggingface MCP server failed to start');
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
   * Run text classification on a text
   * @param text Text to classify
   * @param model Model to use for classification
   * @param options Additional options for the model
   * @returns Classification results
   */
  public async classifyText(
    text: string,
    model: string = 'distilbert-base-uncased-finetuned-sst-2-english',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Classifying text using model: ${model}`);
      
      // Create cache key
      const cacheKey = `classify_${model}_${text.substring(0, 50).replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached classification result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'text_classification',
        arguments: {
          text,
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
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
      console.error('Error classifying text:', error);
      throw error;
    }
  }

  /**
   * Generate text using a language model
   * @param prompt Prompt for text generation
   * @param model Model to use for generation
   * @param options Additional options for the model
   * @returns Generated text
   */
  public async generateText(
    prompt: string,
    model: string = 'gpt2',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Generating text using model: ${model}`);
      
      // Create cache key
      const cacheKey = `generate_${model}_${prompt.substring(0, 50).replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached generation result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'text_generation',
        arguments: {
          prompt,
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
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
      console.error('Error generating text:', error);
      throw error;
    }
  }

  /**
   * Summarize a text
   * @param text Text to summarize
   * @param model Model to use for summarization
   * @param options Additional options for the model
   * @returns Summarized text
   */
  public async summarizeText(
    text: string,
    model: string = 'facebook/bart-large-cnn',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Summarizing text using model: ${model}`);
      
      // Create cache key
      const cacheKey = `summarize_${model}_${text.substring(0, 50).replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached summarization result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'text_summarization',
        arguments: {
          text,
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
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
      console.error('Error summarizing text:', error);
      throw error;
    }
  }

  /**
   * Perform sentiment analysis on a text
   * @param text Text to analyze
   * @param model Model to use for sentiment analysis
   * @param options Additional options for the model
   * @returns Sentiment analysis results
   */
  public async analyzeSentiment(
    text: string,
    model: string = 'distilbert-base-uncased-finetuned-sst-2-english',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Analyzing sentiment using model: ${model}`);
      
      // Create cache key
      const cacheKey = `sentiment_${model}_${text.substring(0, 50).replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached sentiment analysis result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'sentiment_analysis',
        arguments: {
          text,
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
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
      console.error('Error analyzing sentiment:', error);
      throw error;
    }
  }

  /**
   * Extract named entities from a text
   * @param text Text to analyze
   * @param model Model to use for named entity recognition
   * @param options Additional options for the model
   * @returns Named entities
   */
  public async extractEntities(
    text: string,
    model: string = 'dbmdz/bert-large-cased-finetuned-conll03-english',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Extracting entities using model: ${model}`);
      
      // Create cache key
      const cacheKey = `entities_${model}_${text.substring(0, 50).replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached entity extraction result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'named_entity_recognition',
        arguments: {
          text,
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
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
      console.error('Error extracting entities:', error);
      throw error;
    }
  }

  /**
   * Perform question answering on a text
   * @param question Question to answer
   * @param context Context for the question
   * @param model Model to use for question answering
   * @param options Additional options for the model
   * @returns Answer to the question
   */
  public async answerQuestion(
    question: string,
    context: string,
    model: string = 'deepset/roberta-base-squad2',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Answering question using model: ${model}`);
      
      // Create cache key
      const cacheKey = `qa_${model}_${question.substring(0, 50).replace(/\s+/g, '_')}`;
      
      // Check cache first if enabled
      if (this.cacheEnabled) {
        const cachedData = this.getFromCache(cacheKey);
        if (cachedData) {
          console.log('Using cached question answering result');
          return cachedData;
        }
      }
      
      // Prepare the request payload
      const payload = {
        name: 'question_answering',
        arguments: {
          question,
          context,
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
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
      console.error('Error answering question:', error);
      throw error;
    }
  }

  /**
   * Perform time series forecasting
   * @param data Time series data
   * @param model Model to use for forecasting
   * @param options Additional options for the model
   * @returns Forecasted values
   */
  public async forecastTimeSeries(
    data: any[],
    model: string = 'facebook/prophet',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Forecasting time series using model: ${model}`);
      
      // Prepare the request payload
      const payload = {
        name: 'time_series_forecasting',
        arguments: {
          data: JSON.stringify(data),
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error forecasting time series:', error);
      throw error;
    }
  }

  /**
   * Perform anomaly detection on time series data
   * @param data Time series data
   * @param model Model to use for anomaly detection
   * @param options Additional options for the model
   * @returns Anomalies in the data
   */
  public async detectAnomalies(
    data: any[],
    model: string = 'facebook/prophet',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Detecting anomalies using model: ${model}`);
      
      // Prepare the request payload
      const payload = {
        name: 'anomaly_detection',
        arguments: {
          data: JSON.stringify(data),
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error detecting anomalies:', error);
      throw error;
    }
  }

  /**
   * Perform clustering on data
   * @param data Data to cluster
   * @param model Model to use for clustering
   * @param options Additional options for the model
   * @returns Clustered data
   */
  public async clusterData(
    data: any[],
    model: string = 'kmeans',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Clustering data using model: ${model}`);
      
      // Prepare the request payload
      const payload = {
        name: 'clustering',
        arguments: {
          data: JSON.stringify(data),
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error clustering data:', error);
      throw error;
    }
  }

  /**
   * Perform feature extraction on data
   * @param data Data to extract features from
   * @param model Model to use for feature extraction
   * @param options Additional options for the model
   * @returns Extracted features
   */
  public async extractFeatures(
    data: any[],
    model: string = 'pca',
    options: any = {}
  ): Promise<any> {
    try {
      console.log(`Extracting features using model: ${model}`);
      
      // Prepare the request payload
      const payload = {
        name: 'feature_extraction',
        arguments: {
          data: JSON.stringify(data),
          model,
          options: JSON.stringify(options)
        }
      };
      
      // Call the Huggingface MCP server
      const response = await axios.post(
        `${this.serverUrl}:${this.serverPort}/call_tool`,
        payload
      );
      
      // Parse the response
      const result = JSON.parse(response.data.content[0].text);
      
      return result;
    } catch (error) {
      console.error('Error extracting features:', error);
      throw error;
    }
  }
}
