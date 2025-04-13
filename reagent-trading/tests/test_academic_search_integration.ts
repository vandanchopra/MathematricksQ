import { AcademicSearchService } from '../src/services/academic-search-service';
import { AcademicSearchAgent } from '../src/trading/agents/academic-search-agent';
import { ReAgent } from '../src/trading/reagent';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Get API key from environment
const apiKey = process.env.OPENROUTER_API_KEY || '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';

describe('Academic Search Service Tests', () => {
  let academicSearchService: AcademicSearchService;
  
  beforeAll(() => {
    // Initialize the Academic Search service with caching disabled for tests
    academicSearchService = new AcademicSearchService('http://localhost', 8002, false);
  });
  
  test('Search for papers', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify([
              {
                id: 'paper1',
                title: 'Test Paper 1',
                authors: ['Author 1', 'Author 2'],
                source: 'arxiv',
                published: '2023-01-01',
                abstract: 'This is a test paper abstract.'
              },
              {
                id: 'paper2',
                title: 'Test Paper 2',
                authors: ['Author 3', 'Author 4'],
                source: 'pubmed',
                published: '2023-02-01',
                abstract: 'This is another test paper abstract.'
              }
            ])
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Search for papers
    const papers = await academicSearchService.searchPapers('test query', 2, ['arxiv', 'pubmed']);
    
    // Check if papers were found
    expect(papers).toBeDefined();
    expect(Array.isArray(papers)).toBe(true);
    expect(papers.length).toBe(2);
    
    // Check paper structure
    expect(papers[0].id).toBe('paper1');
    expect(papers[0].title).toBe('Test Paper 1');
    expect(papers[0].source).toBe('arxiv');
    expect(papers[1].id).toBe('paper2');
    expect(papers[1].title).toBe('Test Paper 2');
    expect(papers[1].source).toBe('pubmed');
  });
  
  test('Get paper details', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify({
              id: 'paper1',
              title: 'Test Paper 1',
              authors: ['Author 1', 'Author 2'],
              source: 'arxiv',
              published: '2023-01-01',
              abstract: 'This is a test paper abstract.',
              url: 'https://example.com/paper1'
            })
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Get paper details
    const paperDetails = await academicSearchService.getPaperDetails('paper1', 'arxiv');
    
    // Check if paper details were retrieved
    expect(paperDetails).toBeDefined();
    expect(paperDetails.id).toBe('paper1');
    expect(paperDetails.title).toBe('Test Paper 1');
    expect(paperDetails.authors).toEqual(['Author 1', 'Author 2']);
    expect(paperDetails.source).toBe('arxiv');
    expect(paperDetails.abstract).toBe('This is a test paper abstract.');
  });
  
  test('Get citations', async () => {
    // Mock the axios post method
    const mockResponse = {
      data: {
        content: [
          {
            text: JSON.stringify([
              {
                id: 'citation1',
                title: 'Citation Paper 1',
                authors: ['Author 5', 'Author 6'],
                source: 'arxiv',
                published: '2023-03-01'
              },
              {
                id: 'citation2',
                title: 'Citation Paper 2',
                authors: ['Author 7', 'Author 8'],
                source: 'pubmed',
                published: '2023-04-01'
              }
            ])
          }
        ]
      }
    };
    
    // @ts-ignore
    global.axios = {
      post: jest.fn().mockResolvedValue(mockResponse)
    };
    
    // Get citations
    const citations = await academicSearchService.getCitations('paper1', 'arxiv', 2);
    
    // Check if citations were retrieved
    expect(citations).toBeDefined();
    expect(Array.isArray(citations)).toBe(true);
    expect(citations.length).toBe(2);
    
    // Check citation structure
    expect(citations[0].id).toBe('citation1');
    expect(citations[0].title).toBe('Citation Paper 1');
    expect(citations[1].id).toBe('citation2');
    expect(citations[1].title).toBe('Citation Paper 2');
  });
});

