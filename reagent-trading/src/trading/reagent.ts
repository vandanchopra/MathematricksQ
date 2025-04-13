import { BacktestAgent, StrategyGeneratorAgent, StrategyEvaluatorAgent, StrategyOptimizerAgent, WebSearchAgent, YahooFinanceAgent, AcademicSearchAgent, DataAnalysisAgent, VisualizationAgent, MLAgent, DatabaseAgent, AlphaVantageAgent } from './agents';
import { ResearchAgent } from './agents/research-agent';
import { TradingTargets } from './types';
import { DEFAULT_TRADING_TARGETS } from './config';
import path from 'path';
import { exec } from 'child_process';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

export class ReAgent {
  private tradingTargets: TradingTargets;
  private backtestAgent: BacktestAgent;
  private strategyGeneratorAgent: StrategyGeneratorAgent;
  private strategyEvaluatorAgent: StrategyEvaluatorAgent;
  private strategyOptimizerAgent: StrategyOptimizerAgent;
  private webSearchAgent: WebSearchAgent;
  private researchAgent: ResearchAgent;
  private yahooFinanceAgent: YahooFinanceAgent;
  private academicSearchAgent: AcademicSearchAgent;
  private dataAnalysisAgent: DataAnalysisAgent;
  private visualizationAgent: VisualizationAgent;
  private mlAgent: MLAgent;
  private databaseAgent: DatabaseAgent;
  private alphaVantageAgent: AlphaVantageAgent;
  private openRouterApiKey: string;

  constructor(
    tradingTargets: TradingTargets = DEFAULT_TRADING_TARGETS,
    openRouterApiKey?: string,
    useOllamaFallback: boolean = true
  ) {
    // Load environment variables
    dotenv.config();

    this.tradingTargets = tradingTargets;
    this.openRouterApiKey = openRouterApiKey || process.env.OPENROUTER_API_KEY || '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';

    this.backtestAgent = new BacktestAgent();
    this.strategyGeneratorAgent = new StrategyGeneratorAgent(this.openRouterApiKey, useOllamaFallback);
    this.strategyEvaluatorAgent = new StrategyEvaluatorAgent(this.tradingTargets, this.openRouterApiKey, useOllamaFallback);
    this.strategyOptimizerAgent = new StrategyOptimizerAgent(this.openRouterApiKey, useOllamaFallback);
    this.webSearchAgent = new WebSearchAgent();
    this.researchAgent = new ResearchAgent(this.openRouterApiKey, useOllamaFallback);
    this.yahooFinanceAgent = new YahooFinanceAgent();
    this.academicSearchAgent = new AcademicSearchAgent(this.openRouterApiKey, useOllamaFallback);
    this.dataAnalysisAgent = new DataAnalysisAgent();
    this.visualizationAgent = new VisualizationAgent();
    this.mlAgent = new MLAgent();
    this.databaseAgent = new DatabaseAgent();
    this.alphaVantageAgent = new AlphaVantageAgent(process.env.ALPHA_VANTAGE_API_KEY);
  }

  /**
   * Run the ReAgent system
   */
  public async run(): Promise<void> {
    // Start the browser service for web search
    await this.startBrowserService();

    // Generate initial strategies
    const strategies = await this.strategyGeneratorAgent.execute({});

    console.log('Generated strategies:', strategies);

    // Backtest the strategies
    const backtestResults = await Promise.all(
      strategies.map((strategy: any) => this.backtestAgent.runBacktest(strategy))
    );

    console.log('Backtest results:', backtestResults);

    // Evaluate the strategies
    const evaluatedStrategies = await this.strategyEvaluatorAgent.execute(strategies);

    console.log('Evaluated strategies:', evaluatedStrategies);

    // Select the best strategies
    const bestStrategies = evaluatedStrategies
      .filter((strategy: any) => strategy.score >= 0.7)
      .sort((a: any, b: any) => b.score - a.score)
      .slice(0, 5);

    console.log('Best strategies:', bestStrategies);

    // Optimize the best strategies
    const optimizedStrategies = await this.strategyOptimizerAgent.execute(bestStrategies);

    console.log('Optimized strategies:', optimizedStrategies);

    // Stop the browser service
    await this.stopBrowserService();
  }

