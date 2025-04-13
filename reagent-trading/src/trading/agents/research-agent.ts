import { Agent } from './agent';
import { ArxivService } from '../../services/arxiv-service';
import { HypothesisGeneratorService } from '../../services/hypothesis-generator-service';

/**
 * Agent responsible for researching trading strategies from academic papers
 */
export class ResearchAgent extends Agent {
  private arxivService: ArxivService;
  private hypothesisGenerator: HypothesisGeneratorService;

  /**
   * Initialize the research agent
   * @param apiKey OpenRouter API key
   * @param useOllamaFallback Whether to use Ollama as a fallback
   */
  constructor(apiKey: string, useOllamaFallback: boolean = true) {
    super();
    this.arxivService = new ArxivService();
    this.hypothesisGenerator = new HypothesisGeneratorService(apiKey, useOllamaFallback);
  }

  /**
   * Execute the research agent to find and analyze papers
   * @param input Input parameters for research
   * @returns Research results
   */
  public async execute(input: any): Promise<any> {
    console.log('Researching academic papers for trading strategies...');

    try {
      // Start the ArXiv MCP server
      await this.arxivService.startServer();

      // Extract parameters from input
      const { query, strategyType, maxResults = 3 } = input;

      // Search for papers
      let papers;
      if (strategyType) {
        papers = await this.arxivService.searchTradingStrategyPapers(strategyType, maxResults);
      } else if (query) {
        papers = await this.arxivService.searchPapers(query, maxResults);
      } else {
        // Default search for trading strategies
        papers = await this.arxivService.searchPapers('"trading strategy" AND "machine learning"', maxResults);
      }

      console.log(`Found ${papers.length} papers`);

      // Download and read papers
      const paperContents = [];
      for (const paper of papers) {
        try {
          // Download the paper
          const downloadSuccess = await this.arxivService.downloadPaper(paper.id);
          
          if (downloadSuccess) {
            // Read the paper content
            const content = await this.arxivService.readPaper(paper.id);
            
            if (content) {
              paperContents.push({
                id: paper.id,
                title: paper.title,
                authors: paper.authors,
                content: content
              });
            }
          }
        } catch (error) {
          console.error(`Error processing paper ${paper.id}:`, error);
        }
      }

      console.log(`Successfully downloaded and read ${paperContents.length} papers`);

      // Generate hypotheses from papers
      const hypotheses = await this.hypothesisGenerator.generateMultipleHypotheses(
        paperContents.map(paper => ({
          content: paper.content,
          title: paper.title,
          authors: paper.authors
        }))
      );

      console.log(`Generated ${hypotheses.length} hypotheses`);

      // Convert hypotheses to strategies
      const strategies = hypotheses.map(hypothesis => 
        this.hypothesisGenerator.convertHypothesisToStrategy(hypothesis)
      );

      return {
        papers: papers,
        strategies: strategies
      };
    } catch (error) {
      console.error('Error in research agent:', error);
      return {
        papers: [],
        strategies: []
      };
    } finally {
      // Stop the ArXiv MCP server
      await this.arxivService.stopServer();
    }
  }

  /**
   * Research a specific paper by ID
   * @param paperId ArXiv paper ID
   * @returns Research results
   */
  public async researchPaper(paperId: string): Promise<any> {
    console.log(`Researching paper: ${paperId}`);

    try {
      // Start the ArXiv MCP server
      await this.arxivService.startServer();

      // Download the paper
      const downloadSuccess = await this.arxivService.downloadPaper(paperId);
      
      if (!downloadSuccess) {
        throw new Error(`Failed to download paper ${paperId}`);
      }

      // Read the paper content
      const content = await this.arxivService.readPaper(paperId);
      
      if (!content) {
        throw new Error(`Failed to read paper ${paperId}`);
      }

      // Get paper metadata
      const papers = await this.arxivService.listPapers();
      const paperMetadata = papers.find(paper => paper.id === paperId);
      
      if (!paperMetadata) {
        throw new Error(`Failed to get metadata for paper ${paperId}`);
      }

      // Generate a hypothesis from the paper
      const hypothesis = await this.hypothesisGenerator.generateHypothesis(
        content,
        paperMetadata.title,
        paperMetadata.authors
      );

      // Convert the hypothesis to a strategy
      const strategy = this.hypothesisGenerator.convertHypothesisToStrategy(hypothesis);

      return {
        paper: {
          id: paperId,
          title: paperMetadata.title,
          authors: paperMetadata.authors,
          content: content
        },
        hypothesis: hypothesis,
        strategy: strategy
      };
    } catch (error) {
      console.error(`Error researching paper ${paperId}:`, error);
      return null;
    } finally {
      // Stop the ArXiv MCP server
      await this.arxivService.stopServer();
    }
  }

  /**
   * Search for papers on ArXiv
   * @param query Search query
   * @param maxResults Maximum number of results to return
   * @returns Search results
   */
  public async searchPapers(query: string, maxResults: number = 10): Promise<any[]> {
    try {
      // Start the ArXiv MCP server
      await this.arxivService.startServer();

      // Search for papers
      return await this.arxivService.searchPapers(query, maxResults);
    } catch (error) {
      console.error('Error searching papers:', error);
      return [];
    } finally {
      // Stop the ArXiv MCP server
      await this.arxivService.stopServer();
    }
  }
}