describe('Academic Search Agent Tests', () => {
  let academicSearchAgent: AcademicSearchAgent;
  
  beforeAll(() => {
    // Initialize the Academic Search agent
    academicSearchAgent = new AcademicSearchAgent(apiKey, true);
    
    // Mock the AcademicSearchService methods
    academicSearchAgent['academicSearchService'] = {
      startServer: jest.fn().mockResolvedValue(true),
      stopServer: jest.fn().mockResolvedValue(true),
      searchPapers: jest.fn().mockResolvedValue([
        {
          id: 'paper1',
          title: 'Test Paper 1',
          authors: ['Author 1', 'Author 2'],
          source: 'arxiv',
          published: '2023-01-01',
          abstract: 'This is a test paper abstract.'
        }
      ]),
      getPaperDetails: jest.fn().mockResolvedValue({
        id: 'paper1',
        title: 'Test Paper 1',
        authors: ['Author 1', 'Author 2'],
        source: 'arxiv',
        published: '2023-01-01',
        abstract: 'This is a test paper abstract.'
      }),
      downloadPaper: jest.fn().mockResolvedValue(true),
      readPaper: jest.fn().mockResolvedValue('This is the content of the paper.'),
      getCitations: jest.fn().mockResolvedValue([
        {
          id: 'citation1',
          title: 'Citation Paper 1',
          authors: ['Author 5', 'Author 6'],
          source: 'arxiv',
          published: '2023-03-01'
        }
      ]),
      getReferences: jest.fn().mockResolvedValue([
        {
          id: 'reference1',
          title: 'Reference Paper 1',
          authors: ['Author 9', 'Author 10'],
          source: 'arxiv',
          published: '2023-05-01'
        }
      ])
    } as any;
    
    // Mock the HypothesisGeneratorService methods
    academicSearchAgent['hypothesisGenerator'] = {
      generateHypothesis: jest.fn().mockResolvedValue({
        id: 'hypothesis_123',
        name: 'Test Hypothesis',
        description: 'This is a test hypothesis.',
        hypothesis: 'This is the hypothesis statement.',
        entryConditions: ['Condition 1', 'Condition 2'],
        exitConditions: ['Condition 3', 'Condition 4'],
        indicators: [{ name: 'RSI', parameters: { period: 14 } }],
        riskManagement: ['Rule 1', 'Rule 2'],
        timeframes: ['1D', '4H'],
        expectedPerformance: { cagr: 0.15, sharpeRatio: 1.5 }
      }),
      generateMultipleHypotheses: jest.fn().mockResolvedValue([
        {
          id: 'hypothesis_123',
          name: 'Test Hypothesis',
          description: 'This is a test hypothesis.',
          hypothesis: 'This is the hypothesis statement.',
          entryConditions: ['Condition 1', 'Condition 2'],
          exitConditions: ['Condition 3', 'Condition 4'],
          indicators: [{ name: 'RSI', parameters: { period: 14 } }],
          riskManagement: ['Rule 1', 'Rule 2'],
          timeframes: ['1D', '4H'],
          expectedPerformance: { cagr: 0.15, sharpeRatio: 1.5 }
        }
      ]),
      convertHypothesisToStrategy: jest.fn().mockImplementation((hypothesis) => ({
        id: 'strategy_123',
        name: hypothesis.name,
        description: hypothesis.description,
        hypothesis: hypothesis.hypothesis,
        entryConditions: hypothesis.entryConditions,
        exitConditions: hypothesis.exitConditions,
        indicators: hypothesis.indicators,
        riskManagement: hypothesis.riskManagement,
        timeframes: hypothesis.timeframes,
        expectedPerformance: hypothesis.expectedPerformance
      }))
    } as any;
  });
  
  test('Search for papers', async () => {
    // Search for papers
    const papers = await academicSearchAgent.searchPapers('test query', 2, ['arxiv', 'pubmed']);
    
    // Check if papers were found
    expect(papers).toBeDefined();
    expect(Array.isArray(papers)).toBe(true);
    
    // Check if service method was called
    expect(academicSearchAgent['academicSearchService'].searchPapers).toHaveBeenCalledWith('test query', 2, ['arxiv', 'pubmed']);
  });
  
  test('Research a paper', async () => {
    // Research a paper
    const result = await academicSearchAgent.researchPaper('paper1', 'arxiv');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.paper).toBeDefined();
    expect(result.paper.id).toBe('paper1');
    expect(result.paper.title).toBe('Test Paper 1');
    expect(result.citations).toBeDefined();
    expect(result.references).toBeDefined();
    expect(result.hypothesis).toBeDefined();
    expect(result.strategy).toBeDefined();
    
    // Check if service methods were called
    expect(academicSearchAgent['academicSearchService'].getPaperDetails).toHaveBeenCalledWith('paper1', 'arxiv');
    expect(academicSearchAgent['academicSearchService'].downloadPaper).toHaveBeenCalledWith('paper1', 'arxiv');
    expect(academicSearchAgent['academicSearchService'].readPaper).toHaveBeenCalledWith('paper1', 'arxiv');
    expect(academicSearchAgent['academicSearchService'].getCitations).toHaveBeenCalledWith('paper1', 'arxiv');
    expect(academicSearchAgent['academicSearchService'].getReferences).toHaveBeenCalledWith('paper1', 'arxiv');
  });
  
  test('Execute agent', async () => {
    // Execute the agent
    const result = await academicSearchAgent.execute({
      query: 'test query',
      maxResults: 2,
      sources: ['arxiv', 'pubmed']
    });
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.papers).toBeDefined();
    expect(Array.isArray(result.papers)).toBe(true);
    expect(result.strategies).toBeDefined();
    expect(Array.isArray(result.strategies)).toBe(true);
    
    // Check if service methods were called
    expect(academicSearchAgent['academicSearchService'].searchPapers).toHaveBeenCalled();
    expect(academicSearchAgent['hypothesisGenerator'].generateMultipleHypotheses).toHaveBeenCalled();
    expect(academicSearchAgent['hypothesisGenerator'].convertHypothesisToStrategy).toHaveBeenCalled();
  });
});

