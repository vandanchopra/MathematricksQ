# Memory Knowledge Graph Dashboard

An interactive dashboard for exploring the memory knowledge graph of trading strategies.

## Features

- **Graph Visualization**: Interactive visualization of the complete knowledge graph
- **Metrics Analysis**: Bar charts showing performance metrics for strategies
- **Context Comparison**: Comparison of strategies across different market contexts
- **Strategy Evolution**: Line charts showing how strategy performance evolves across versions
- **Search**: Search for nodes by description or metrics
- **Similarity Search**: Find similar nodes using PatANN vector similarity

## Installation

### Local Development

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your configuration:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
PATANN_URL=http://localhost:9200
```

3. Run the dashboard:

```bash
python src/dashboard.py
```

4. Open your browser at http://localhost:8051

### Docker Deployment

1. Build and run using Docker Compose:

```bash
docker-compose up -d
```

2. Access the dashboard at http://localhost:8050

## Usage

### Graph Visualization Tab

- Use the checkboxes to filter by node types (Ideas, Backtests, Contexts, Scenarios)
- Use the checkboxes to filter by relationship types (TESTED_IN, EXECUTED_IN, APPLIES_IN, SUBIDEA_OF)
- Click "Refresh Graph" to update the visualization
- Drag nodes to rearrange the layout
- Hover over nodes to see details

### Metrics Analysis Tab

- Select a metric from the dropdown (Sharpe, CAGR, MaxDrawdown, etc.)
- Optionally filter by context
- Click "Show Metrics" to update the bar chart
- Hover over bars to see exact values

### Context Comparison Tab

- Select multiple contexts to compare
- Select a metric to compare
- Click "Compare Contexts" to update the chart
- See how strategies perform across different market contexts

### Strategy Evolution Tab

- Select a strategy to track
- Select a metric to track
- Click "Show Evolution" to update the chart
- See how strategy performance evolves across versions

### Search Tab

- Enter search terms to find nodes by description
- Filter by node type and metrics
- Click on a result to see detailed information
- View relationships to other nodes

### Similarity Search Tab

- Describe the trading strategy or idea you're looking for
- Click "Find Similar" to search using vector similarity
- View similar nodes with their similarity scores

## Scheduled Reports

The dashboard includes a script for generating and emailing weekly reports of top-performing strategies.

### Configuration

Add the following to your `.env` file:

```
EMAIL_SENDER=your-email@example.com
EMAIL_PASSWORD=your-email-password
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
REPORT_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

### Running Reports Manually

```bash
python src/reports/weekly_report.py
```

### Scheduling Reports

Add a cron job to run the reports automatically:

```bash
# Run weekly report every Monday at 8:00 AM
0 8 * * 1 /path/to/MathematricksQ/src/reports/schedule_reports.sh
```

## Customization

### Styling

The dashboard uses Bootstrap for styling. You can customize the appearance by modifying the CSS or adding custom stylesheets.

### Adding New Visualizations

To add new visualizations:

1. Create a new tab in the `app.layout`
2. Define the controls and visualization area
3. Add a callback to update the visualization

## Troubleshooting

- **Connection Issues**: Ensure Neo4j and PatANN are running and accessible
- **Missing Data**: Check that your memory graph has been populated with data
- **Performance Issues**: For large graphs, consider pre-computing layouts or using WebGL renderer
