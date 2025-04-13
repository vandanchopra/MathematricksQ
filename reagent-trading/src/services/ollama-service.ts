import axios from 'axios';

/**
 * Service for interacting with Ollama API
 */
export class OllamaService {
  private baseUrl: string;
  private model: string;

  /**
   * Initialize the Ollama service
   * @param baseUrl Ollama API base URL
   * @param model Ollama model to use
   */
  constructor(baseUrl: string = 'http://localhost:11434', model: string = 'llama3') {
    this.baseUrl = baseUrl;
    this.model = model;
  }

  /**
   * Generate text using the Ollama API
   * @param prompt The prompt to send to the model
   * @param maxTokens Maximum number of tokens to generate
   * @returns Generated text
   */
  public async generateText(prompt: string, maxTokens: number = 500): Promise<string> {
    try {
      console.log(`Using local Ollama model: ${this.model}`);

      const response = await axios.post(
        `${this.baseUrl}/api/generate`,
        {
          model: this.model,
          prompt: prompt,
          stream: false,
          options: {
            num_predict: maxTokens
          }
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      return response.data.response;
    } catch (error) {
      console.error('Error generating text with Ollama:', error);
      throw error;
    }
  }

  /**
   * Analyze a trading strategy using the Ollama API
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

    const analysis = await this.generateText(prompt);

    return {
      strategy: strategy,
      analysis: analysis
    };
  }

  /**
   * Generate a new trading strategy using the Ollama API
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

      Return only the JSON without any additional text.
    `;

    const generatedText = await this.generateText(prompt);

    try {
      // Extract JSON from the response
      const jsonMatch = generatedText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      } else {
        throw new Error('No valid JSON found in the response');
      }
    } catch (error) {
      console.error('Error parsing generated strategy:', error);
      throw error;
    }
  }

  /**
   * Optimize a trading strategy using the Ollama API
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

      Return only the JSON without any additional text.
    `;

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
    } catch (error) {
      console.error('Error parsing optimized strategy:', error);
      throw error;
    }
  }

  /**
   * Check if Ollama is available
   * @returns True if Ollama is available, false otherwise
   */
  public async isAvailable(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/version`);
      return response.status === 200;
    } catch (error) {
      console.error('Ollama is not available:', error);
      return false;
    }
  }
}
