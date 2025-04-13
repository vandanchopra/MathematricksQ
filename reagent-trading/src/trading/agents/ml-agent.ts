import { Agent } from './agent';
import { HuggingfaceService } from '../../services/huggingface-service';
import { YahooFinanceService } from '../../services/yahoo-finance-service';

/**
 * Agent responsible for machine learning tasks
 */
export class MLAgent extends Agent {
  private huggingfaceService: HuggingfaceService;
  private yahooFinanceService: YahooFinanceService;

  /**
   * Initialize the ML agent
   */
  constructor() {
    super();
    this.huggingfaceService = new HuggingfaceService();
    this.yahooFinanceService = new YahooFinanceService();
  }

  /**
   * Execute the ML agent
   * @param input Input parameters for ML tasks
   * @returns ML results
   */
  public async execute(input: any): Promise<any> {
    console.log('Executing ML tasks...');

    try {
      // Start the Huggingface MCP server
      await this.huggingfaceService.startServer();

      // Extract parameters from input
      const { task, data, model, options } = input;

      // Execute the appropriate task
      let result;
      switch (task) {
        case 'sentiment_analysis':
          result = await this.analyzeSentiment(data, model, options);
          break;
        case 'text_classification':
          result = await this.classifyText(data, model, options);
          break;
        case 'text_generation':
          result = await this.generateText(data, model, options);
          break;
        case 'text_summarization':
          result = await this.summarizeText(data, model, options);
          break;
        case 'named_entity_recognition':
          result = await this.extractEntities(data, model, options);
          break;
        case 'question_answering':
          result = await this.answerQuestion(data.question, data.context, model, options);
          break;
        case 'time_series_forecasting':
          result = await this.forecastTimeSeries(data, model, options);
          break;
        case 'anomaly_detection':
          result = await this.detectAnomalies(data, model, options);
          break;
        case 'clustering':
          result = await this.clusterData(data, model, options);
          break;
        case 'feature_extraction':
          result = await this.extractFeatures(data, model, options);
          break;
        default:
          throw new Error(`Unsupported task: ${task}`);
      }

      return {
        task,
        model,
        result
      };
    } catch (error) {
      console.error('Error in ML agent:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Huggingface MCP server
      await this.huggingfaceService.stopServer();
    }
  }

  /**
   * Analyze sentiment of a text
   * @param text Text to analyze
   * @param model Model to use for sentiment analysis
   * @param options Additional options for the model
   * @returns Sentiment analysis results
   */
  public async analyzeSentiment(
    text: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Analyzing sentiment of text: ${text.substring(0, 50)}...`);
    return await this.huggingfaceService.analyzeSentiment(text, model, options);
  }

  /**
   * Classify a text
   * @param text Text to classify
   * @param model Model to use for classification
   * @param options Additional options for the model
   * @returns Classification results
   */
  public async classifyText(
    text: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Classifying text: ${text.substring(0, 50)}...`);
    return await this.huggingfaceService.classifyText(text, model, options);
  }