  /**
   * Search for trading strategies and market information
   * @param query The search query
   */
  public async searchMarketInfo(query: string): Promise<any[]> {
    // Start the browser service if not already running
    await this.startBrowserService();

    // Search for information
    const results = await this.webSearchAgent.search(query);

    return results;
  }

  /**
   * Research a specific trading strategy type
   * @param strategyType The type of strategy to research
   */
  public async researchStrategy(strategyType: string): Promise<any> {
    // Start the browser service if not already running
    await this.startBrowserService();

    // Search for the strategy
    const strategyInfo = await this.webSearchAgent.searchTradingStrategy(strategyType);

    return strategyInfo;
  }

  /**
   * Research trading strategies from academic papers
   * @param query Search query for finding relevant papers
   * @param maxResults Maximum number of papers to analyze
   */
  public async researchPapers(query: string, maxResults: number = 3): Promise<any> {
    console.log(`Researching papers for: ${query}`);

    // Use the research agent to find and analyze papers
    const researchResults = await this.researchAgent.execute({
      query: query,
      maxResults: maxResults
    });

    // If strategies were generated, evaluate them
    if (researchResults.strategies && researchResults.strategies.length > 0) {
      console.log(`Evaluating ${researchResults.strategies.length} strategies from research papers`);

      // Evaluate the strategies
      const evaluatedStrategies = await this.strategyEvaluatorAgent.execute(researchResults.strategies);

      // Select the best strategies
      const bestStrategies = evaluatedStrategies
        .filter((strategy: any) => strategy.score >= 0.6)
        .sort((a: any, b: any) => b.score - a.score)
        .slice(0, 3);

      // Optimize the best strategies
      const optimizedStrategies = await this.strategyOptimizerAgent.execute(bestStrategies);

      // Add the optimized strategies to the results
      researchResults.evaluatedStrategies = evaluatedStrategies;
      researchResults.bestStrategies = bestStrategies;
      researchResults.optimizedStrategies = optimizedStrategies;
    }

    return researchResults;
  }

  /**
   * Research a specific paper by ID
   * @param paperId ArXiv paper ID
   */
  public async researchPaper(paperId: string): Promise<any> {
    console.log(`Researching paper: ${paperId}`);

    // Use the research agent to analyze the paper
    const researchResult = await this.researchAgent.researchPaper(paperId);

    if (researchResult && researchResult.strategy) {
      // Evaluate the strategy
      const evaluatedStrategy = await this.strategyEvaluatorAgent.execute([researchResult.strategy]);

      // Optimize the strategy if it's good enough
      if (evaluatedStrategy[0].score >= 0.6) {
        const optimizedStrategy = await this.strategyOptimizerAgent.execute([evaluatedStrategy[0]]);

        // Add the evaluated and optimized strategy to the result
        researchResult.evaluatedStrategy = evaluatedStrategy[0];
        researchResult.optimizedStrategy = optimizedStrategy[0];
      } else {
        researchResult.evaluatedStrategy = evaluatedStrategy[0];
      }
    }

    return researchResult;
  }

  /**
   * Search for papers on ArXiv
   * @param query Search query
   * @param maxResults Maximum number of results to return
   */
  public async searchPapers(query: string, maxResults: number = 10): Promise<any[]> {
    console.log(`Searching papers for: ${query}`);

    // Use the research agent to search for papers
    return await this.researchAgent.searchPapers(query, maxResults);
  }

  /**
   * Get stock quote data
   * @param symbol Stock symbol
   */
  public async getStockQuote(symbol: string): Promise<any> {
    console.log(`Getting stock quote for: ${symbol}`);
    return await this.yahooFinanceAgent.getStockQuote(symbol);
  }

  /**
   * Get historical stock data
   * @param symbol Stock symbol
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   */
  public async getHistoricalData(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    console.log(`Getting historical data for: ${symbol}`);
    return await this.yahooFinanceAgent.getHistoricalData(symbol, period, interval);
  }

