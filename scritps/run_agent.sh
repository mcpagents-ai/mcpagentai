#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# This script is located at:
#   scripts/run_agent.sh
# ------------------------------------------------------------------------------

# 1) Get the absolute path of THIS script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 2) Move to the project root (which is one level up from `scripts`):
#    scripts -> (project root)
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
cd "${PROJECT_ROOT}" || exit 1

# Now you are at the project root and can run your desired commands here.
echo "Current directory: $(pwd)"


# ------------------------------------------------------------------------------
# Color definitions for friendly output
# ------------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Twitter AI Agent...${NC}\n"

# ------------------------------------------------------------------------------
# Check for Node.js installation
# ------------------------------------------------------------------------------
if ! command -v node > /dev/null 2>&1; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js first.${NC}"
    echo -e "Visit: https://nodejs.org/en/download/"
    exit 1
fi

# ------------------------------------------------------------------------------
# Check for npm installation
# ------------------------------------------------------------------------------
if ! command -v npm > /dev/null 2>&1; then
    echo -e "${RED}❌ npm is not installed. Please install npm first.${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Check for .env file in the project root
# ------------------------------------------------------------------------------
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found in project root. Please create .env with your credentials first.${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Install or update Node.js dependencies
# ------------------------------------------------------------------------------
echo -e "${GREEN}📦 Checking Node.js dependencies...${NC}"

# Create package.json if it doesn't exist
if [ ! -f "package.json" ]; then
    echo -e "${YELLOW}Creating package.json...${NC}"
    cat <<EOF > package.json
{
  "name": "mcpagentai-twitter",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "agent-twitter-client": "^0.0.18",
    "tough-cookie": "^4.0.0"
  }
}
EOF
fi

# Install Node.js dependencies if needed
if ! npm list agent-twitter-client &>/dev/null || ! npm list tough-cookie &>/dev/null; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    npm install --no-audit --no-fund || {
        echo -e "${RED}❌ Failed to install Node.js dependencies${NC}"
        exit 1
    }
fi

# ------------------------------------------------------------------------------
# Create store directory and necessary files
# ------------------------------------------------------------------------------
echo -e "${GREEN}📁 Setting up storage...${NC}"
mkdir -p store
touch store/replied_tweets.json
touch cookies.json

# ------------------------------------------------------------------------------
# Set up Python environment
# ------------------------------------------------------------------------------
export PYTHONPATH=../../../../../src
export LOG_LEVEL=DEBUG

echo -e "${GREEN}✨ Starting agent with configured personality...${NC}\n"

# ------------------------------------------------------------------------------
# Finally, start the agent
# ------------------------------------------------------------------------------
mcpagentai
