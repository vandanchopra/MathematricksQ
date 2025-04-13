import { BacktestAgent, StrategyGeneratorAgent, StrategyEvaluatorAgent, StrategyOptimizerAgent, WebSearchAgent } from './agents';
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