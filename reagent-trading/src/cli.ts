import { ReAgent } from './trading/reagent';
import dotenv from 'dotenv';

async function main() {
  // Load environment variables
  dotenv.config();

  const args = process.argv.slice(2);

  // Parse flags
  const flagsObj: { [key: string]: string } = {};
  const nonFlagArgs = [];

  for (const arg of args) {
    if (arg.startsWith('--')) {
      const parts = arg.substring(2).split('=');
      if (parts.length === 2) {
        flagsObj[parts[0]] = parts[1];
      } else {
        flagsObj[parts[0]] = 'true';
      }
    } else {
      nonFlagArgs.push(arg);
    }
  }

  const command = nonFlagArgs[0];

  // Get OpenRouter API key from environment or use the provided one
  const openRouterApiKey = process.env.OPENROUTER_API_KEY || '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';

  // Check if Ollama fallback is enabled
  const useOllamaFallback = flagsObj['use-ollama'] === 'true' || process.env.USE_OLLAMA_FALLBACK === 'true';

  console.log('Using OpenRouter API for enhanced strategy generation and analysis');
  if (useOllamaFallback) {
    console.log('Ollama fallback is enabled - will use local DeepSeek R1 model if OpenRouter fails');
  }

  const reagent = new ReAgent(undefined, openRouterApiKey, useOllamaFallback);

  try {
    if (!command) {
      // Run the full ReAgent system
      console.log('Running the full ReAgent system...');
      await reagent.run();
    } else if (command === 'search') {
      // Search for market information
      const query = nonFlagArgs.slice(1).join(' ');
      if (!query) {
        console.error('Error: Search query is required');
        process.exit(1);
      }

      console.log(`Searching for: ${query}`);
      const results = await reagent.searchMarketInfo(query);

      console.log('Search Results:');
      results.forEach((result, index) => {
        console.log(`\n[${index + 1}] ${result.title}`);
        console.log(`URL: ${result.url}`);
        console.log(`Snippet: ${result.snippet}`);
      });
    } else if (command === 'research') {
      // Research a specific strategy type
      const strategyType = nonFlagArgs.slice(1).join(' ');
      if (!strategyType) {
        console.error('Error: Strategy type is required');
        process.exit(1);
      }

      console.log(`Researching strategy type: ${strategyType}`);
      const strategyInfo = await reagent.researchStrategy(strategyType);

      if (strategyInfo) {
        console.log('\nStrategy Information:');
        console.log(`Type: ${strategyInfo.type}`);
        console.log(`Description: ${strategyInfo.description}`);
        console.log('\nPerformance Metrics:');

        if (strategyInfo.metrics) {
          Object.entries(strategyInfo.metrics).forEach(([key, value]) => {
            console.log(`${key}: ${value}`);
          });
        } else {
          console.log('No performance metrics found');
        }

        console.log(`\nSource: ${strategyInfo.source}`);
      } else {
        console.log('No information found for this strategy type');
      }
    } else if (command === 'research-papers') {
      // Research papers for trading strategies
      const query = nonFlagArgs.slice(1).join(' ');
      if (!query) {
        console.error('Error: Search query is required');
        process.exit(1);
      }

      console.log(`Researching papers for: ${query}`);
      const results = await reagent.researchPapers(query);

      if (results && results.papers) {
        console.log(`\nFound ${results.papers.length} papers:`);
        results.papers.forEach((paper: any, index: number) => {
          console.log(`\n[${index + 1}] ${paper.title}`);
          console.log(`Authors: ${paper.authors.join(', ')}`);
          console.log(`ID: ${paper.id}`);
          console.log(`Published: ${paper.published}`);
          console.log(`Categories: ${paper.categories.join(', ')}`);
        });

        if (results.strategies) {
          console.log(`\nGenerated ${results.strategies.length} strategies from papers:`);
          results.strategies.forEach((strategy: any, index: number) => {
            console.log(`\n[${index + 1}] ${strategy.name}`);
            console.log(`Description: ${strategy.description}`);
            console.log(`Hypothesis: ${strategy.hypothesis}`);
          });
        }

        if (results.optimizedStrategies) {
          console.log(`\nOptimized strategies:`);
          results.optimizedStrategies.forEach((strategy: any, index: number) => {
            console.log(`\n[${index + 1}] ${strategy.name}`);
            console.log(`Description: ${strategy.description}`);
            console.log(`Score: ${strategy.score}`);
          });
        }
      } else {
        console.log('No papers or strategies found');
      }
    } else if (command === 'research-paper') {
      // Research a specific paper by ID
      const paperId = nonFlagArgs.slice(1).join(' ');
      if (!paperId) {
        console.error('Error: Paper ID is required');
        process.exit(1);
      }

      console.log(`Researching paper: ${paperId}`);
      const result = await reagent.researchPaper(paperId);

      if (result && result.paper) {
        console.log(`\nPaper: ${result.paper.title}`);
        console.log(`Authors: ${result.paper.authors.join(', ')}`);
        console.log(`ID: ${result.paper.id}`);

        if (result.strategy) {
          console.log(`\nGenerated Strategy: ${result.strategy.name}`);
          console.log(`Description: ${result.strategy.description}`);
          console.log(`Hypothesis: ${result.strategy.hypothesis}`);

          if (result.evaluatedStrategy) {
            console.log(`\nEvaluation Score: ${result.evaluatedStrategy.score}`);
          }

          if (result.optimizedStrategy) {
            console.log(`\nOptimized Strategy: ${result.optimizedStrategy.name}`);
            console.log(`Description: ${result.optimizedStrategy.description}`);
          }
        }
      } else {
        console.log('Paper not found or could not be analyzed');
      }
    } else if (command === 'search-papers') {
      // Search for papers on ArXiv
      const query = nonFlagArgs.slice(1).join(' ');
      if (!query) {
        console.error('Error: Search query is required');
        process.exit(1);
      }

      console.log(`Searching papers for: ${query}`);
      const papers = await reagent.searchPapers(query);

      if (papers && papers.length > 0) {
        console.log(`\nFound ${papers.length} papers:`);
        papers.forEach((paper: any, index: number) => {
          console.log(`\n[${index + 1}] ${paper.title}`);
          console.log(`Authors: ${paper.authors.join(', ')}`);
          console.log(`ID: ${paper.id}`);
          console.log(`Published: ${paper.published}`);
          console.log(`Categories: ${paper.categories.join(', ')}`);
          console.log(`Abstract: ${paper.abstract.substring(0, 200)}...`);
        });
      } else {
        console.log('No papers found');
      }
    } else if (command === 'search-academic') {
      // Search for academic papers across multiple sources
      const query = nonFlagArgs.slice(1).join(' ');
      if (!query) {
        console.error('Error: Search query is required');
        process.exit(1);
      }

      // Extract sources from flags
      const sources = flagsObj['sources'] ? flagsObj['sources'].split(',') : ['arxiv', 'pubmed', 'semanticscholar'];
      const maxResults = flagsObj['max'] ? parseInt(flagsObj['max']) : 10;

      console.log(`Searching academic papers for: ${query}`);
      console.log(`Sources: ${sources.join(', ')}`);
      const papers = await reagent.searchAcademicPapers(query, maxResults, sources);

      if (papers && papers.length > 0) {
        console.log(`\nFound ${papers.length} papers:`);
        papers.forEach((paper: any, index: number) => {
          console.log(`\n[${index + 1}] ${paper.title}`);
          console.log(`Authors: ${paper.authors.join(', ')}`);
          console.log(`ID: ${paper.id}`);
          console.log(`Source: ${paper.source}`);
          console.log(`Published: ${paper.published || 'N/A'}`);
          if (paper.abstract) {
            console.log(`Abstract: ${paper.abstract.substring(0, 200)}...`);
          }
        });
      } else {
        console.log('No papers found');
      }
    } else if (command === 'research-academic') {
      // Research a specific academic paper
      const paperId = nonFlagArgs[1];
      const source = nonFlagArgs[2] || 'arxiv';

      if (!paperId) {
        console.error('Error: Paper ID is required');
        process.exit(1);
      }

      console.log(`Researching academic paper: ${paperId} from ${source}`);
      const result = await reagent.researchAcademicPaper(paperId, source);

      if (result && result.paper) {
        console.log(`\nPaper: ${result.paper.title}`);
        console.log(`Authors: ${result.paper.authors.join(', ')}`);
        console.log(`ID: ${result.paper.id}`);
        console.log(`Source: ${result.paper.source}`);

        if (result.citations && result.citations.length > 0) {
          console.log(`\nCitations (${result.citations.length}):`);
          result.citations.slice(0, 5).forEach((citation: any, index: number) => {
            console.log(`  [${index + 1}] ${citation.title}`);
          });
          if (result.citations.length > 5) {
            console.log(`  ... and ${result.citations.length - 5} more`);
          }
        }

        if (result.references && result.references.length > 0) {
          console.log(`\nReferences (${result.references.length}):`);
          result.references.slice(0, 5).forEach((reference: any, index: number) => {
            console.log(`  [${index + 1}] ${reference.title}`);
          });
          if (result.references.length > 5) {
            console.log(`  ... and ${result.references.length - 5} more`);
          }
        }

        if (result.strategy) {
          console.log(`\nGenerated Strategy: ${result.strategy.name}`);
          console.log(`Description: ${result.strategy.description}`);
          console.log(`Hypothesis: ${result.strategy.hypothesis}`);
        }
      } else {
        console.log('Paper not found or could not be analyzed');
      }
    } else if (command === 'academic-strategies') {
      // Research trading strategies from academic papers
      const query = nonFlagArgs.slice(1).join(' ');
      if (!query) {
        console.error('Error: Search query is required');
        process.exit(1);
      }

      // Extract sources from flags
      const sources = flagsObj['sources'] ? flagsObj['sources'].split(',') : ['arxiv', 'pubmed', 'semanticscholar'];
      const maxResults = flagsObj['max'] ? parseInt(flagsObj['max']) : 5;

      console.log(`Researching academic strategies for: ${query}`);
      console.log(`Sources: ${sources.join(', ')}`);
      const results = await reagent.researchAcademicStrategies(query, maxResults, sources);

      if (results && results.papers) {
        console.log(`\nFound ${results.papers.length} papers:`);
        results.papers.forEach((paper: any, index: number) => {
          console.log(`\n[${index + 1}] ${paper.title}`);
          console.log(`Authors: ${paper.authors.join(', ')}`);
          console.log(`ID: ${paper.id}`);
          console.log(`Source: ${paper.source}`);
        });

        if (results.strategies) {
          console.log(`\nGenerated ${results.strategies.length} strategies from papers:`);
          results.strategies.forEach((strategy: any, index: number) => {
            console.log(`\n[${index + 1}] ${strategy.name}`);
            console.log(`Description: ${strategy.description}`);
            console.log(`Hypothesis: ${strategy.hypothesis}`);
          });
        }

        if (results.optimizedStrategies) {
          console.log(`\nOptimized strategies:`);
          results.optimizedStrategies.forEach((strategy: any, index: number) => {
            console.log(`\n[${index + 1}] ${strategy.name}`);
            console.log(`Description: ${strategy.description}`);
            console.log(`Score: ${strategy.score}`);
          });
        }
      } else {
        console.log('No papers or strategies found');
      }
    } else if (command === 'stock-quote') {
      // Get stock quote
      const symbol = nonFlagArgs.slice(1).join(' ');
      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Getting stock quote for: ${symbol}`);
      const quote = await reagent.getStockQuote(symbol);

      if (quote) {
        console.log('\nStock Quote:');
        console.log(`Symbol: ${quote.symbol}`);
        console.log(`Price: ${quote.regularMarketPrice}`);
        console.log(`Change: ${quote.regularMarketChange} (${quote.regularMarketChangePercent}%)`);
        console.log(`Previous Close: ${quote.regularMarketPreviousClose}`);
        console.log(`Open: ${quote.regularMarketOpen}`);
        console.log(`Day Range: ${quote.regularMarketDayLow} - ${quote.regularMarketDayHigh}`);
        console.log(`Volume: ${quote.regularMarketVolume}`);
      } else {
        console.log('No quote data found');
      }
    } else if (command === 'historical-data') {
      // Get historical data
      const symbol = nonFlagArgs[1];
      const period = nonFlagArgs[2] || '1y';
      const interval = nonFlagArgs[3] || '1d';

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Getting historical data for: ${symbol}`);
      const data = await reagent.getHistoricalData(symbol, period, interval);

      if (data && data.length > 0) {
        console.log(`\nHistorical Data for ${symbol} (${period}, ${interval}):`);
        console.log(`Found ${data.length} data points`);

        // Display the first 5 and last 5 data points
        const displayCount = Math.min(5, data.length);

        console.log('\nFirst data points:');
        for (let i = 0; i < displayCount; i++) {
          const point = data[i];
          console.log(`${point.date}: Open ${point.open}, High ${point.high}, Low ${point.low}, Close ${point.close}, Volume ${point.volume}`);
        }

        if (data.length > 10) {
          console.log('\n...');

          console.log('\nLast data points:');
          for (let i = data.length - displayCount; i < data.length; i++) {
            const point = data[i];
            console.log(`${point.date}: Open ${point.open}, High ${point.high}, Low ${point.low}, Close ${point.close}, Volume ${point.volume}`);
          }
        }
      } else {
        console.log('No historical data found');
      }
    } else if (command === 'company-info') {
      // Get company information
      const symbol = nonFlagArgs.slice(1).join(' ');
      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Getting company info for: ${symbol}`);
      const info = await reagent.getCompanyInfo(symbol);

      if (info) {
        console.log('\nCompany Information:');
        console.log(`Name: ${info.longName}`);
        console.log(`Symbol: ${info.symbol}`);
        console.log(`Industry: ${info.industry}`);
        console.log(`Sector: ${info.sector}`);
        console.log(`Website: ${info.website}`);
        console.log(`Description: ${info.longBusinessSummary}`);
      } else {
        console.log('No company information found');
      }
    } else if (command === 'market-news') {
      // Get market news
      const category = nonFlagArgs[1] || 'general';
      const count = parseInt(nonFlagArgs[2] || '10');

      console.log(`Getting market news for category: ${category}`);
      const news = await reagent.getMarketNews(category, count);

      if (news && news.length > 0) {
        console.log(`\nMarket News (${category}):`);
        news.forEach((item: any, index: number) => {
          console.log(`\n[${index + 1}] ${item.title}`);
          console.log(`Published: ${item.published}`);
          console.log(`Source: ${item.source}`);
          console.log(`URL: ${item.url}`);
          console.log(`Summary: ${item.summary}`);
        });
      } else {
        console.log('No news found');
      }
    } else if (command === 'search-financial') {
      // Search for financial instruments
      const query = nonFlagArgs.slice(1).join(' ');
      if (!query) {
        console.error('Error: Search query is required');
        process.exit(1);
      }

      console.log(`Searching financial instruments for: ${query}`);
      const results = await reagent.searchFinancial(query);

      if (results && results.length > 0) {
        console.log(`\nSearch Results for "${query}":`);
        results.forEach((item: any, index: number) => {
          console.log(`\n[${index + 1}] ${item.shortname} (${item.symbol})`);
          console.log(`Exchange: ${item.exchange}`);
          console.log(`Type: ${item.typeDisp}`);
          if (item.price) {
            console.log(`Price: ${item.price}`);
          }
        });
      } else {
        console.log('No search results found');
      }
    } else {
      console.error(`Error: Unknown command '${command}'`);
      console.log('\nAvailable commands:');
      console.log('  (no command)  - Run the full ReAgent system');
      console.log('  search <query> - Search for market information');
      console.log('  research <strategy_type> - Research a specific strategy type');
      console.log('\nArXiv Research:');
      console.log('  research-papers <query> - Research trading strategies from academic papers');
      console.log('  research-paper <paper_id> - Research a specific paper by ID');
      console.log('  search-papers <query> - Search for papers on ArXiv');
      console.log('\nAcademic Research:');
      console.log('  search-academic <query> [--sources=arxiv,pubmed,semanticscholar] [--max=10] - Search for academic papers');
      console.log('  research-academic <paper_id> <source> - Research a specific academic paper');
      console.log('  academic-strategies <query> [--sources=arxiv,pubmed,semanticscholar] [--max=5] - Research trading strategies from academic papers');
      console.log('\nFinancial Data:');
      console.log('  stock-quote <symbol> - Get stock quote data');
      console.log('  historical-data <symbol> [period] [interval] - Get historical stock data');
      console.log('  company-info <symbol> - Get company information');
      console.log('  market-news [category] [count] - Get market news');
      console.log('  search-financial <query> - Search for financial instruments');
      process.exit(1);
    }
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});
