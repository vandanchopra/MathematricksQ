from setuptools import setup, find_packages

setup(
    name="agentic-developer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
        "langchain-community>=0.0.10",
        "openai>=1.12.0",
        "ollama>=0.1.6",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "quantconnect-stubs>=2024.3"
    ]
)