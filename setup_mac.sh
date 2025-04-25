#!/bin/bash

echo "Setting up MathematricksQ Graph Memory System for macOS..."

# Check for Python installation
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed! Please install Python 3.8 or later."
    echo "You can use Homebrew: brew install python3"
    exit 1
fi

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed! It's recommended for installing Neo4j and PatANN."
    echo "Visit: https://brew.sh"
    exit 1
fi

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install core requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -e AgenticDeveloper

# Install graph memory specific requirements
echo "Installing graph memory specific requirements..."
pip install sentence-transformers neo4j-python-driver requests numpy python-dotenv

# Check for Neo4j installation
if ! brew list neo4j &> /dev/null; then
    echo "Installing Neo4j using Homebrew..."
    brew install neo4j
    echo "Please run 'neo4j-admin set-initial-password <your-password>' to set up Neo4j"
fi

# Install APOC plugin
NEO4J_PLUGIN_DIR="$(brew --prefix)/var/neo4j/plugins"
if [ -d "$NEO4J_PLUGIN_DIR" ]; then
    echo "Copying APOC plugin..."
    cp neo4j/plugins/apoc.jar "$NEO4J_PLUGIN_DIR/"
    echo "APOC plugin copied to Neo4j plugins directory"
else
    echo "Neo4j plugins directory not found! Please ensure Neo4j is properly installed."
fi

# Check for PatANN
echo "Checking PatANN installation..."
if ! curl -s -f http://localhost:9200 &> /dev/null; then
    echo "PatANN server is not running or not installed!"
    echo "Please install PatANN from https://github.com/mesibo/patann"
    echo "and ensure it's running on port 9200"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
PATANN_URL=http://localhost:9200
EOL
    echo "Created .env file - please update with your configurations"
fi

# Set execute permissions
chmod +x src/reports/schedule_reports.sh

# Start Neo4j service
echo "Starting Neo4j service..."
brew services start neo4j

echo
echo "Setup completed! Please ensure:"
echo "1. Neo4j 4.4+ is running (brew services start neo4j)"
echo "2. APOC plugin is installed in: $NEO4J_PLUGIN_DIR"
echo "3. PatANN server is installed and running on port 9200"
echo "4. .env file is configured with correct credentials"
echo
echo "To verify the setup:"
echo "1. Run 'python -m pytest tests/unit/test_memory_interface.py'"
echo "2. Try the example: 'python examples/memory_example.py'"
echo
echo "Additional commands:"
echo "- Start Neo4j: brew services start neo4j"
echo "- Stop Neo4j: brew services stop neo4j"
echo "- Restart Neo4j: brew services restart neo4j"
echo "- Neo4j status: brew services list | grep neo4j"