  /**
   * Get company information
   * @param symbol Stock symbol
   */
  public async getCompanyInfo(symbol: string): Promise<any> {
    console.log(`Getting company info for: ${symbol}`);
    return await this.yahooFinanceAgent.getCompanyInfo(symbol);
  }

  /**
   * Get market news
   * @param category News category (e.g., 'general', 'stocks', 'economy', 'crypto')
   * @param count Number of news items to retrieve
   */
  public async getMarketNews(
    category: string = 'general',
    count: number = 10
  ): Promise<any> {
    console.log(`Getting market news for category: ${category}`);
    return await this.yahooFinanceAgent.getMarketNews(category, count);
  }

  /**
   * Search for financial instruments
   * @param query Search query
   * @param limit Maximum number of results to return
   */
  public async searchFinancial(query: string, limit: number = 10): Promise<any> {
    console.log(`Searching financial instruments for: ${query}`);
    return await this.yahooFinanceAgent.search(query, limit);
  }

  /**
   * Analyze financial data for a specific symbol
   * @param symbol Stock symbol
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   */
  public async analyzeFinancialData(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    console.log(`Analyzing financial data for: ${symbol}`);
    return await this.dataAnalysisAgent.analyzeFinancialData(symbol, period, interval);
  }

  /**
   * Run a custom analysis query on financial data
   * @param symbol Stock symbol
   * @param query Analysis query
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   */
  public async runAnalysisQuery(
    symbol: string,
    query: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    console.log(`Running analysis query for: ${symbol}`);
    return await this.dataAnalysisAgent.runAnalysisQuery(symbol, query, period, interval);
  }

  /**
   * Generate a trading strategy based on financial data analysis
   * @param symbol Stock symbol
   * @param strategyType Type of strategy to generate
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   */
  public async generateDataDrivenStrategy(
    symbol: string,
    strategyType: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    console.log(`Generating ${strategyType} strategy for: ${symbol}`);
    return await this.dataAnalysisAgent.generateTradingStrategy(symbol, strategyType, period, interval);
  }

  /**
   * Compare multiple symbols
   * @param symbols Array of stock symbols
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   */
  public async compareSymbols(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> {
    console.log(`Comparing symbols: ${symbols.join(', ')}`);
    return await this.dataAnalysisAgent.compareSymbols(symbols, period, interval);
  }

  /**
   * Create a chart for a stock
   * @param symbol Stock symbol
   * @param chartType Type of chart to create (e.g., 'line', 'candlestick', 'technical')
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @param title Custom title for the chart
   * @param indicators Technical indicators to include (for technical charts)
   */
  public async createChart(
    symbol: string,
    chartType: string = 'line',
    period: string = '1y',
    interval: string = '1d',
    title?: string,
    indicators: any[] = []
  ): Promise<any> {
    console.log(`Creating ${chartType} chart for: ${symbol}`);
    return await this.visualizationAgent.execute({
      symbol,
      chartType,
      period,
      interval,
      title,
      indicators
    });
  }

  /**
   * Create a price comparison chart for multiple stocks
   * @param symbols Array of stock symbols
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @param title Custom title for the chart
   */
  public async createComparisonChart(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d',
    title?: string
  ): Promise<any> {
    console.log(`Creating comparison chart for: ${symbols.join(', ')}`);
    return await this.visualizationAgent.createComparisonChart(symbols, period, interval, title);
  }

  /**
   * Create a correlation heatmap for multiple stocks
   * @param symbols Array of stock symbols
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @param title Custom title for the chart
   */
  public async createCorrelationHeatmap(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d',
    title?: string
  ): Promise<any> {
    console.log(`Creating correlation heatmap for: ${symbols.join(', ')}`);
    return await this.visualizationAgent.createCorrelationHeatmap(symbols, period, interval, title);
  }

  /**
   * Create a returns distribution histogram
   * @param symbol Stock symbol
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   * @param title Custom title for the chart
   */
  public async createReturnsHistogram(
    symbol: string,
    period: string = '1y',
    interval: string = '1d',
    title?: string
  ): Promise<any> {
    console.log(`Creating returns histogram for: ${symbol}`);
    return await this.visualizationAgent.createReturnsHistogram(symbol, period, interval, title);
  }

  /**
   * Create a backtest results visualization
   * @param backtestResults Backtest results data
   * @param title Custom title for the chart
   */
  public async createBacktestVisualization(
    backtestResults: any,
    title?: string
  ): Promise<any> {
    console.log('Creating backtest visualization');
    return await this.visualizationAgent.createBacktestVisualization(backtestResults, title);
  }

  /**
   * Create a dashboard with multiple charts
   * @param charts Array of charts to include in the dashboard
   * @param title Custom title for the dashboard
   */
  public async createDashboard(
    charts: any[],
    title?: string
  ): Promise<any> {
    console.log('Creating dashboard');
    return await this.visualizationAgent.createDashboard(charts, title);
  }

  /**
   * Analyze sentiment of a text
   * @param text Text to analyze
   * @param model Model to use for sentiment analysis
   * @param options Additional options for the model
   */
  public async analyzeSentiment(
    text: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Analyzing sentiment of text: ${text.substring(0, 50)}...`);
    return await this.mlAgent.analyzeSentiment(text, model, options);
  }

  /**
   * Classify a text
   * @param text Text to classify
   * @param model Model to use for classification
   * @param options Additional options for the model
   */
  public async classifyText(
    text: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Classifying text: ${text.substring(0, 50)}...`);
    return await this.mlAgent.classifyText(text, model, options);
  }

