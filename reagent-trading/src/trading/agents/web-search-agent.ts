import axios from 'axios';
import puppeteer from 'puppeteer-core';
import { Agent } from './agent';

export class WebSearchAgent extends Agent {
  private browserWSEndpoint: string;

  constructor(browserWSEndpoint: string = 'ws://localhost:3000') {
    super();
    this.browserWSEndpoint = browserWSEndpoint;
  }

  /**
   * Search the web for information related to trading strategies
   * @param query The search query
   * @returns Search results
   */
  public async search(query: string): Promise<any[]> {
    try {
      console.log(`Searching the web for: ${query}`);
      
      // Connect to the browserless Chrome instance
      const browser = await puppeteer.connect({
        browserWSEndpoint: this.browserWSEndpoint,
      });
      
      const page = await browser.newPage();
      await page.setViewport({ width: 1280, height: 800 });
      
      // Go to Google
      await page.goto('https://www.google.com');
      
      // Accept cookies if the dialog appears
      try {
        const acceptButton = await page.waitForSelector('button[id="L2AGLb"]', { timeout: 5000 });
        if (acceptButton) {
          await acceptButton.click();
        }
      } catch (e) {
        // Cookie dialog might not appear, continue
      }
      
      // Type the search query
      await page.type('input[name="q"]', query);
      await page.keyboard.press('Enter');
      
      // Wait for results to load
      await page.waitForSelector('#search');
      
      // Extract search results
      const results = await page.evaluate(() => {
        const searchResults: any[] = [];
        const resultElements = document.querySelectorAll('#search .g');
        
        resultElements.forEach((element) => {
          const titleElement = element.querySelector('h3');
          const linkElement = element.querySelector('a');
          const snippetElement = element.querySelector('.VwiC3b');
          
          if (titleElement && linkElement && snippetElement) {
            searchResults.push({
              title: titleElement.textContent,
              url: linkElement.getAttribute('href'),
              snippet: snippetElement.textContent,
            });
          }
        });
        
        return searchResults;
      });
      
      await browser.disconnect();
      
      console.log(`Found ${results.length} search results`);
      return results;
    } catch (error) {
      console.error('Web search failed:', error);
      return [];
    }
  }

  /**
   * Visit a webpage and extract information
   * @param url The URL to visit
   * @param selector Optional CSS selector to extract specific content
   * @returns Extracted content
   */
  public async extractFromWebpage(url: string, selector?: string): Promise<string> {
    try {
      console.log(`Extracting information from: ${url}`);
      
      // Connect to the browserless Chrome instance
      const browser = await puppeteer.connect({
        browserWSEndpoint: this.browserWSEndpoint,
      });
      
      const page = await browser.newPage();
      await page.setViewport({ width: 1280, height: 800 });
      
      // Go to the URL
      await page.goto(url, { waitUntil: 'networkidle2' });
      
      // Extract content
      let content: string;
      
      if (selector) {
        // Extract specific content if selector is provided
        await page.waitForSelector(selector);
        content = await page.evaluate((sel) => {
          const element = document.querySelector(sel);
          return element ? element.textContent || '' : '';
        }, selector);
      } else {
        // Extract all text content from the page
        content = await page.evaluate(() => {
          return document.body.innerText;
        });
      }
      
      await browser.disconnect();
      
      return content;
    } catch (error) {
      console.error('Web extraction failed:', error);
      return '';
    }
  }

  /**
   * Search for trading strategies and extract relevant information
   * @param strategyType Type of trading strategy to search for
   * @returns Information about the trading strategy
   */
  public async searchTradingStrategy(strategyType: string): Promise<any> {
    try {
      const query = `${strategyType} trading strategy performance metrics`;
      const searchResults = await this.search(query);
      
      if (searchResults.length === 0) {
        return null;
      }
      
      // Visit the first result and extract information
      const firstResult = searchResults[0];
      const content = await this.extractFromWebpage(firstResult.url);
      
      // Parse the content to extract strategy information
      const strategyInfo = this.parseStrategyInformation(content, strategyType);
      
      return {
        ...strategyInfo,
        source: firstResult.url,
        title: firstResult.title,
      };
    } catch (error) {
      console.error('Strategy search failed:', error);
      return null;
    }
  }

  /**
   * Parse extracted content to find strategy information
   * @param content The extracted content
   * @param strategyType The type of strategy
   * @returns Parsed strategy information
   */
  private parseStrategyInformation(content: string, strategyType: string): any {
    // Simple parsing logic - in a real implementation, this would be more sophisticated
    const lines = content.split('\n');
    
    const info: any = {
      type: strategyType,
      metrics: {},
      description: '',
    };
    
    // Look for performance metrics
    for (const line of lines) {
      if (line.toLowerCase().includes('cagr') || line.toLowerCase().includes('annual return')) {
        const match = line.match(/(\d+(\.\d+)?)%/);
        if (match) {
          info.metrics.cagr = parseFloat(match[1]) / 100;
        }
      }
      
      if (line.toLowerCase().includes('sharpe')) {
        const match = line.match(/(\d+(\.\d+)?)/);
        if (match) {
          info.metrics.sharpeRatio = parseFloat(match[1]);
        }
      }
      
      if (line.toLowerCase().includes('drawdown')) {
        const match = line.match(/(\d+(\.\d+)?)%/);
        if (match) {
          info.metrics.maxDrawdown = parseFloat(match[1]) / 100;
        }
      }
      
      // Extract description
      if (line.toLowerCase().includes(strategyType.toLowerCase()) && line.length > 50) {
        info.description = line.trim();
      }
    }
    
    return info;
  }
}
