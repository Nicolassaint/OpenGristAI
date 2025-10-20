#!/bin/bash

# 🔧 OpenGristAI - Backend Development Server
# Starts FastAPI backend with hot-reload
#
# Usage:
#   ./scripts/dev-backend.sh
#
# Prerequisites:
#   - Python environment activated (conda, venv, etc.)
#   - Dependencies installed: pip install -r backend/requirements.txt
#   - .env file configured: cp backend/.env.example backend/.env

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔧 OpenGristAI - Backend Development Server${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Warning: backend/.env not found${NC}"
    echo -e "${YELLOW}   Creating from .env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${RED}   🚨 Please edit backend/.env with your API keys before continuing!${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python not found. Please activate your Python environment.${NC}"
    echo -e "${YELLOW}   Example:${NC}"
    echo -e "${YELLOW}     conda activate your-env${NC}"
    echo -e "${YELLOW}     # or${NC}"
    echo -e "${YELLOW}     source venv/bin/activate${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python found: $(python --version)${NC}"

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies not found. Installing...${NC}"
    pip install -r backend/requirements.txt
fi

echo ""
echo -e "${GREEN}🚀 Starting backend on http://localhost:8000${NC}"
echo -e "${GREEN}📖 API docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}🔄 Hot-reload enabled${NC}"
echo ""

cd backend
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
