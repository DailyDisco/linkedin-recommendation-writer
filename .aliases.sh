# LinkedIn Recommendation Writer - Easy Commands
# Source this file: source .aliases.sh

# One-letter aliases for common commands
alias s='./setup.sh'           # Setup script
alias q='./start.sh'           # Quick start
alias l='s dev logs'           # Show logs
alias st='s dev status'        # Show status
alias up='s dev start'         # Start services
alias down='s dev stop'        # Stop services
alias test='s test test'       # Run tests
alias clean='s clean'          # Clean up

# Development shortcuts
alias dev='s dev setup'        # Full dev setup
alias prod='s prod setup'      # Full prod setup
alias build='s dev build'      # Build only

# Service-specific logs
alias logs-fe='s dev logs frontend'
alias logs-be='s dev logs backend'
alias logs-db='s dev logs postgres'
alias logs-redis='s dev logs redis'

# Database shortcuts
alias db='s dev shell-backend'
alias db-connect='s dev shell-backend bash -c "python -c \"import asyncio; from app.core.database import init_database; asyncio.run(init_database())\""'

# Test shortcuts
alias test-fe='s test-interactive'  # Frontend test UI
alias test-be='s test-backend'      # Backend tests only
alias coverage='s test-coverage'    # Generate coverage reports

echo "🚀 LinkedIn Recommendation Writer aliases loaded!"
echo ""
echo "Available commands:"
echo "  q           - Quick start everything"
echo "  dev         - Full development setup"
echo "  prod        - Full production setup"
echo "  up          - Start services"
echo "  down        - Stop services"
echo "  l           - Show logs"
echo "  st          - Show status"
echo "  test        - Run all tests"
echo "  clean       - Clean up Docker resources"
echo ""
echo "Examples:"
echo "  q           # Start everything"
echo "  l           # View logs"
echo "  test        # Run tests"
echo "  down        # Stop services"
