@echo off
echo Setting up MathematricksQ Graph Memory System for Windows...

:: Check for Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.8 or later.
    exit /b 1
)

:: Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

:: Install core requirements
echo Installing Python dependencies...
pip install -r requirements.txt
pip install -e AgenticDeveloper

:: Install graph memory specific requirements
pip install sentence-transformers neo4j-python-driver requests numpy python-dotenv

:: Check for Neo4j installation
where neo4j > nul 2>&1
if errorlevel 1 (
    echo Neo4j is not installed! Please install Neo4j 4.4 or later.
    echo Visit: https://neo4j.com/download/
    echo After installation, please:
    echo 1. Set initial password for Neo4j
    echo 2. Install APOC plugin from Neo4j Desktop
)

:: Copy APOC plugin if Neo4j is installed
if exist "C:\Program Files\Neo4j\*\plugins" (
    echo Copying APOC plugin...
    xcopy /y "neo4j\plugins\apoc.jar" "C:\Program Files\Neo4j\*\plugins\"
)

:: Check for PatANN
echo Checking PatANN installation...
curl -f http://localhost:9200 > nul 2>&1
if errorlevel 1 (
    echo PatANN server is not running or not installed!
    echo Please install PatANN from https://github.com/mesibo/patann
    echo and ensure it's running on port 9200
)

:: Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from sample...
    (
    echo NEO4J_URI=bolt://localhost:7687
    echo NEO4J_USER=neo4j
    echo NEO4J_PASSWORD=password
    echo PATANN_URL=http://localhost:9200
    ) > .env
    echo Created .env file - please update with your configurations
)

echo.
echo Setup completed! Please ensure:
echo 1. Neo4j 4.4+ is installed and running
echo 2. APOC plugin is installed in Neo4j plugins directory
echo 3. PatANN server is installed and running on port 9200
echo 4. .env file is configured with correct credentials
echo.
echo To verify the setup:
echo 1. Run 'python -m pytest tests/unit/test_memory_interface.py'
echo 2. Try the example: 'python examples/memory_example.py'