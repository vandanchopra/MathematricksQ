import axios from 'axios';
import { OllamaService } from './ollama-service';

/**
 * Service for interacting with OpenRouter API
 */
export class OpenRouterService {
  private apiKey: string;
  private baseUrl: string = 'https://openrouter.ai/api/v1';
  private ollamaService: OllamaService;
  private useOllamaFallback: boolean = true;

  /**
   * Initialize the OpenRouter service
   * @param apiKey OpenRouter API key
   * @param useOllamaFallback Whether to use Ollama as a fallback
   */
  constructor(apiKey: string, useOllamaFallback: boolean = true) {
    this.apiKey = apiKey;
    this.useOllamaFallback = useOllamaFallback;
    this.ollamaService = new OllamaService();
  }

  /**
   * Generate text using the OpenRouter API
   * @param prompt The prompt to send to the model
   * @param model The model to use (defaults to Claude)
   * @param maxTokens Maximum number of tokens to generate
   * @returns Generated text
   */
  public async generateText(
    prompt: string,
    model: string = 'google/gemini-pro',
    maxTokens: number = 500
  ): Promise<string> {
    try {
      const response = await axios.post(
        `${this.baseUrl}/chat/completions`,
        {
          model: model,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: maxTokens
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('OpenRouter API Response:', JSON.stringify(response.data, null, 2));

      // Check if the response has the expected structure
      if (response.data &&
          response.data.choices &&
          response.data.choices.length > 0 &&
          response.data.choices[0].message &&
          response.data.choices[0].message.content) {
        return response.data.choices[0].message.content;
      } else {
        console.error('Unexpected API response structure:', response.data);
        throw new Error('Unexpected API response structure');
      }
    } catch (error) {
      console.error('Error generating text with OpenRouter:', error);

      // Try using Ollama as a fallback
      if (this.useOllamaFallback) {
        try {
          console.log('Falling back to Ollama...');
          const isOllamaAvailable = await this.ollamaService.isAvailable();

          if (isOllamaAvailable) {
            return await this.ollamaService.generateText(prompt, maxTokens);
          } else {
            console.error('Ollama is not available');
            throw new Error('Both OpenRouter and Ollama are unavailable');
          }
        } catch (ollamaError) {
          console.error('Error generating text with Ollama:', ollamaError);
          throw new Error('Both OpenRouter and Ollama failed: ' + (error instanceof Error ? error.message : String(error)));
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Analyze a trading strategy using the OpenRouter API
   * @param strategy The strategy to analyze
   * @returns Analysis of the strategy
   */
  public async analyzeStrategy(strategy: any): Promise<any> {
    const prompt = `
      Analyze the following trading strategy and provide insights:

      Strategy Name: ${strategy.name}
      Description: ${strategy.description}
      Parameters: ${JSON.stringify(strategy.parameters)}

      Please provide:
      1. Strengths and weaknesses of this strategy
      2. Market conditions where this strategy would perform well
      3. Market conditions where this strategy might struggle
      4. Suggestions for improving the strategy
      5. Risk management considerations
    `;

    try {
      const analysis = await this.generateText(prompt);

      return {
        strategy: strategy,
        analysis: analysis
      };
    } catch (error) {
      console.error('Error analyzing strategy with OpenRouter:', error);

      // Try using Ollama as a fallback
      if (this.useOllamaFallback) {
        try {
          console.log('Falling back to Ollama for strategy analysis...');
          return await this.ollamaService.analyzeStrategy(strategy);
        } catch (ollamaError) {
          console.error('Error analyzing strategy with Ollama:', ollamaError);
          throw new Error('Both OpenRouter and Ollama failed to analyze strategy');
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Generate a new trading strategy using the OpenRouter API
   * @param type Type of strategy to generate (e.g., "trend-following", "mean-reversion")
   * @param asset Asset class to focus on (e.g., "equities", "forex", "crypto")
   * @returns Generated strategy
   */
  public async generateStrategy(type: string, asset: string): Promise<any> {
    const prompt = `
      Generate a detailed trading strategy with the following characteristics:

      Type: ${type}
      Asset Class: ${asset}

      Please provide:
      1. Strategy name
      2. Detailed description
      3. Entry conditions (specific and quantifiable)
      4. Exit conditions (specific and quantifiable)
      5. Risk management rules
      6. Required indicators and their parameters
      7. Timeframe recommendations
      8. Expected performance metrics

      Format the response as JSON with the following structure:
      {
        "name": "Strategy Name",
        "type": "${type}",
        "assetClass": "${asset}",
        "description": "Detailed description",
        "entryConditions": ["condition1", "condition2"],
        "exitConditions": ["condition1", "condition2"],
        "riskManagement": ["rule1", "rule2"],
        "indicators": [
          {"name": "indicator1", "parameters": {"param1": value1}},
          {"name": "indicator2", "parameters": {"param1": value1}}
        ],
        "timeframes": ["timeframe1", "timeframe2"],
        "expectedPerformance": {
          "cagr": 0.15,
          "sharpeRatio": 1.2,
          "maxDrawdown": 0.12,
          "winRate": 0.55
        }
      }
    `;

    try {
      const generatedText = await this.generateText(prompt);

      try {
        // Extract JSON from the response
        const jsonMatch = generatedText.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[0]);
        } else {
          throw new Error('No valid JSON found in the response');
        }
      } catch (parseError) {
        console.error('Error parsing generated strategy:', parseError);
        throw parseError;
      }
    } catch (error) {
      console.error('Error generating strategy with OpenRouter:', error);

      // Try using Ollama as a fallback
      if (this.useOllamaFallback) {
        try {
          console.log('Falling back to Ollama for strategy generation...');
          return await this.ollamaService.generateStrategy(type, asset);
        } catch (ollamaError) {
          console.error('Error generating strategy with Ollama:', ollamaError);
          throw new Error('Both OpenRouter and Ollama failed to generate strategy');
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Optimize a trading strategy using the OpenRouter API
   * @param strategy The strategy to optimize
   * @param performanceMetrics Current performance metrics
   * @returns Optimized strategy
   */
  public async optimizeStrategy(strategy: any, performanceMetrics: any): Promise<any> {
    const prompt = `
      Optimize the following trading strategy based on its current performance:

      Strategy Name: ${strategy.name}
      Description: ${strategy.description}
      Parameters: ${JSON.stringify(strategy.parameters)}

      Current Performance Metrics:
      CAGR: ${performanceMetrics.cagr}
      Sharpe Ratio: ${performanceMetrics.sharpeRatio}
      Max Drawdown: ${performanceMetrics.maxDrawdown}
      Win Rate: ${performanceMetrics.winRate}

      Please provide:
      1. Optimized parameters
      2. Additional indicators or rules to improve performance
      3. Modified entry/exit conditions
      4. Enhanced risk management rules

      Format the response as JSON with the following structure:
      {
        "name": "${strategy.name}",
        "description": "Updated description",
        "parameters": {
          "param1": value1,
          "param2": value2
        },
        "additionalIndicators": [
          {"name": "indicator1", "parameters": {"param1": value1}}
        ],
        "modifiedEntryConditions": ["condition1", "condition2"],
        "modifiedExitConditions": ["condition1", "condition2"],
        "enhancedRiskManagement": ["rule1", "rule2"]
      }
    `;

    try {
      const generatedText = await this.generateText(prompt);

      try {
        // Extract JSON from the response
        const jsonMatch = generatedText.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const optimizedStrategy = JSON.parse(jsonMatch[0]);
          return {
            ...strategy,
            ...optimizedStrategy,
            isOptimized: true
          };
        } else {
          throw new Error('No valid JSON found in the response');
        }
      } catch (parseError) {
        console.error('Error parsing optimized strategy:', parseError);
        throw parseError;
      }
    } catch (error) {
      console.error('Error optimizing strategy with OpenRouter:', error);

      // Try using Ollama as a fallback
      if (this.useOllamaFallback) {
        try {
          console.log('Falling back to Ollama for strategy optimization...');
          return await this.ollamaService.optimizeStrategy(strategy, performanceMetrics);
        } catch (ollamaError) {
          console.error('Error optimizing strategy with Ollama:', ollamaError);
          throw new Error('Both OpenRouter and Ollama failed to optimize strategy');
        }
      } else {
        throw error;
      }
    }
  }
}
