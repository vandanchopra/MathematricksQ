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
    } else if (command === 'analyze-data') {
      // Analyze financial data
      const symbol = nonFlagArgs[1];
      const period = nonFlagArgs[2] || '1y';
      const interval = nonFlagArgs[3] || '1d';

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Analyzing financial data for: ${symbol}`);
      const results = await reagent.analyzeFinancialData(symbol, period, interval);

      if (results && !results.error) {
        console.log(`\nAnalysis Results for ${symbol}:`);

        if (results.dataframeInfo) {
          console.log('\nDataFrame Information:');
          console.log(`Columns: ${results.dataframeInfo.columns.join(', ')}`);
          console.log(`Shape: ${results.dataframeInfo.shape[0]} rows, ${results.dataframeInfo.shape[1]} columns`);
        }

        if (results.dataframeStats) {
          console.log('\nDataFrame Statistics:');
          for (const column in results.dataframeStats) {
            console.log(`${column}:`);
            for (const stat in results.dataframeStats[column]) {
              console.log(`  ${stat}: ${results.dataframeStats[column][stat]}`);
            }
          }
        }

        if (results.stockQuote) {
          console.log('\nCurrent Stock Quote:');
          console.log(`Price: ${results.stockQuote.regularMarketPrice}`);
          console.log(`Change: ${results.stockQuote.regularMarketChange} (${results.stockQuote.regularMarketChangePercent}%)`);
        }
      } else {
        console.log('Error analyzing data:', results.error || 'Unknown error');
      }
    } else if (command === 'run-query') {
      // Run a custom analysis query
      const symbol = nonFlagArgs[1];
      const query = nonFlagArgs.slice(2).join(' ');

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      if (!query) {
        console.error('Error: Analysis query is required');
        process.exit(1);
      }

      console.log(`Running analysis query for: ${symbol}`);
      console.log(`Query: ${query}`);
      const results = await reagent.runAnalysisQuery(symbol, query);

      if (results && !results.error) {
        console.log(`\nAnalysis Results for ${symbol}:`);

        if (results.analysisResult) {
          console.log('\nAnalysis Result:');
          console.log(results.analysisResult);
        }
      } else {
        console.log('Error running query:', results.error || 'Unknown error');
      }
    } else if (command === 'generate-data-strategy') {
      // Generate a data-driven trading strategy
      const symbol = nonFlagArgs[1];
      const strategyType = nonFlagArgs[2] || 'momentum';
      const period = nonFlagArgs[3] || '1y';
      const interval = nonFlagArgs[4] || '1d';

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Generating ${strategyType} strategy for: ${symbol}`);
      const results = await reagent.generateDataDrivenStrategy(symbol, strategyType, period, interval);

      if (results && !results.error) {
        console.log(`\nGenerated Strategy for ${symbol}:`);

        if (results.strategy) {
          console.log(`\nStrategy: ${results.strategy.name}`);
          console.log(`Description: ${results.strategy.description}`);

          if (results.strategy.entryConditions) {
            console.log('\nEntry Conditions:');
            results.strategy.entryConditions.forEach((condition: string, index: number) => {
              console.log(`  ${index + 1}. ${condition}`);
            });
          }

          if (results.strategy.exitConditions) {
            console.log('\nExit Conditions:');
            results.strategy.exitConditions.forEach((condition: string, index: number) => {
              console.log(`  ${index + 1}. ${condition}`);
            });
          }

          if (results.strategy.indicators) {
            console.log('\nIndicators:');
            results.strategy.indicators.forEach((indicator: any, index: number) => {
              console.log(`  ${index + 1}. ${indicator.name}`);
              for (const param in indicator.parameters) {
                console.log(`     ${param}: ${indicator.parameters[param]}`);
              }
            });
          }
        }

        if (results.backtestResults) {
          console.log('\nBacktest Results:');
          console.log(`Total Return: ${results.backtestResults.totalReturn}%`);
          console.log(`Annual Return: ${results.backtestResults.annualReturn}%`);
          console.log(`Sharpe Ratio: ${results.backtestResults.sharpeRatio}`);
          console.log(`Max Drawdown: ${results.backtestResults.maxDrawdown}%`);
          console.log(`Win Rate: ${results.backtestResults.winRate}%`);
        }
      } else {
        console.log('Error generating strategy:', results.error || 'Unknown error');
      }
    } else if (command === 'compare-symbols') {
      // Compare multiple symbols
      const symbols = nonFlagArgs.slice(1);
      const period = flagsObj['period'] || '1y';
      const interval = flagsObj['interval'] || '1d';

      if (symbols.length < 2) {
        console.error('Error: At least two stock symbols are required');
        process.exit(1);
      }

      console.log(`Comparing symbols: ${symbols.join(', ')}`);
      const results = await reagent.compareSymbols(symbols, period, interval);

      if (results && !results.error) {
        console.log(`\nComparison Results:`);

        for (const symbol in results.individualResults) {
          const result = results.individualResults[symbol];

          if (!result.error) {
            console.log(`\n${symbol}:`);

            if (result.stockQuote) {
              console.log(`  Current Price: ${result.stockQuote.regularMarketPrice}`);
              console.log(`  Change: ${result.stockQuote.regularMarketChange} (${result.stockQuote.regularMarketChangePercent}%)`);
            }

            if (result.dataframeStats && result.dataframeStats.Close) {
              console.log(`  Mean: ${result.dataframeStats.Close.mean}`);
              console.log(`  Std Dev: ${result.dataframeStats.Close.std}`);
              console.log(`  Min: ${result.dataframeStats.Close.min}`);
              console.log(`  Max: ${result.dataframeStats.Close.max}`);
            }
          } else {
            console.log(`\n${symbol}: Error - ${result.error}`);
          }
        }

        if (results.comparisonAnalysis) {
          console.log('\nComparison Analysis:');
          console.log(results.comparisonAnalysis);
        }
      } else {
        console.log('Error comparing symbols:', results.error || 'Unknown error');
      }
    } else if (command === 'create-chart') {
      // Create a chart for a stock
      const symbol = nonFlagArgs[1];
      const chartType = nonFlagArgs[2] || 'line';
      const period = nonFlagArgs[3] || '1y';
      const interval = nonFlagArgs[4] || '1d';
      const title = flagsObj['title'];

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Creating ${chartType} chart for: ${symbol}`);
      const result = await reagent.createChart(symbol, chartType, period, interval, title);

      if (result && !result.error) {
        console.log(`\nChart created for ${symbol}:`);
        console.log(`Chart URL: ${result.chartUrl}`);
        console.log('\nOpen the URL in your browser to view the chart');
      } else {
        console.log('Error creating chart:', result.error || 'Unknown error');
      }
    } else if (command === 'create-comparison-chart') {
      // Create a price comparison chart for multiple stocks
      const symbols = nonFlagArgs.slice(1);
      const period = flagsObj['period'] || '1y';
      const interval = flagsObj['interval'] || '1d';
      const title = flagsObj['title'];

      if (symbols.length < 2) {
        console.error('Error: At least two stock symbols are required');
        process.exit(1);
      }

      console.log(`Creating comparison chart for: ${symbols.join(', ')}`);
      const result = await reagent.createComparisonChart(symbols, period, interval, title);

      if (result && typeof result === 'string') {
        console.log(`\nComparison chart created:`);
        console.log(`Chart URL: ${result}`);
        console.log('\nOpen the URL in your browser to view the chart');
      } else if (result && result.error) {
        console.log('Error creating comparison chart:', result.error);
      } else {
        console.log('Error creating comparison chart: Unknown error');
      }
    } else if (command === 'create-correlation-heatmap') {
      // Create a correlation heatmap for multiple stocks
      const symbols = nonFlagArgs.slice(1);
      const period = flagsObj['period'] || '1y';
      const interval = flagsObj['interval'] || '1d';
      const title = flagsObj['title'];

      if (symbols.length < 2) {
        console.error('Error: At least two stock symbols are required');
        process.exit(1);
      }

      console.log(`Creating correlation heatmap for: ${symbols.join(', ')}`);
      const result = await reagent.createCorrelationHeatmap(symbols, period, interval, title);

      if (result && typeof result === 'string') {
        console.log(`\nCorrelation heatmap created:`);
        console.log(`Chart URL: ${result}`);
        console.log('\nOpen the URL in your browser to view the chart');
      } else if (result && result.error) {
        console.log('Error creating correlation heatmap:', result.error);
      } else {
        console.log('Error creating correlation heatmap: Unknown error');
      }
    } else if (command === 'create-returns-histogram') {
      // Create a returns distribution histogram
      const symbol = nonFlagArgs[1];
      const period = nonFlagArgs[2] || '1y';
      const interval = nonFlagArgs[3] || '1d';
      const title = flagsObj['title'];

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Creating returns histogram for: ${symbol}`);
      const result = await reagent.createReturnsHistogram(symbol, period, interval, title);

      if (result && typeof result === 'string') {
        console.log(`\nReturns histogram created:`);
        console.log(`Chart URL: ${result}`);
        console.log('\nOpen the URL in your browser to view the chart');
      } else if (result && result.error) {
        console.log('Error creating returns histogram:', result.error);
      } else {
        console.log('Error creating returns histogram: Unknown error');
      }
    } else if (command === 'analyze-sentiment') {
      // Analyze sentiment of a text
      const text = nonFlagArgs.slice(1).join(' ');
      const model = flagsObj['model'];

      if (!text) {
        console.error('Error: Text to analyze is required');
        process.exit(1);
      }

      console.log(`Analyzing sentiment of text: ${text.substring(0, 50)}...`);
      const result = await reagent.analyzeSentiment(text, model);

      if (result && !result.error) {
        console.log(`\nSentiment Analysis Result:`);
        console.log(`Label: ${result.label}`);
        console.log(`Score: ${result.score}`);
      } else {
        console.log('Error analyzing sentiment:', result.error || 'Unknown error');
      }
    } else if (command === 'analyze-news-sentiment') {
      // Analyze sentiment of market news
      const symbol = nonFlagArgs[1];
      const count = flagsObj['count'] ? parseInt(flagsObj['count']) : 10;
      const model = flagsObj['model'];

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Analyzing market news sentiment for: ${symbol}`);
      const result = await reagent.analyzeMarketNewsSentiment(symbol, count, model);

      if (result && !result.error) {
        console.log(`\nMarket News Sentiment Analysis for ${symbol}:`);
        console.log(`Aggregate Sentiment:`);
        console.log(`  Positive: ${(result.aggregateSentiment.positive * 100).toFixed(2)}%`);
        console.log(`  Negative: ${(result.aggregateSentiment.negative * 100).toFixed(2)}%`);

        console.log(`\nAnalyzed Articles:`);
        result.articles.forEach((article: any, index: number) => {
          console.log(`\n[${index + 1}] ${article.article.title}`);
          console.log(`  Publisher: ${article.article.publisher}`);
          console.log(`  Published: ${article.article.publishedAt}`);
          console.log(`  Sentiment: ${article.sentiment.label} (${article.sentiment.score.toFixed(4)})`);
        });
      } else {
        console.log('Error analyzing news sentiment:', result.error || 'Unknown error');
      }
    } else if (command === 'forecast-prices') {
      // Forecast stock prices
      const symbol = nonFlagArgs[1];
      const period = nonFlagArgs[2] || '1y';
      const interval = nonFlagArgs[3] || '1d';
      const forecastDays = flagsObj['days'] ? parseInt(flagsObj['days']) : 30;
      const model = flagsObj['model'];

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Forecasting stock prices for: ${symbol}`);
      const result = await reagent.forecastStockPrices(symbol, period, interval, forecastDays, model);

      if (result && !result.error) {
        console.log(`\nStock Price Forecast for ${symbol}:`);
        console.log(`Forecast Period: ${forecastDays} days`);

        if (result.forecast && result.forecast.forecast) {
          console.log(`\nForecast Results:`);
          console.log(`  Start Date: ${result.forecast.forecast[0].ds}`);
          console.log(`  End Date: ${result.forecast.forecast[result.forecast.forecast.length - 1].ds}`);
          console.log(`  Current Price: ${result.historicalData[result.historicalData.length - 1].y.toFixed(2)}`);
          console.log(`  Forecasted End Price: ${result.forecast.forecast[result.forecast.forecast.length - 1].yhat.toFixed(2)}`);
          console.log(`  Forecasted Change: ${((result.forecast.forecast[result.forecast.forecast.length - 1].yhat - result.historicalData[result.historicalData.length - 1].y) / result.historicalData[result.historicalData.length - 1].y * 100).toFixed(2)}%`);
        }
      } else {
        console.log('Error forecasting prices:', result.error || 'Unknown error');
      }
    } else if (command === 'detect-anomalies') {
      // Detect anomalies in stock prices
      const symbol = nonFlagArgs[1];
      const period = nonFlagArgs[2] || '1y';
      const interval = nonFlagArgs[3] || '1d';
      const model = flagsObj['model'];

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Detecting anomalies in stock prices for: ${symbol}`);
      const result = await reagent.detectStockAnomalies(symbol, period, interval, model);

      if (result && !result.error) {
        console.log(`\nStock Price Anomalies for ${symbol}:`);

        if (result.anomalies && result.anomalies.anomalies) {
          console.log(`\nDetected ${result.anomalies.anomalies.length} anomalies:`);
          result.anomalies.anomalies.forEach((anomaly: any, index: number) => {
            console.log(`\n[${index + 1}] Date: ${anomaly.ds}`);
            console.log(`  Expected: ${anomaly.expected.toFixed(2)}`);
            console.log(`  Actual: ${anomaly.actual.toFixed(2)}`);
            console.log(`  Deviation: ${anomaly.deviation.toFixed(2)}%`);
          });
        } else {
          console.log('No anomalies detected');
        }
      } else {
        console.log('Error detecting anomalies:', result.error || 'Unknown error');
      }
    } else if (command === 'cluster-stocks') {
      // Cluster stocks based on their price movements
      const symbols = nonFlagArgs.slice(1);
      const period = flagsObj['period'] || '1y';
      const interval = flagsObj['interval'] || '1d';
      const numClusters = flagsObj['clusters'] ? parseInt(flagsObj['clusters']) : 3;
      const model = flagsObj['model'];

      if (symbols.length < 2) {
        console.error('Error: At least two stock symbols are required');
        process.exit(1);
      }

      console.log(`Clustering stocks: ${symbols.join(', ')}`);
      const result = await reagent.clusterStocks(symbols, period, interval, numClusters, model);

      if (result && !result.error) {
        console.log(`\nStock Clustering Results:`);

        if (result.clusters && result.clusters.clusters) {
          console.log(`\nIdentified ${Object.keys(result.clusters.clusters).length} clusters:`);

          for (const clusterId in result.clusters.clusters) {
            const cluster = result.clusters.clusters[clusterId];
            console.log(`\nCluster ${clusterId}:`);
            console.log(`  Stocks: ${cluster.map((item: any) => item.symbol).join(', ')}`);
          }
        } else {
          console.log('No clusters identified');
        }
      } else {
        console.log('Error clustering stocks:', result.error || 'Unknown error');
      }
    } else if (command === 'execute-query') {
      // Execute a SQL query
      const query = nonFlagArgs.slice(1).join(' ');
      const params = flagsObj['params'] ? JSON.parse(flagsObj['params']) : [];

      if (!query) {
        console.error('Error: SQL query is required');
        process.exit(1);
      }

      console.log(`Executing SQL query: ${query}`);
      const result = await reagent.executeQuery(query, params);

      if (result && !result.error) {
        console.log(`\nQuery Results:`);
        console.log(result);
      } else {
        console.log('Error executing query:', result.error || 'Unknown error');
      }
    } else if (command === 'list-tables') {
      // List tables in the database
      console.log('Listing tables in the database');
      const result = await reagent.listTables();

      if (result && !result.error) {
        console.log(`\nTables in the database:`);
        result.forEach((table: any, index: number) => {
          console.log(`  ${index + 1}. ${table.table_name}`);
        });
      } else {
        console.log('Error listing tables:', result.error || 'Unknown error');
      }
    } else if (command === 'get-table-schema') {
      // Get table schema
      const tableName = nonFlagArgs[1];

      if (!tableName) {
        console.error('Error: Table name is required');
        process.exit(1);
      }

      console.log(`Getting schema for table: ${tableName}`);
      const result = await reagent.getTableSchema(tableName);

      if (result && !result.error) {
        console.log(`\nSchema for table ${tableName}:`);
        result.forEach((column: any, index: number) => {
          console.log(`  ${index + 1}. ${column.column_name} (${column.data_type})${column.is_nullable === 'NO' ? ' NOT NULL' : ''}${column.column_default ? ` DEFAULT ${column.column_default}` : ''}`);
        });
      } else {
        console.log('Error getting table schema:', result.error || 'Unknown error');
      }
    } else if (command === 'create-table') {
      // Create a table
      const tableName = nonFlagArgs[1];
      const columnsStr = nonFlagArgs.slice(2).join(' ');

      if (!tableName) {
        console.error('Error: Table name is required');
        process.exit(1);
      }

      if (!columnsStr) {
        console.error('Error: Columns definition is required');
        process.exit(1);
      }

      try {
        const columns = JSON.parse(columnsStr);
        console.log(`Creating table: ${tableName}`);
        const result = await reagent.createTable(tableName, columns);

        if (result && !result.error) {
          console.log(`\nTable ${tableName} created successfully`);
        } else {
          console.log('Error creating table:', result.error || 'Unknown error');
        }
      } catch (error) {
        console.error('Error parsing columns JSON:', error);
        process.exit(1);
      }
    } else if (command === 'store-historical-data') {
      // Store historical data for a symbol
      const symbol = nonFlagArgs[1];
      const period = nonFlagArgs[2] || '1y';
      const interval = nonFlagArgs[3] || '1d';

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Storing historical data for: ${symbol}`);
      const result = await reagent.storeHistoricalData(symbol, period, interval);

      if (result && !result.error) {
        console.log(`\nHistorical data for ${symbol} stored successfully`);
        console.log(`  Total points: ${result.totalPoints}`);
        console.log(`  Inserted: ${result.insertedCount}`);
      } else {
        console.log('Error storing historical data:', result.error || 'Unknown error');
      }
    } else if (command === 'get-historical-data-db') {
      // Get historical data for a symbol from the database
      const symbol = nonFlagArgs[1];
      const startDate = flagsObj['start'];
      const endDate = flagsObj['end'];

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      console.log(`Getting historical data for: ${symbol} from database`);
      const result = await reagent.getHistoricalDataFromDB(symbol, startDate, endDate);

      if (result && !result.error) {
        console.log(`\nHistorical data for ${symbol}:`);
        console.log(`  Total points: ${result.length}`);

        if (result.length > 0) {
          console.log(`  First date: ${result[0].date}`);
          console.log(`  Last date: ${result[result.length - 1].date}`);
          console.log(`\nSample data:`);
          result.slice(0, 5).forEach((item: any, index: number) => {
            console.log(`  ${index + 1}. ${item.date}: Open ${item.open}, High ${item.high}, Low ${item.low}, Close ${item.close}, Volume ${item.volume}`);
          });
        }
      } else {
        console.log('Error getting historical data:', result.error || 'Unknown error');
      }
    } else if (command === 'store-strategy-results') {
      // Store strategy results
      const strategyName = nonFlagArgs[1];
      const symbol = nonFlagArgs[2];
      const resultsStr = nonFlagArgs.slice(3).join(' ');

      if (!strategyName) {
        console.error('Error: Strategy name is required');
        process.exit(1);
      }

      if (!symbol) {
        console.error('Error: Stock symbol is required');
        process.exit(1);
      }

      if (!resultsStr) {
        console.error('Error: Strategy results are required');
        process.exit(1);
      }

      try {
        const results = JSON.parse(resultsStr);
        console.log(`Storing strategy results for: ${strategyName} on ${symbol}`);
        const result = await reagent.storeStrategyResults(strategyName, symbol, results);

        if (result && !result.error) {
          console.log(`\nStrategy results stored successfully`);
          console.log(`  Strategy: ${result.strategyName}`);
          console.log(`  Symbol: ${result.symbol}`);
          console.log(`  ID: ${result.strategyResultId}`);
          console.log(`  Trades: ${result.tradeCount}`);
        } else {
          console.log('Error storing strategy results:', result.error || 'Unknown error');
        }
      } catch (error) {
        console.error('Error parsing results JSON:', error);
        process.exit(1);
      }
    } else if (command === 'get-strategy-results') {
      // Get strategy results
      const strategyName = nonFlagArgs[1];
      const symbol = nonFlagArgs[2];

      console.log(`Getting strategy results${strategyName ? ` for: ${strategyName}` : ''}${symbol ? ` on ${symbol}` : ''}`);
      const result = await reagent.getStrategyResults(strategyName, symbol);

      if (result && !result.error) {
        console.log(`\nStrategy Results:`);
        console.log(`  Total results: ${result.length}`);

        if (result.length > 0) {
          result.forEach((item: any, index: number) => {
            console.log(`\n[${index + 1}] ${item.strategy_name} on ${item.symbol}`);
            console.log(`  Period: ${item.start_date} to ${item.end_date}`);
            console.log(`  Total Return: ${item.total_return}%`);
            console.log(`  Annual Return: ${item.annual_return}%`);
            console.log(`  Sharpe Ratio: ${item.sharpe_ratio}`);
            console.log(`  Max Drawdown: ${item.max_drawdown}%`);
            console.log(`  Win Rate: ${item.win_rate}%`);
            console.log(`  Trades: ${item.trade_count}`);
          });
        }
      } else {
        console.log('Error getting strategy results:', result.error || 'Unknown error');
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
      console.log('\nData Analysis:');
      console.log('  analyze-data <symbol> [period] [interval] - Analyze financial data');
      console.log('  run-query <symbol> <query> - Run a custom analysis query');
      console.log('  generate-data-strategy <symbol> [strategy_type] [period] [interval] - Generate a data-driven trading strategy');
      console.log('  compare-symbols <symbol1> <symbol2> [symbol3...] [--period=1y] [--interval=1d] - Compare multiple symbols');
      console.log('\nVisualization:');
      console.log('  create-chart <symbol> [chart_type] [period] [interval] [--title=title] - Create a chart for a stock');
      console.log('  create-comparison-chart <symbol1> <symbol2> [symbol3...] [--period=1y] [--interval=1d] [--title=title] - Create a price comparison chart');
      console.log('  create-correlation-heatmap <symbol1> <symbol2> [symbol3...] [--period=1y] [--interval=1d] [--title=title] - Create a correlation heatmap');
      console.log('  create-returns-histogram <symbol> [period] [interval] [--title=title] - Create a returns distribution histogram');
      console.log('\nMachine Learning:');
      console.log('  analyze-sentiment <text> [--model=model_name] - Analyze sentiment of a text');
      console.log('  analyze-news-sentiment <symbol> [--count=10] [--model=model_name] - Analyze sentiment of market news');
      console.log('  forecast-prices <symbol> [period] [interval] [--days=30] [--model=model_name] - Forecast stock prices');
      console.log('  detect-anomalies <symbol> [period] [interval] [--model=model_name] - Detect anomalies in stock prices');
      console.log('  cluster-stocks <symbol1> <symbol2> [symbol3...] [--period=1y] [--interval=1d] [--clusters=3] [--model=model_name] - Cluster stocks based on price movements');
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
      console.log('  cluster-stocks <symbol1> <symbol2> [symbol3...] [--period=1y] [--interval=1d] [--clusters=3] [--model=model_name] - Cluster stocks based on price movements');
      console.log('\nDatabase:');
      console.log('  execute-query <query> [--params=\'["param1", "param2"]\'] - Execute a SQL query');
      console.log('  list-tables - List tables in the database');
      console.log('  get-table-schema <table_name> - Get table schema');
      console.log('  create-table <table_name> <columns_json> - Create a table');
      console.log('  store-historical-data <symbol> [period] [interval] - Store historical data for a symbol');
      console.log('  get-historical-data-db <symbol> [--start=YYYY-MM-DD] [--end=YYYY-MM-DD] - Get historical data from database');
      console.log('  store-strategy-results <strategy_name> <symbol> <results_json> - Store strategy results');
      console.log('  get-strategy-results [strategy_name] [symbol] - Get strategy results');
      process.exit(1);
