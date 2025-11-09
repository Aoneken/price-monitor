#!/bin/bash
set -e

echo "🚀 Price Monitor - Setup Script"
echo "================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    PYTHON_CMD="python3"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    PYTHON_CMD="python3"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="Windows"
    PYTHON_CMD="python"
else
    OS="Unknown"
    PYTHON_CMD="python3"
fi

echo "✓ Detected OS: $OS"
echo ""

# Check Python version
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
echo "✓ Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate and install dependencies
echo "📥 Installing dependencies..."
if [[ "$OS" == "Windows" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

pip install --upgrade pip setuptools wheel -q
pip install -r requirements-dev.txt -q

echo "✓ Dependencies installed"
echo ""

# Initialize database
echo "🗄️  Initializing database..."
python -c "from webapp.database import init_db; init_db(); print('✓ Database initialized')"
echo ""

# Load sample data
echo "📊 Loading sample establishments..."
python -c "from webapp.main import _autoload_establishments; count = _autoload_establishments(); print(f'✓ Loaded {count} establishments')"
echo ""

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/unit -v --tb=short
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. Start webapp: make webapp  (or: python run_webapp.py)"
echo "  3. Run CLI: make cli  (or: python -m price_monitor.cli.main --help)"
echo "  4. Run tests: make test"
echo ""
echo "📚 Documentation:"
echo "  - README.md"
echo "  - docs/webapp/guide.md"
echo "  - CONTRIBUTING.md"
echo ""
echo "🎉 Happy coding!"
