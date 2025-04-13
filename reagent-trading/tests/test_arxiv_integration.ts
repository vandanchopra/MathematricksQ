import { ArxivService } from '../src/services/arxiv-service';
import { HypothesisGeneratorService } from '../src/services/hypothesis-generator-service';
import { ResearchAgent } from '../src/trading/agents/research-agent';
import { ReAgent } from '../src/trading/reagent';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Get API key from environment
const apiKey = process.env.OPENROUTER_API_KEY || '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';

describe('ArXiv Integration Tests', () => {
  let arxivService: ArxivService;
  
  beforeAll(async () => {
    // Initialize the ArXiv service
    arxivService = new ArxivService();
    
    // Start the ArXiv MCP server
    await arxivService.startServer();
  });
  
  afterAll(async () => {
    // Stop the ArXiv MCP server
    await arxivService.stopServer();
  });
  
  test('Search for papers', async () => {
    // Search for papers
    const papers = await arxivService.searchPapers('trading strategy', 3);
    
    // Check if papers were found
    expect(papers).toBeDefined();
    expect(Array.isArray(papers)).toBe(true);
    
    // If papers were found, check their structure
    if (papers.length > 0) {
      const paper = papers[0];
      expect(paper.id).toBeDefined();
      expect(paper.title).toBeDefined();
      expect(paper.authors).toBeDefined();
      expect(Array.isArray(paper.authors)).toBe(true);
    }
  });
  
  test('Download and read a paper', async () => {
    // Search for papers
    const papers = await arxivService.searchPapers('trading strategy', 1);
    
    // Check if papers were found
    if (papers.length > 0) {
      const paper = papers[0];
      
      // Download the paper
      const downloadSuccess = await arxivService.downloadPaper(paper.id);
      expect(downloadSuccess).toBe(true);
      
      // Read the paper
      const content = await arxivService.readPaper(paper.id);
      expect(content).toBeDefined();
      expect(typeof content).toBe('string');
      expect(content.length).toBeGreaterThan(0);
    }
  });
});

describe('Hypothesis Generator Tests', () => {
  let hypothesisGenerator: HypothesisGeneratorService;
  
  beforeAll(() => {
    // Initialize the hypothesis generator
    hypothesisGenerator = new HypothesisGeneratorService(apiKey, true);
  });
  
  test('Generate a hypothesis', async () => {
    // Sample paper content
    const paperContent = `
      This paper presents a novel trading strategy based on machine learning.
      We use a combination of technical indicators and sentiment analysis to predict market movements.
      Our strategy achieves a Sharpe ratio of 1.5 and an annual return of 15%.
    `;
    
    // Generate a hypothesis
    const hypothesis = await hypothesisGenerator.generateHypothesis(
      paperContent,
      'Novel Trading Strategy Using Machine Learning',
      ['John Doe', 'Jane Smith']
    );
    
    // Check if hypothesis was generated
    expect(hypothesis).toBeDefined();
    expect(hypothesis.name).toBeDefined();
    expect(hypothesis.description).toBeDefined();
    expect(hypothesis.hypothesis).toBeDefined();
    expect(hypothesis.entryConditions).toBeDefined();
    expect(Array.isArray(hypothesis.entryConditions)).toBe(true);
    expect(hypothesis.exitConditions).toBeDefined();
    expect(Array.isArray(hypothesis.exitConditions)).toBe(true);
  });
  
  test('Convert hypothesis to strategy', () => {
    // Sample hypothesis
    const hypothesis = {
      id: 'hypothesis_123',
      name: 'ML-Based Trading Strategy',
      description: 'A trading strategy based on machine learning',
      hypothesis: 'Machine learning can predict market movements',
      keyInsights: ['Insight 1', 'Insight 2'],
      entryConditions: ['Condition 1', 'Condition 2'],
      exitConditions: ['Condition 1', 'Condition 2'],
      indicators: [
        { name: 'RSI', parameters: { period: 14 } },
        { name: 'MACD', parameters: { fast: 12, slow: 26, signal: 9 } }
      ],
      riskManagement: ['Rule 1', 'Rule 2'],
      timeframes: ['1D', '4H'],
      assetClasses: ['equities', 'forex'],
      expectedPerformance: {
        cagr: 0.15,
        sharpeRatio: 1.5,
        maxDrawdown: 0.1,
        winRate: 0.6
      },
      implementationChallenges: ['Challenge 1', 'Challenge 2'],
      paperReference: 'Novel Trading Strategy Using Machine Learning'
    };
    
    // Convert hypothesis to strategy
    const strategy = hypothesisGenerator.convertHypothesisToStrategy(hypothesis);
    
    // Check if strategy was created correctly
    expect(strategy).toBeDefined();
    expect(strategy.name).toBe(hypothesis.name);
    expect(strategy.description).toBe(hypothesis.description);
    expect(strategy.entryConditions).toEqual(hypothesis.entryConditions);
    expect(strategy.exitConditions).toEqual(hypothesis.exitConditions);
    expect(strategy.indicators).toEqual(hypothesis.indicators);
    expect(strategy.riskManagement).toEqual(hypothesis.riskManagement);
    expect(strategy.timeframes).toEqual(hypothesis.timeframes);
    expect(strategy.expectedPerformance).toEqual(hypothesis.expectedPerformance);
    expect(strategy.paperReference).toBe(hypothesis.paperReference);
    expect(strategy.hypothesis).toBe(hypothesis.hypothesis);
    expect(strategy.keyInsights).toEqual(hypothesis.keyInsights);
  });
});

describe('Research Agent Tests', () => {
  let researchAgent: ResearchAgent;
  
  beforeAll(() => {
    // Initialize the research agent
    researchAgent = new ResearchAgent(apiKey, true);
  });
  
  test('Search for papers', async () => {
    // Search for papers
    const papers = await researchAgent.searchPapers('momentum trading', 3);
    
    // Check if papers were found
    expect(papers).toBeDefined();
    expect(Array.isArray(papers)).toBe(true);
  });
});

describe('ReAgent Integration Tests', () => {
  let reagent: ReAgent;
  
  beforeAll(() => {
    // Initialize the ReAgent
    reagent = new ReAgent(undefined, apiKey, true);
  });
  
  test('Search for papers', async () => {
    // Search for papers
    const papers = await reagent.searchPapers('mean reversion', 3);
    
    // Check if papers were found
    expect(papers).toBeDefined();
    expect(Array.isArray(papers)).toBe(true);
  });
});
