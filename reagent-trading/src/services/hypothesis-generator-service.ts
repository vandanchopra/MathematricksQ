import { OpenRouterService } from './openrouter-service';
import { OllamaService } from './ollama-service';

/**
 * Service for generating trading strategy hypotheses based on research papers
 */
export class HypothesisGeneratorService {
  private openRouterService: OpenRouterService;
  private ollamaService: OllamaService;
  private useOllamaFallback: boolean;

  /**
   * Initialize the hypothesis generator service
   * @param apiKey OpenRouter API key
   * @param useOllamaFallback Whether to use Ollama as a fallback
   */
  constructor(apiKey: string, useOllamaFallback: boolean = true) {
    this.openRouterService = new OpenRouterService(apiKey, useOllamaFallback);
    this.ollamaService = new OllamaService();
    this.useOllamaFallback = useOllamaFallback;
  }

  /**
   * Generate a trading strategy hypothesis based on a research paper
   * @param paperContent Content of the research paper
   * @param paperTitle Title of the research paper
   * @param paperAuthors Authors of the research paper
   * @returns Generated hypothesis
   */
  public async generateHypothesis(
    paperContent: string,
    paperTitle: string,
    paperAuthors: string[]
  ): Promise<any> {
    try {
      // Create a prompt for generating a trading strategy hypothesis
      const prompt = this.createHypothesisPrompt(paperContent, paperTitle, paperAuthors);
      
      // Generate the hypothesis using OpenRouter
      const generatedText = await this.openRouterService.generateText(prompt);
      
      // Parse the generated hypothesis
      return this.parseHypothesis(generatedText);
    } catch (error) {
      console.error('Error generating hypothesis:', error);
      
      // Try using Ollama as a fallback
      if (this.useOllamaFallback) {
        try {
          console.log('Falling back to Ollama for hypothesis generation...');
          const prompt = this.createHypothesisPrompt(paperContent, paperTitle, paperAuthors);
          const generatedText = await this.ollamaService.generateText(prompt);
          return this.parseHypothesis(generatedText);
        } catch (ollamaError) {
          console.error('Error generating hypothesis with Ollama:', ollamaError);
          throw new Error('Both OpenRouter and Ollama failed to generate hypothesis');
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Create a prompt for generating a trading strategy hypothesis
   * @param paperContent Content of the research paper
   * @param paperTitle Title of the research paper
   * @param paperAuthors Authors of the research paper
   * @returns Prompt for generating a hypothesis
   */
  private createHypothesisPrompt(
    paperContent: string,
    paperTitle: string,
    paperAuthors: string[]
  ): string {
    // Truncate the paper content if it's too long
    const truncatedContent = paperContent.length > 10000 
      ? paperContent.substring(0, 10000) + '...' 
      : paperContent;
    
    return `
      You are a quantitative finance expert tasked with developing profitable trading strategies based on academic research.
      
      Please analyze the following research paper and generate a detailed trading strategy hypothesis:
      
      Title: ${paperTitle}
      Authors: ${paperAuthors.join(', ')}
      
      Paper Content:
      ${truncatedContent}
      
      Based on this paper, please:
      
      1. Identify the key insights and methodologies that could be applied to trading
      2. Develop a specific, testable trading strategy hypothesis
      3. Define clear entry and exit conditions
      4. Specify the indicators and parameters needed
      5. Suggest risk management rules
      6. Predict expected performance metrics
      
      Format your response as JSON with the following structure:
      {
        "name": "Strategy name based on the paper",
        "description": "Detailed description of the strategy",
        "hypothesis": "The specific, testable hypothesis",
        "keyInsights": ["Key insight 1", "Key insight 2", ...],
        "entryConditions": ["Entry condition 1", "Entry condition 2", ...],
        "exitConditions": ["Exit condition 1", "Exit condition 2", ...],
        "indicators": [
          {"name": "Indicator name", "parameters": {"param1": value1, ...}},
          ...
        ],
        "riskManagement": ["Risk management rule 1", "Risk management rule 2", ...],
        "timeframes": ["Suggested timeframe 1", "Suggested timeframe 2", ...],
        "assetClasses": ["Suggested asset class 1", "Suggested asset class 2", ...],
        "expectedPerformance": {
          "cagr": estimated_cagr,
          "sharpeRatio": estimated_sharpe,
          "maxDrawdown": estimated_max_drawdown,
          "winRate": estimated_win_rate
        },
        "implementationChallenges": ["Challenge 1", "Challenge 2", ...],
        "paperReference": "${paperTitle}"
      }
      
      Return only the JSON without any additional text.
    `;
  }

  /**
   * Parse a generated hypothesis
   * @param generatedText Generated text containing the hypothesis
   * @returns Parsed hypothesis
   */
  private parseHypothesis(generatedText: string): any {
    try {
      // Extract JSON from the response
      const jsonMatch = generatedText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const hypothesis = JSON.parse(jsonMatch[0]);
        
        // Add an ID to the hypothesis
        hypothesis.id = `hypothesis_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
        
        return hypothesis;
      } else {
        throw new Error('No valid JSON found in the response');
      }
    } catch (error) {
      console.error('Error parsing hypothesis:', error);
      throw error;
    }
  }

  /**
   * Generate multiple trading strategy hypotheses based on a set of research papers
   * @param papers Array of papers with content, title, and authors
   * @returns Array of generated hypotheses
   */
  public async generateMultipleHypotheses(
    papers: Array<{ content: string; title: string; authors: string[] }>
  ): Promise<any[]> {
    const hypotheses = [];
    
    for (const paper of papers) {
      try {
        const hypothesis = await this.generateHypothesis(
          paper.content,
          paper.title,
          paper.authors
        );
        
        hypotheses.push(hypothesis);
      } catch (error) {
        console.error(`Error generating hypothesis for paper "${paper.title}":`, error);
        // Continue with the next paper
      }
    }
    
    return hypotheses;
  }

  /**
   * Convert a hypothesis to a trading strategy
   * @param hypothesis The hypothesis to convert
   * @returns Trading strategy
   */
  public convertHypothesisToStrategy(hypothesis: any): any {
    return {
      id: `strategy_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      name: hypothesis.name,
      description: hypothesis.description,
      parameters: hypothesis.indicators.reduce((params: any, indicator: any) => {
        return { ...params, ...indicator.parameters };
      }, {}),
      entryConditions: hypothesis.entryConditions,
      exitConditions: hypothesis.exitConditions,
      riskManagement: hypothesis.riskManagement,
      indicators: hypothesis.indicators,
      timeframes: hypothesis.timeframes,
      expectedPerformance: hypothesis.expectedPerformance,
      paperReference: hypothesis.paperReference,
      hypothesis: hypothesis.hypothesis,
      keyInsights: hypothesis.keyInsights
    };
  }
}