describe('ReAgent Integration Tests', () => {
  let reagent: ReAgent;
  
  beforeAll(() => {
    // Initialize the ReAgent
    reagent = new ReAgent(undefined, apiKey, true);
    
    // Mock the AcademicSearchAgent methods
    reagent['academicSearchAgent'] = {
      searchPapers: jest.fn().mockResolvedValue([
        {
          id: 'paper1',
          title: 'Test Paper 1',
          authors: ['Author 1', 'Author 2'],
          source: 'arxiv',
          published: '2023-01-01',
          abstract: 'This is a test paper abstract.'
        }
      ]),
      researchPaper: jest.fn().mockResolvedValue({
        paper: {
          id: 'paper1',
          title: 'Test Paper 1',
          authors: ['Author 1', 'Author 2'],
          source: 'arxiv',
          published: '2023-01-01',
          abstract: 'This is a test paper abstract.',
          content: 'This is the content of the paper.'
        },
        citations: [
          {
            id: 'citation1',
            title: 'Citation Paper 1',
            authors: ['Author 5', 'Author 6'],
            source: 'arxiv',
            published: '2023-03-01'
          }
        ],
        references: [
          {
            id: 'reference1',
            title: 'Reference Paper 1',
            authors: ['Author 9', 'Author 10'],
            source: 'arxiv',
            published: '2023-05-01'
          }
        ],
        hypothesis: {
          id: 'hypothesis_123',
          name: 'Test Hypothesis',
          description: 'This is a test hypothesis.',
          hypothesis: 'This is the hypothesis statement.',
          entryConditions: ['Condition 1', 'Condition 2'],
          exitConditions: ['Condition 3', 'Condition 4'],
          indicators: [{ name: 'RSI', parameters: { period: 14 } }],
          riskManagement: ['Rule 1', 'Rule 2'],
          timeframes: ['1D', '4H'],
          expectedPerformance: { cagr: 0.15, sharpeRatio: 1.5 }
        },
        strategy: {
          id: 'strategy_123',
          name: 'Test Hypothesis',
          description: 'This is a test hypothesis.',
          hypothesis: 'This is the hypothesis statement.',
          entryConditions: ['Condition 1', 'Condition 2'],
          exitConditions: ['Condition 3', 'Condition 4'],
          indicators: [{ name: 'RSI', parameters: { period: 14 } }],
          riskManagement: ['Rule 1', 'Rule 2'],
          timeframes: ['1D', '4H'],
          expectedPerformance: { cagr: 0.15, sharpeRatio: 1.5 }
        }
      }),
      getCitations: jest.fn().mockResolvedValue([
        {
          id: 'citation1',
          title: 'Citation Paper 1',
          authors: ['Author 5', 'Author 6'],
          source: 'arxiv',
          published: '2023-03-01'
        }
      ]),
      getReferences: jest.fn().mockResolvedValue([
        {
          id: 'reference1',
          title: 'Reference Paper 1',
          authors: ['Author 9', 'Author 10'],
          source: 'arxiv',
          published: '2023-05-01'
        }
      ]),
      execute: jest.fn().mockResolvedValue({
        papers: [
          {
            id: 'paper1',
            title: 'Test Paper 1',
            authors: ['Author 1', 'Author 2'],
            source: 'arxiv',
            published: '2023-01-01',
            abstract: 'This is a test paper abstract.'
          }
        ],
        strategies: [
          {
            id: 'strategy_123',
            name: 'Test Strategy',
            description: 'This is a test strategy.',
            hypothesis: 'This is the hypothesis statement.',
            entryConditions: ['Condition 1', 'Condition 2'],
            exitConditions: ['Condition 3', 'Condition 4'],
            indicators: [{ name: 'RSI', parameters: { period: 14 } }],
            riskManagement: ['Rule 1', 'Rule 2'],
            timeframes: ['1D', '4H'],
            expectedPerformance: { cagr: 0.15, sharpeRatio: 1.5 }
          }
        ]
      })
    } as any;
    
    // Mock the StrategyEvaluatorAgent methods
    reagent['strategyEvaluatorAgent'] = {
      execute: jest.fn().mockImplementation((strategies) => 
        strategies.map((strategy: any) => ({
          ...strategy,
          score: 0.8
        }))
      )
    } as any;
    
    // Mock the StrategyOptimizerAgent methods
    reagent['strategyOptimizerAgent'] = {
      execute: jest.fn().mockImplementation((strategies) => 
        strategies.map((strategy: any) => ({
          ...strategy,
          name: `Optimized ${strategy.name}`,
          description: `Optimized version of ${strategy.description}`
        }))
      )
    } as any;
  });
  
  test('Search academic papers', async () => {
    // Search for papers
    const papers = await reagent.searchAcademicPapers('test query', 2, ['arxiv', 'pubmed']);
    
    // Check if papers were found
    expect(papers).toBeDefined();
    expect(Array.isArray(papers)).toBe(true);
    
    // Check if agent method was called
    expect(reagent['academicSearchAgent'].searchPapers).toHaveBeenCalledWith('test query', 2, ['arxiv', 'pubmed']);
  });
  
  test('Research academic paper', async () => {
    // Research a paper
    const result = await reagent.researchAcademicPaper('paper1', 'arxiv');
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.paper).toBeDefined();
    expect(result.paper.id).toBe('paper1');
    expect(result.paper.title).toBe('Test Paper 1');
    expect(result.citations).toBeDefined();
    expect(result.references).toBeDefined();
    expect(result.hypothesis).toBeDefined();
    expect(result.strategy).toBeDefined();
    
    // Check if agent method was called
    expect(reagent['academicSearchAgent'].researchPaper).toHaveBeenCalledWith('paper1', 'arxiv');
  });
  
  test('Get citations', async () => {
    // Get citations
    const citations = await reagent.getCitations('paper1', 'arxiv', 2);
    
    // Check if citations were found
    expect(citations).toBeDefined();
    expect(Array.isArray(citations)).toBe(true);
    
    // Check if agent method was called
    expect(reagent['academicSearchAgent'].getCitations).toHaveBeenCalledWith('paper1', 'arxiv', 2);
  });
  
  test('Get references', async () => {
    // Get references
    const references = await reagent.getReferences('paper1', 'arxiv', 2);
    
    // Check if references were found
    expect(references).toBeDefined();
    expect(Array.isArray(references)).toBe(true);
    
    // Check if agent method was called
    expect(reagent['academicSearchAgent'].getReferences).toHaveBeenCalledWith('paper1', 'arxiv', 2);
  });
  
  test('Research academic strategies', async () => {
    // Research strategies
    const result = await reagent.researchAcademicStrategies('test query', 2, ['arxiv', 'pubmed']);
    
    // Check if result was returned
    expect(result).toBeDefined();
    expect(result.papers).toBeDefined();
    expect(Array.isArray(result.papers)).toBe(true);
    expect(result.strategies).toBeDefined();
    expect(Array.isArray(result.strategies)).toBe(true);
    expect(result.evaluatedStrategies).toBeDefined();
    expect(Array.isArray(result.evaluatedStrategies)).toBe(true);
    expect(result.optimizedStrategies).toBeDefined();
    expect(Array.isArray(result.optimizedStrategies)).toBe(true);
    
    // Check if agent methods were called
    expect(reagent['academicSearchAgent'].execute).toHaveBeenCalledWith({
      query: 'test query',
      maxResults: 2,
      sources: ['arxiv', 'pubmed']
    });
    expect(reagent['strategyEvaluatorAgent'].execute).toHaveBeenCalled();
    expect(reagent['strategyOptimizerAgent'].execute).toHaveBeenCalled();
  });
});
