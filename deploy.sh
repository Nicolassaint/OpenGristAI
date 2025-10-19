#!/bin/bash

# ==============================================================================
# Grist AI API - Deployment Script
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Configuration
# ==============================================================================

CONDA_ENV="grist"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"

# Determine environment (default: development)
ENVIRONMENT="${ENVIRONMENT:-development}"

# Set log level based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    LOG_LEVEL="INFO"
    RELOAD="--no-reload"
else
    LOG_LEVEL="DEBUG"
    RELOAD="--reload"
fi

# ==============================================================================
# Functions
# ==============================================================================

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Grist AI API - Deployment${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==============================================================================
# Main Script
# ==============================================================================

print_header

# Check if conda is available
if ! command -v conda &> /dev/null; then
    print_error "Conda not found. Please install Anaconda or Miniconda."
    exit 1
fi

print_info "Activating conda environment: $CONDA_ENV"

# Initialize conda for bash
eval "$(conda shell.bash hook)"

# Activate conda environment
if conda activate "$CONDA_ENV" 2>/dev/null; then
    print_info "Environment '$CONDA_ENV' activated successfully"
else
    print_error "Failed to activate environment '$CONDA_ENV'"
    print_info "Available environments:"
    conda env list
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Using default configuration."
fi

# Display configuration
echo ""
print_info "Configuration:"
echo "  - Environment: $ENVIRONMENT"
echo "  - Log Level: $LOG_LEVEL"
echo "  - Host: $API_HOST"
echo "  - Port: $API_PORT"
echo "  - Reload: ${RELOAD/--no-reload/Disabled}"
echo "  - Reload: ${RELOAD/--reload/Enabled}"
echo ""

# Start the API
print_info "Starting Grist AI API..."
echo ""

export LOG_LEVEL="$LOG_LEVEL"
export ENVIRONMENT="$ENVIRONMENT"

uvicorn app.api.main:app \
    --host "$API_HOST" \
    --port "$API_PORT" \
    $RELOAD

print_info "API stopped."

