#!/bin/bash
set -e  # Exit on error

echo "🔨 Building Wind Turbine Analytics..."

# 1. Build Frontend
echo "📦 Building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✅ Frontend built to frontend/dist/"

# 2. Verify backend dependencies
echo "🐍 Verifying Python dependencies..."
pip install -r requirements.txt --quiet

echo "✅ Backend dependencies ready"

# 3. Test FastAPI can import
echo "🧪 Testing FastAPI imports..."
python -c "from src.wind_turbine_analytics.api.main import app; print('FastAPI app loaded successfully')"

echo "🎉 Build complete! Ready for deployment."
