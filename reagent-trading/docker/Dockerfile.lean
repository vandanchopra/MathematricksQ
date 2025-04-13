FROM quantconnect/lean:latest

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3-pip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Lean CLI
RUN pip3 install lean

# Install Node.js packages for web browsing
RUN npm install -g puppeteer-core node-fetch axios

# Set working directory
WORKDIR /app

# Create directories
RUN mkdir -p /app/strategies /app/data /app/results

# Copy strategy files
COPY ./strategies /app/strategies

# Set environment variables
ENV QC_USER_ID=357130
ENV QC_API_TOKEN=400c99249479b8bca6e035d5817d85c01eafaea0a210b022e1d826196e3d4c0b
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV BROWSER_WS_ENDPOINT=ws://puppeteer:3000

# Entry point
ENTRYPOINT ["bash"]
