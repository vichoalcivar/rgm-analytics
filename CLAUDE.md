# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RGM Analytics Platform is a Revenue Growth Management system with Machine Learning capabilities for price optimization, promotional analysis, and portfolio management. The platform uses Python with FastAPI backend, Streamlit dashboards, and various ML libraries for advanced analytics.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requisitos.txt
# or using Makefile
make install
```

### Running the Application
```bash
# Run FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
# or
make run-api

# Run Streamlit dashboard
streamlit run dashboards/streamlit/app.py
# or
make run-dashboard
```

### Testing and Code Quality
```bash
# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html
# or
make test

# Code formatting and linting
make format  # Format with black and isort
make lint    # Run flake8, mypy, black check, isort check
```

### Database and Data Management
```bash
# Initialize database
python scripts/setup_database.py
# or
make db-init

# Generate sample data
python scripts/generate_sample_data.py
# or
make db-seed

# Run daily ETL pipeline
python scripts/run_daily_pipeline.py --date today
# or
make run-pipeline
```

### Docker Operations
```bash
make docker-build  # Build Docker images
make docker-up     # Start services
make docker-down   # Stop services
make docker-logs   # View logs
```

## Architecture Overview

### Core Structure
- **src/**: Main application code
  - **api/**: FastAPI endpoints and schemas
  - **models/**: ML models (pricing, forecasting, optimization, clustering)
  - **data_ingestion/**: Data pipeline components
  - **etl/**: Extract, Transform, Load processes
  - **features/**: Feature engineering modules
  - **utils/**: Shared utilities and logging
- **dashboards/**: Visualization interfaces (Streamlit, Dash, Power BI)
- **notebooks/**: Jupyter notebooks for analysis and experimentation
- **data/**: Data storage (raw, processed, interim, synthetic, external)
- **tests/**: Unit and integration tests
- **scripts/**: Automation and setup scripts

### Key Components
- **Configuration**: Centralized settings in `config/settings.py` using Pydantic
- **Logging**: Structured logging with rotation in `src/utils/logger.py`
- **API**: RESTful API with FastAPI for pricing, promotions, forecasting, and inventory endpoints
- **ML Models**: Organized by domain (pricing elasticity, demand forecasting, portfolio optimization)
- **Data Pipeline**: ETL processes for data ingestion and transformation

### Data Flow
1. Raw data ingested through `src/data_ingestion/`
2. Processing via ETL pipelines in `src/etl/`
3. Feature engineering in `src/features/`
4. Model training/prediction in `src/models/`
5. API serving through `src/api/`
6. Visualization via dashboards

### Technology Stack
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **ML/Analytics**: scikit-learn, XGBoost, Prophet, TensorFlow, PyTorch
- **Databases**: PostgreSQL, Redis, MongoDB
- **Visualization**: Streamlit, Plotly, matplotlib, seaborn
- **Data Processing**: pandas, numpy, scipy
- **Causal Inference**: dowhy, econml

## Key Files and Configuration

### Dependencies
- Main dependencies in `requisitos.txt`
- Development setup via `setup.py`
- Environment variables configured via `.env` file (copy from `.env.example`)

### Settings
- Application configuration in `config/settings.py` (note: typo in filename `setttings.py`)
- Database, Redis, API, and ML configuration centralized
- Paths automatically configured relative to project root

### Testing
- Tests organized in `tests/unit/` and `tests/integration/`
- Use pytest with coverage reporting
- No specific test framework assumptions - check existing test files for patterns

### Notebooks
Key analysis notebooks:
- `01_analisis_exploratorio_rgm.ipynb`: Exploratory data analysis
- `02_modelos_ml_rgm.ipynb`: ML model development

## Important Notes

### Data Handling
- Large datasets are processed in the notebooks (millions of records)
- Synthetic data generation available via scripts
- Data stored in organized directory structure by processing stage

### ML Development
- Models organized by business function (pricing, forecasting, etc.)
- MLflow integration available for model tracking
- Causal inference tools integrated for price elasticity analysis

### API Development
- FastAPI with automatic OpenAPI documentation at `/docs`
- CORS enabled for development (configure for production)
- Health check endpoint at `/health`
- Endpoints organized by business domain

When working with this codebase, always activate the virtual environment first and ensure dependencies are installed. Use the Makefile commands for consistent development workflow.