import { Agent } from './agent';
import { AcademicSearchService } from '../../services/academic-search-service';
import { HypothesisGeneratorService } from '../../services/hypothesis-generator-service';

/**
 * Agent responsible for searching and analyzing academic papers
 */
export class AcademicSearchAgent extends Agent {
  private academicSearchService: AcademicSearchService;
  private hypothesisGenerator: HypothesisGeneratorService;

  /**
   * Initialize the academic search agent
   * @param apiKey OpenRouter API key
   * @param useOllamaFallback Whether to use Ollama as a fallback
   */
  constructor(apiKey: string, useOllamaFallback: boolean = true) {
    super();
    this.academicSearchService = new AcademicSearchService();
    this.hypothesisGenerator = new HypothesisGeneratorService(apiKey, useOllamaFallback);
  }

  /**
   * Execute the academic search agent to find and analyze papers
   * @param input Input parameters for research
   * @returns Research results
   */
  public async execute(input: any): Promise<any> {
    console.log('Searching academic papers for trading strategies...');

    try {
      // Start the Academic Search MCP server
      await this.academicSearchService.startServer();

      // Extract parameters from input
      const { query, strategyType, maxResults = 5, sources = ['arxiv', 'pubmed', 'semanticscholar'] } = input;

      // Search for papers
      let papers;
      if (strategyType) {
        papers = await this.academicSearchService.searchTradingStrategyPapers(strategyType, maxResults, sources);
      } else if (query) {
        papers = await this.academicSearchService.searchPapers(query, maxResults, sources);
      } else {
        // Default search for trading strategies
        papers = await this.academicSearchService.searchPapers('"trading strategy" AND "machine learning"', maxResults, sources);
      }

      console.log(`Found ${papers.length} papers`);

      // Download and read papers
      const paperContents = [];
      for (const paper of papers) {
        try {
          // Get paper details
          const paperDetails = await this.academicSearchService.getPaperDetails(paper.id, paper.source);
          
          if (paperDetails) {
            // Download the paper
            const downloadSuccess = await this.academicSearchService.downloadPaper(paper.id, paper.source);
            
            if (downloadSuccess) {
              // Read the paper content
              const content = await this.academicSearchService.readPaper(paper.id, paper.source);
              
              if (content) {
                paperContents.push({
                  id: paper.id,
                  source: paper.source,
                  title: paperDetails.title,
                  authors: paperDetails.authors,
                  abstract: paperDetails.abstract,
                  content: content
                });
              }
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
        paperDetails: paperContents.map(paper => ({
          id: paper.id,
          source: paper.source,
          title: paper.title,
          authors: paper.authors,
          abstract: paper.abstract
        })),
        strategies: strategies
      };
    } catch (error) {
      console.error('Error in academic search agent:', error);
      return {
        papers: [],
        paperDetails: [],
        strategies: []
      };
    } finally {
      // Stop the Academic Search MCP server
      await this.academicSearchService.stopServer();
    }
  }

  /**
   * Research a specific paper by ID
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @returns Research results
   */
  public async researchPaper(paperId: string, source: string): Promise<any> {
    console.log(`Researching paper: ${paperId} from ${source}`);

    try {
      // Start the Academic Search MCP server
      await this.academicSearchService.startServer();

      // Get paper details
      const paperDetails = await this.academicSearchService.getPaperDetails(paperId, source);
      
      if (!paperDetails) {
        throw new Error(`Failed to get details for paper ${paperId}`);
      }

      // Download the paper
      const downloadSuccess = await this.academicSearchService.downloadPaper(paperId, source);
      
      if (!downloadSuccess) {
        throw new Error(`Failed to download paper ${paperId}`);
      }

      // Read the paper content
      const content = await this.academicSearchService.readPaper(paperId, source);
      
      if (!content) {
        throw new Error(`Failed to read paper ${paperId}`);
      }

      // Get citations and references
      const citations = await this.academicSearchService.getCitations(paperId, source);
      const references = await this.academicSearchService.getReferences(paperId, source);

      // Generate a hypothesis from the paper
      const hypothesis = await this.hypothesisGenerator.generateHypothesis(
        content,
        paperDetails.title,
        paperDetails.authors
      );

      // Convert the hypothesis to a strategy
      const strategy = this.hypothesisGenerator.convertHypothesisToStrategy(hypothesis);

      return {
        paper: {
          id: paperId,
          source: source,
          title: paperDetails.title,
          authors: paperDetails.authors,
          abstract: paperDetails.abstract,
          content: content
        },
        citations: citations,
        references: references,
        hypothesis: hypothesis,
        strategy: strategy
      };
    } catch (error) {
      console.error(`Error researching paper ${paperId}:`, error);
      return null;
    } finally {
      // Stop the Academic Search MCP server
      await this.academicSearchService.stopServer();
    }
  }

  /**
   * Search for papers
   * @param query Search query
   * @param maxResults Maximum number of results to return
   * @param sources Sources to search (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @returns Search results
   */
  public async searchPapers(
    query: string,
    maxResults: number = 10,
    sources: string[] = ['arxiv', 'pubmed', 'semanticscholar']
  ): Promise<any[]> {
    try {
      // Start the Academic Search MCP server
      await this.academicSearchService.startServer();

      // Search for papers
      return await this.academicSearchService.searchPapers(query, maxResults, sources);
    } catch (error) {
      console.error('Error searching papers:', error);
      return [];
    } finally {
      // Stop the Academic Search MCP server
      await this.academicSearchService.stopServer();
    }
  }

  /**
   * Get citations for a paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @param maxResults Maximum number of results to return
   * @returns Citations for the paper
   */
  public async getCitations(
    paperId: string,
    source: string,
    maxResults: number = 10
  ): Promise<any[]> {
    try {
      // Start the Academic Search MCP server
      await this.academicSearchService.startServer();

      // Get citations
      return await this.academicSearchService.getCitations(paperId, source, maxResults);
    } catch (error) {
      console.error('Error getting citations:', error);
      return [];
    } finally {
      // Stop the Academic Search MCP server
      await this.academicSearchService.stopServer();
    }
  }

  /**
   * Get references for a paper
   * @param paperId Paper ID
   * @param source Source of the paper (e.g., 'arxiv', 'pubmed', 'semanticscholar')
   * @param maxResults Maximum number of results to return
   * @returns References for the paper
   */
  public async getReferences(
    paperId: string,
    source: string,
    maxResults: number = 10
  ): Promise<any[]> {
    try {
      // Start the Academic Search MCP server
      await this.academicSearchService.startServer();

      // Get references
      return await this.academicSearchService.getReferences(paperId, source, maxResults);
    } catch (error) {
      console.error('Error getting references:', error);
      return [];
    } finally {
      // Stop the Academic Search MCP server
      await this.academicSearchService.stopServer();
    }
  }
}
