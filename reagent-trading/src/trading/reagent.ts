import { BacktestAgent, StrategyGeneratorAgent, StrategyEvaluatorAgent, StrategyOptimizerAgent, WebSearchAgent } from './agents';
import { TradingTargets } from './types';
import { DEFAULT_TRADING_TARGETS } from './config';
import path from 'path';
import { exec } from 'child_process';
import fetch from 'node-fetch';

export class ReAgent {
  private tradingTargets: TradingTargets;
  private backtestAgent: BacktestAgent;
  private strategyGeneratorAgent: StrategyGeneratorAgent;
  private strategyEvaluatorAgent: StrategyEvaluatorAgent;
  private strategyOptimizerAgent: StrategyOptimizerAgent;
  private webSearchAgent: WebSearchAgent;

  constructor(tradingTargets: TradingTargets = DEFAULT_TRADING_TARGETS) {
    this.tradingTargets = tradingTargets;
    this.backtestAgent = new BacktestAgent(this.tradingTargets);
    this.strategyGeneratorAgent = new StrategyGeneratorAgent();
    this.strategyEvaluatorAgent = new StrategyEvaluatorAgent(this.tradingTargets);
    this.strategyOptimizerAgent = new StrategyOptimizerAgent();
    this.webSearchAgent = new WebSearchAgent();
  }

  /**
   * Run the ReAgent system
   */
  public async run(): Promise<void> {
    // Start the browser service for web search
    await this.startBrowserService();

    // Generate initial strategies
    const strategies = await this.strategyGeneratorAgent.generateStrategies();

    console.log('Generated strategies:', strategies);

    // Backtest the strategies
    const backtestResults = await this.backtestAgent.backtestStrategies(strategies);

    console.log('Backtest results:', backtestResults);

    // Evaluate the strategies
    const evaluatedStrategies = await this.strategyEvaluatorAgent.evaluateStrategies(strategies, backtestResults);

    console.log('Evaluated strategies:', evaluatedStrategies);

    // Select the best strategies
    const bestStrategies = evaluatedStrategies
      .filter(strategy => strategy.score >= 0.7)
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);

    console.log('Best strategies:', bestStrategies);

    // Optimize the best strategies
    const optimizedStrategies = await this.strategyOptimizerAgent.optimizeStrategies(bestStrategies);

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