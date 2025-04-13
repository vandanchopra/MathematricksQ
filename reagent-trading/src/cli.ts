import { ReAgent } from './trading/reagent';
import dotenv from 'dotenv';

async function main() {
  // Load environment variables
  dotenv.config();

  const args = process.argv.slice(2);

  // Filter out flags
  const flags = args.filter(arg => arg.startsWith('--'));
  const nonFlagArgs = args.filter(arg => !arg.startsWith('--'));

  const command = nonFlagArgs[0];

  // Get OpenRouter API key from environment or use the provided one
  const openRouterApiKey = process.env.OPENROUTER_API_KEY || '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';

  // Check if Ollama fallback is enabled
  const useOllamaFallback = flags.includes('--use-ollama') || process.env.USE_OLLAMA_FALLBACK === 'true';

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
    } else {
      console.error(`Error: Unknown command '${command}'`);
      console.log('\nAvailable commands:');
      console.log('  (no command)  - Run the full ReAgent system');
      console.log('  search <query> - Search for market information');
      console.log('  research <strategy_type> - Research a specific strategy type');
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