  /**
   * Generate text
   * @param prompt Prompt for text generation
   * @param model Model to use for generation
   * @param options Additional options for the model
   */
  public async generateText(
    prompt: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Generating text from prompt: ${prompt.substring(0, 50)}...`);
    return await this.mlAgent.generateText(prompt, model, options);
  }

  /**
   * Summarize a text
   * @param text Text to summarize
   * @param model Model to use for summarization
   * @param options Additional options for the model
   */
  public async summarizeText(
    text: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Summarizing text: ${text.substring(0, 50)}...`);
    return await this.mlAgent.summarizeText(text, model, options);
  }

  /**
   * Extract named entities from a text
   * @param text Text to analyze
   * @param model Model to use for named entity recognition
   * @param options Additional options for the model
   */
  public async extractEntities(
    text: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Extracting entities from text: ${text.substring(0, 50)}...`);
    return await this.mlAgent.extractEntities(text, model, options);
  }

  /**
   * Answer a question
   * @param question Question to answer
   * @param context Context for the question
   * @param model Model to use for question answering
   * @param options Additional options for the model
   */
  public async answerQuestion(
    question: string,
    context: string,
    model?: string,
    options?: any
  ): Promise<any> {
    console.log(`Answering question: ${question}`);
    return await this.mlAgent.answerQuestion(question, context, model, options);
  }

  /**
   * Analyze sentiment of market news
   * @param symbol Stock symbol
   * @param count Number of news articles to analyze
   * @param model Model to use for sentiment analysis
   */
  public async analyzeMarketNewsSentiment(
    symbol: string,
    count: number = 10,
    model?: string
  ): Promise<any> {
    console.log(`Analyzing market news sentiment for: ${symbol}`);
    return await this.mlAgent.analyzeMarketNewsSentiment(symbol, count, model);
  }

  /**
   * Forecast stock prices
   * @param symbol Stock symbol
   * @param period Period of historical data to use
   * @param interval Interval of historical data
   * @param forecastDays Number of days to forecast
   * @param model Model to use for forecasting
   */
  public async forecastStockPrices(
    symbol: string,
    period: string = '1y',
    interval: string = '1d',
    forecastDays: number = 30,
    model?: string
  ): Promise<any> {
    console.log(`Forecasting stock prices for: ${symbol}`);
    return await this.mlAgent.forecastStockPrices(symbol, period, interval, forecastDays, model);
  }

  /**
   * Detect anomalies in stock prices
   * @param symbol Stock symbol
   * @param period Period of historical data to use
   * @param interval Interval of historical data
   * @param model Model to use for anomaly detection
   */
  public async detectStockAnomalies(
    symbol: string,
    period: string = '1y',
    interval: string = '1d',
    model?: string
  ): Promise<any> {
    console.log(`Detecting anomalies in stock prices for: ${symbol}`);
    return await this.mlAgent.detectStockAnomalies(symbol, period, interval, model);
  }

  /**
   * Cluster stocks based on their price movements
   * @param symbols Array of stock symbols
   * @param period Period of historical data to use
   * @param interval Interval of historical data
   * @param numClusters Number of clusters to create
   * @param model Model to use for clustering
   */
  public async clusterStocks(
    symbols: string[],
    period: string = '1y',
    interval: string = '1d',
    numClusters: number = 3,
    model?: string
  ): Promise<any> {
    console.log(`Clustering stocks: ${symbols.join(', ')}`);
    return await this.mlAgent.clusterStocks(symbols, period, interval, numClusters, model);
  }

  /**
   * Execute a SQL query
   * @param query SQL query to execute
   * @param params Parameters for the query
   */
  public async executeQuery(query: string, params: any[] = []): Promise<any> {
    console.log(`Executing SQL query: ${query.substring(0, 100)}...`);
    return await this.databaseAgent.executeQuery(query, params);
  }

  /**
   * Create a table
   * @param tableName Name of the table to create
   * @param columns Columns for the table
   */
  public async createTable(tableName: string, columns: any[]): Promise<any> {
    console.log(`Creating table: ${tableName}`);
    return await this.databaseAgent.createTable(tableName, columns);
  }

  /**
   * Insert data into a table
   * @param tableName Name of the table to insert into
   * @param data Data to insert
   */
  public async insertData(tableName: string, data: any[]): Promise<any> {
    console.log(`Inserting data into table: ${tableName}`);
    return await this.databaseAgent.insertData(tableName, data);
  }

  /**
   * Update data in a table
   * @param tableName Name of the table to update
   * @param data Data to update
   * @param condition Condition for the update
   */
  public async updateData(tableName: string, data: any, condition: string): Promise<any> {
    console.log(`Updating data in table: ${tableName}`);
    return await this.databaseAgent.updateData(tableName, data, condition);
  }

  /**
   * Delete data from a table
   * @param tableName Name of the table to delete from
   * @param condition Condition for the delete
   */
  public async deleteData(tableName: string, condition: string): Promise<any> {
    console.log(`Deleting data from table: ${tableName}`);
    return await this.databaseAgent.deleteData(tableName, condition);
  }

  /**
   * Get table schema
   * @param tableName Name of the table to get schema for
   */
  public async getTableSchema(tableName: string): Promise<any> {
    console.log(`Getting schema for table: ${tableName}`);
    return await this.databaseAgent.getTableSchema(tableName);
  }

  /**
   * List tables in the database
   */
  public async listTables(): Promise<any> {
    console.log('Listing tables in the database');
    return await this.databaseAgent.listTables();
  }

  /**
   * Import data from a CSV file
   * @param tableName Name of the table to import into
   * @param filePath Path to the CSV file
   * @param options Options for the import
   */
  public async importFromCSV(tableName: string, filePath: string, options: any = {}): Promise<any> {
    console.log(`Importing data from CSV file: ${filePath} into table: ${tableName}`);
    return await this.databaseAgent.importFromCSV(tableName, filePath, options);
  }

  /**
   * Export data to a CSV file
   * @param tableName Name of the table to export from
   * @param filePath Path to the CSV file
   * @param condition Condition for the export
   */
  public async exportToCSV(tableName: string, filePath: string, condition: string = ''): Promise<any> {
    console.log(`Exporting data from table: ${tableName} to CSV file: ${filePath}`);
    return await this.databaseAgent.exportToCSV(tableName, filePath, condition);
  }

  /**
   * Create a database backup
   * @param backupPath Path to the backup file
   */
  public async createBackup(backupPath: string): Promise<any> {
    console.log(`Creating database backup: ${backupPath}`);
    return await this.databaseAgent.createBackup(backupPath);
  }

  /**
   * Restore a database from a backup
   * @param backupPath Path to the backup file
   */
  public async restoreBackup(backupPath: string): Promise<any> {
    console.log(`Restoring database from backup: ${backupPath}`);
    return await this.databaseAgent.restoreBackup(backupPath);
  }

  /**
   * Store historical data for a symbol
   * @param symbol Stock symbol
   * @param period Period (e.g., '1y', '6mo')
   * @param interval Interval (e.g., '1d', '1wk')
   */
  public async storeHistoricalData(symbol: string, period: string = '1y', interval: string = '1d'): Promise<any> {
    console.log(`Storing historical data for: ${symbol}`);
    return await this.databaseAgent.storeHistoricalData(symbol, period, interval);
  }

  /**
   * Get historical data for a symbol from the database
   * @param symbol Stock symbol
   * @param startDate Start date (YYYY-MM-DD)
   * @param endDate End date (YYYY-MM-DD)
   */
  public async getHistoricalDataFromDB(symbol: string, startDate?: string, endDate?: string): Promise<any> {
    console.log(`Getting historical data for: ${symbol} from database`);
    return await this.databaseAgent.getHistoricalData(symbol, startDate, endDate);
  }

  /**
   * Store strategy results
   * @param strategyName Name of the strategy
   * @param symbol Stock symbol
   * @param results Strategy results
   */
  public async storeStrategyResults(strategyName: string, symbol: string, results: any): Promise<any> {
    console.log(`Storing strategy results for: ${strategyName} on ${symbol}`);
    return await this.databaseAgent.storeStrategyResults(strategyName, symbol, results);
  }

  /**
   * Get strategy results
   * @param strategyName Name of the strategy (optional)
   * @param symbol Stock symbol (optional)
   */
  public async getStrategyResults(strategyName?: string, symbol?: string): Promise<any> {
    console.log(`Getting strategy results${strategyName ? ` for: ${strategyName}` : ''}${symbol ? ` on ${symbol}` : ''}`);
    return await this.databaseAgent.getStrategyResults(strategyName, symbol);
  }

  /**
   * Get time series data from Alpha Vantage
   * @param symbol Stock symbol
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   * @param outputSize Output size ('compact' or 'full')
   */
  public async getAlphaVantageTimeSeries(symbol: string, interval: string = 'daily', outputSize: string = 'compact'): Promise<any> {
    console.log(`Getting Alpha Vantage time series data for: ${symbol} (${interval})`);
    return await this.alphaVantageAgent.getTimeSeries(symbol, interval, outputSize);
  }

  /**
   * Get technical indicator data from Alpha Vantage
   * @param symbol Stock symbol
   * @param indicator Technical indicator (e.g., 'SMA', 'EMA', 'MACD', 'RSI', 'BBANDS', 'ADX', 'CCI', 'STOCH')
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   * @param timePeriod Time period
   * @param seriesType Series type (e.g., 'close', 'open', 'high', 'low')
   */
  public async getTechnicalIndicator(
    symbol: string,
    indicator: string,
    interval: string = 'daily',
    timePeriod: number = 14,
    seriesType: string = 'close'
  ): Promise<any> {
    console.log(`Getting ${indicator} data for: ${symbol} (${interval}, period: ${timePeriod})`);
    return await this.alphaVantageAgent.getTechnicalIndicator(symbol, indicator, interval, timePeriod, seriesType);
  }

  /**
   * Get sector performance data from Alpha Vantage
   */
  public async getSectorPerformance(): Promise<any> {
    console.log('Getting sector performance data');
    return await this.alphaVantageAgent.getSectorPerformance();
  }

  /**
   * Get forex data from Alpha Vantage
   * @param fromCurrency From currency
   * @param toCurrency To currency
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   * @param outputSize Output size ('compact' or 'full')
   */
  public async getForexData(
    fromCurrency: string,
    toCurrency: string,
    interval: string = 'daily',
    outputSize: string = 'compact'
  ): Promise<any> {
    console.log(`Getting forex data for: ${fromCurrency}/${toCurrency} (${interval})`);
    return await this.alphaVantageAgent.getForexData(fromCurrency, toCurrency, interval, outputSize);
  }

  /**
   * Get crypto data from Alpha Vantage
   * @param symbol Crypto symbol
   * @param market Market
   * @param interval Interval (e.g., '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly')
   */
  public async getCryptoData(
    symbol: string,
    market: string = 'USD',
    interval: string = 'daily'
  ): Promise<any> {
    console.log(`Getting crypto data for: ${symbol}/${market} (${interval})`);
    return await this.alphaVantageAgent.getCryptoData(symbol, market, interval);
  }

  /**
   * Get economic indicator data from Alpha Vantage
   * @param economicIndicator Economic indicator (e.g., 'REAL_GDP', 'REAL_GDP_PER_CAPITA', 'TREASURY_YIELD', 'FEDERAL_FUNDS_RATE', 'CPI', 'INFLATION', 'RETAIL_SALES', 'DURABLES', 'UNEMPLOYMENT', 'NONFARM_PAYROLL')
   * @param interval Interval (e.g., 'annual', 'quarterly', 'monthly', 'daily')
   * @param maturity Maturity (for treasury yield, e.g., '3month', '5year', '10year', '30year')
   */
  public async getEconomicIndicator(
    economicIndicator: string,
    interval: string = 'monthly',
    maturity: string = ''
  ): Promise<any> {
    console.log(`Getting economic indicator data for: ${economicIndicator} (${interval})`);
    return await this.alphaVantageAgent.getEconomicIndicator(economicIndicator, interval, maturity);
  }

  /**
   * Get company overview from Alpha Vantage
   * @param symbol Stock symbol
   */
  public async getCompanyOverview(symbol: string): Promise<any> {
    console.log(`Getting company overview for: ${symbol}`);
    return await this.alphaVantageAgent.getCompanyOverview(symbol);
  }

  /**
   * Get earnings data from Alpha Vantage
   * @param symbol Stock symbol
   */
  public async getEarnings(symbol: string): Promise<any> {
    console.log(`Getting earnings data for: ${symbol}`);
    return await this.alphaVantageAgent.getEarnings(symbol);
  }

  /**
   * Get income statement from Alpha Vantage
   * @param symbol Stock symbol
   */
  public async getIncomeStatement(symbol: string): Promise<any> {
    console.log(`Getting income statement for: ${symbol}`);
    return await this.alphaVantageAgent.getIncomeStatement(symbol);
  }

  /**
   * Get balance sheet from Alpha Vantage
   * @param symbol Stock symbol
   */
  public async getBalanceSheet(symbol: string): Promise<any> {
    console.log(`Getting balance sheet for: ${symbol}`);
    return await this.alphaVantageAgent.getBalanceSheet(symbol);
  }

  /**
   * Get cash flow from Alpha Vantage
   * @param symbol Stock symbol
   */
  public async getCashFlow(symbol: string): Promise<any> {
    console.log(`Getting cash flow for: ${symbol}`);
    return await this.alphaVantageAgent.getCashFlow(symbol);
  }

  /**
   * Get global market status from Alpha Vantage
   */
  public async getGlobalMarketStatus(): Promise<any> {
    console.log('Getting global market status');
    return await this.alphaVantageAgent.getGlobalMarketStatus();
  }

  /**
   * Search for academic papers across multiple sources
   * @param query Search query
   * @param maxResults Maximum number of results to return
   * @param sources Sources to search (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   */
  public async searchAcademicPapers(
    query: string,
    maxResults: number = 10,
    sources: string[] = ['arxiv', 'pubmed', 'semanticscholar']
  ): Promise<any[]> {
    console.log(`Searching academic papers for: ${query}`);
    return await this.academicSearchAgent.searchPapers(query, maxResults, sources);
  }

  /**
   * Research a specific academic paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   */
  public async researchAcademicPaper(paperId: string, source: string): Promise<any> {
    console.log(`Researching academic paper: ${paperId} from ${source}`);
    return await this.academicSearchAgent.researchPaper(paperId, source);
  }

  /**
   * Get citations for a paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @param maxResults Maximum number of results to return
   */
  public async getCitations(
    paperId: string,
    source: string,
    maxResults: number = 10
  ): Promise<any[]> {
    console.log(`Getting citations for paper: ${paperId} from ${source}`);
    return await this.academicSearchAgent.getCitations(paperId, source, maxResults);
  }

  /**
   * Get references for a paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @param maxResults Maximum number of results to return
   */
  public async getReferences(
    paperId: string,
    source: string,
    maxResults: number = 10
  ): Promise<any[]> {
    console.log(`Getting references for paper: ${paperId} from ${source}`);
    return await this.academicSearchAgent.getReferences(paperId, source, maxResults);
  }

  /**
   * Research trading strategies from academic papers across multiple sources
   * @param query Search query for finding relevant papers
   * @param maxResults Maximum number of papers to analyze
   * @param sources Sources to search (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   */
  public async researchAcademicStrategies(
    query: string,
    maxResults: number = 5,
    sources: string[] = ['arxiv', 'pubmed', 'semanticscholar']
  ): Promise<any> {
    console.log(`Researching academic strategies for: ${query}`);

    // Use the academic search agent to find and analyze papers
    const researchResults = await this.academicSearchAgent.execute({
      query: query,
      maxResults: maxResults,
      sources: sources
    });

    // If strategies were generated, evaluate them
    if (researchResults.strategies && researchResults.strategies.length > 0) {
      console.log(`Evaluating ${researchResults.strategies.length} strategies from academic papers`);

      // Evaluate the strategies
      const evaluatedStrategies = await this.strategyEvaluatorAgent.execute(researchResults.strategies);

      // Select the best strategies
      const bestStrategies = evaluatedStrategies
        .filter((strategy: any) => strategy.score >= 0.6)
        .sort((a: any, b: any) => b.score - a.score)
        .slice(0, 3);

      // Optimize the best strategies
      const optimizedStrategies = await this.strategyOptimizerAgent.execute(bestStrategies);

      // Add the optimized strategies to the results
      researchResults.evaluatedStrategies = evaluatedStrategies;
      researchResults.bestStrategies = bestStrategies;
      researchResults.optimizedStrategies = optimizedStrategies;
    }

    return researchResults;
  }

  /**
   * Start the browser service for web search
   */
  private async startBrowserService(): Promise<void> {
    try {
      console.log('Starting browser service for web search...');
      // Check if the browser service is already running
      const response = await fetch('http://localhost:3000/json/version')
        .then(res => res.json())
        .catch(() => null);

      if (!response) {
        console.log('Browser service not running, starting it...');
        // Start the browser service using docker-compose
        const dockerComposeDir = path.join(process.cwd(), 'docker');
        const startCommand = `cd ${dockerComposeDir} && docker-compose up -d puppeteer`;

        await new Promise<void>((resolve, reject) => {
          exec(startCommand, (error) => {
            if (error) {
              console.error('Failed to start browser service:', error);
              reject(error);
            } else {
              console.log('Browser service started successfully');
              resolve();
            }
          });
        });

        // Wait for the service to be ready
        await new Promise(resolve => setTimeout(resolve, 5000));
      } else {
        console.log('Browser service is already running');
      }
    } catch (error) {
      console.error('Error starting browser service:', error);
    }
  }

  /**
   * Stop the browser service
   */
  private async stopBrowserService(): Promise<void> {
    try {
      console.log('Stopping browser service...');
      // Stop the browser service using docker-compose
      const dockerComposeDir = path.join(process.cwd(), 'docker');
      const stopCommand = `cd ${dockerComposeDir} && docker-compose down`;

      await new Promise<void>((resolve, reject) => {
        exec(stopCommand, (error) => {
          if (error) {
            console.error('Failed to stop browser service:', error);
            reject(error);
          } else {
            console.log('Browser service stopped successfully');
            resolve();
          }
        });
      });
    } catch (error) {
      console.error('Error stopping browser service:', error);
    }
  }
}