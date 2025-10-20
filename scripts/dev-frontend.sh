#!/bin/bash

# 🎨 OpenGristAI - Frontend Development Server
# Starts SvelteKit frontend with hot-reload
#
# Usage:
#   ./scripts/dev-frontend.sh
#
# Prerequisites:
#   - Node.js installed
#   - Dependencies installed: cd frontend && npm install

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎨 OpenGristAI - Frontend Development Server${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"

# Check if dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Dependencies not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo ""
echo -e "${GREEN}🚀 Starting frontend on http://localhost:5173${NC}"
echo -e "${GREEN}🔄 Hot-reload enabled${NC}"
echo -e "${YELLOW}📌 Make sure backend is running on http://localhost:8000${NC}"
echo ""

cd frontend
npm run dev