  /**
   * Generate text
   * @param prompt Prompt for text generation
   * @param model Model to use for generation
   * @param options Additional options for the model
   * @returns Generated text
   */
  public async generateText(
    prompt: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Generating text from prompt: ${prompt.substring(0, 50)}...`);
    return await this.huggingfaceService.generateText(prompt, model, options);
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
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Summarizing text: ${text.substring(0, 50)}...`);
    return await this.huggingfaceService.summarizeText(text, model, options);
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
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Extracting entities from text: ${text.substring(0, 50)}...`);
    return await this.huggingfaceService.extractEntities(text, model, options);
  }

  /**
   * Answer a question
   * @param question Question to answer
   * @param context Context for the question
   * @param model Model to use for question answering
   * @param options Additional options for the model
   * @returns Answer to the question
   */
  public async answerQuestion(
    question: string,
    context: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Answering question: ${question}`);
    return await this.huggingfaceService.answerQuestion(question, context, model, options);
  }

  /**
   * Forecast time series data
   * @param data Time series data
   * @param model Model to use for forecasting
   * @param options Additional options for the model
   * @returns Forecasted values
   */
  public async forecastTimeSeries(
    data: any[],
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Forecasting time series data with ${data.length} points`);
    return await this.huggingfaceService.forecastTimeSeries(data, model, options);
  }

  /**
   * Detect anomalies in time series data
   * @param data Time series data
   * @param model Model to use for anomaly detection
   * @param options Additional options for the model
   * @returns Anomalies in the data
   */
  public async detectAnomalies(
    data: any[],
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Detecting anomalies in time series data with ${data.length} points`);
    return await this.huggingfaceService.detectAnomalies(data, model, options);
  }

  /**
   * Cluster data
   * @param data Data to cluster
   * @param model Model to use for clustering
   * @param options Additional options for the model
   * @returns Clustered data
   */
  public async clusterData(
    data: any[],
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Clustering data with ${data.length} points`);
    return await this.huggingfaceService.clusterData(data, model, options);
  }

  /**
   * Extract features from data
   * @param data Data to extract features from
   * @param model Model to use for feature extraction
   * @param options Additional options for the model
   * @returns Extracted features
   */
  public async extractFeatures(
    data: any[],
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Extracting features from data with ${data.length} points`);
    return await this.huggingfaceService.extractFeatures(data, model, options);
  }

  /**
   * Analyze sentiment of market news
   * @param symbol Stock symbol
   * @param count Number of news articles to analyze
   * @param model Model to use for sentiment analysis
   * @returns Sentiment analysis results
   */
  public async analyzeMarketNewsSentiment(
    symbol: string,
    count: number = 10,
    model?: string
  ): Promise<any> {
    try {
      // Start the Huggingface MCP server
      await this.huggingfaceService.startServer();

      // Get market news for the symbol
      const news = await this.yahooFinanceService.getMarketNews(symbol, count);
      console.log(`Got ${news.length} news articles for ${symbol}`);

      // Analyze sentiment of each news article
      const sentimentResults = [];
      for (const article of news) {
        try {
          // Extract text from the article
          const text = `${article.title}. ${article.summary || ''}`;
          
          // Analyze sentiment
          const sentiment = await this.huggingfaceService.analyzeSentiment(text, model);
          
          // Add to results
          sentimentResults.push({
            article: {
              title: article.title,
              link: article.link,
              publisher: article.publisher,
              publishedAt: article.publishedAt
            },
            sentiment
          });
        } catch (error) {
          console.error(`Error analyzing sentiment for article: ${article.title}`, error);
        }
      }

      // Calculate aggregate sentiment
      const positiveSentiments = sentimentResults.filter(result => 
        result.sentiment.label === 'POSITIVE' || 
        result.sentiment.label === 'positive'
      );
      
      const aggregateSentiment = {
        positive: positiveSentiments.length / sentimentResults.length,
        negative: 1 - (positiveSentiments.length / sentimentResults.length),
        articles: sentimentResults
      };

      return {
        symbol,
        aggregateSentiment,
        articles: sentimentResults
      };
    } catch (error) {
      console.error('Error analyzing market news sentiment:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Huggingface MCP server
      await this.huggingfaceService.stopServer();
    }
  }

  /**
   * Forecast stock prices
   * @param symbol Stock symbol
   * @param period Period of historical data to use
   * @param interval Interval of historical data
   * @param forecastDays Number of days to forecast
   * @param model Model to use for forecasting
   * @returns Forecasted prices
   */
  public async forecastStockPrices(
    symbol: string,
    period: string = '1y',
    interval: string = '1d',
    forecastDays: number = 30,
    model?: string
  ): Promise<any> {
    try {
      // Start the Huggingface MCP server
      await this.huggingfaceService.startServer();

      // Get historical data for the symbol
      const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);
      console.log(`Got ${historicalData.length} historical data points for ${symbol}`);

      // Prepare data for forecasting
      const timeSeriesData = historicalData.map((item: any) => ({
        ds: item.date, // date
        y: item.close // value to forecast
      }));

      // Forecast prices
      const forecastOptions = {
        periods: forecastDays,
        frequency: interval === '1d' ? 'D' : interval === '1wk' ? 'W' : 'M'
      };
      
      const forecast = await this.huggingfaceService.forecastTimeSeries(
        timeSeriesData,
        model,
        forecastOptions
      );

      return {
        symbol,
        historicalData: timeSeriesData,
        forecast
      };
    } catch (error) {
      console.error('Error forecasting stock prices:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Huggingface MCP server
      await this.huggingfaceService.stopServer();
    }
  }

  /**
   * Detect anomalies in stock prices
   * @param symbol Stock symbol
   * @param period Period of historical data to use
   * @param interval Interval of historical data
   * @param model Model to use for anomaly detection
   * @returns Detected anomalies
   */
  public async detectStockAnomalies(
    symbol: string,
    period: string = '1y',
    interval: string = '1d',
    model?: string
  ): Promise<any> {
    try {
      // Start the Huggingface MCP server
      await this.huggingfaceService.startServer();

      // Get historical data for the symbol
      const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);
      console.log(`Got ${historicalData.length} historical data points for ${symbol}`);

      // Prepare data for anomaly detection
      const timeSeriesData = historicalData.map((item: any) => ({
        ds: item.date, // date
        y: item.close // value to analyze
      }));

      // Detect anomalies
      const anomalies = await this.huggingfaceService.detectAnomalies(
        timeSeriesData,
        model
      );

      return {
        symbol,
        historicalData: timeSeriesData,
        anomalies
      };
    } catch (error) {
      console.error('Error detecting stock anomalies:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Huggingface MCP server
      await this.huggingfaceService.stopServer();
    }
  }

  /**
   * Cluster stocks based on their price movements
   * @param symbols Array of stock symbols
   * @param period Period of historical data to use
   * @param interval Interval of historical data
   * @param numClusters Number of clusters to create
   * @param model Model to use for clustering
   * @returns Clustered stocks
   */
  public async clusterStocks(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d',
    numClusters: number = 3,
    model?: string
  ): Promise<any> {
    try {
      // Start the Huggingface MCP server
      await this.huggingfaceService.startServer();

      // Get historical data for each symbol
      const stocksData: Record<string, any[]> = {};
      for (const symbol of symbols) {
        try {
          const historicalData = await this.yahooFinanceService.getHistoricalData(symbol, period, interval);
          console.log(`Got ${historicalData.length} historical data points for ${symbol}`);
          
          // Calculate daily returns
          const returns = [];
          for (let i = 1; i < historicalData.length; i++) {
            const prevClose = historicalData[i - 1].close;
            const currClose = historicalData[i].close;
            returns.push((currClose - prevClose) / prevClose);
          }
          
          stocksData[symbol] = returns;
        } catch (error) {
          console.error(`Error getting data for ${symbol}:`, error);
        }
      }

      // Prepare data for clustering
      const clusteringData = Object.keys(stocksData).map(symbol => ({
        symbol,
        features: stocksData[symbol]
      }));

      // Cluster stocks
      const clusteringOptions = {
        n_clusters: numClusters
      };
      
      const clusters = await this.huggingfaceService.clusterData(
        clusteringData,
        model,
        clusteringOptions
      );

      return {
        symbols,
        clusters
      };
    } catch (error) {
      console.error('Error clustering stocks:', error);
      return {
        error: error instanceof Error ? error.message : String(error)
      };
    } finally {
      // Stop the Huggingface MCP server
      await this.huggingfaceService.stopServer();
    }
  }
}
