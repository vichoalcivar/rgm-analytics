# RGM Analytics Platform 🚀

Sistema integral de Revenue Growth Management con Machine Learning para optimización de precios, promociones y portafolio.

## 🎯 Características Principales

- **Optimización de Precios**: ML causal para elasticidad y pricing dinámico
- **Análisis Promocional**: ROI y efectividad de mecánicas promocionales
- **Gestión de Portafolio**: Optimización de mix y SKU rationalization
- **Forecasting Avanzado**: Modelos híbridos neurales-estadísticos
- **Inteligencia Competitiva**: Monitoreo y respuesta automatizada

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **ML/Analytics**: scikit-learn, XGBoost, Prophet, PyTorch
- **Databases**: PostgreSQL, Redis, MongoDB
- **Orquestación**: Apache Airflow
- **Visualización**: Streamlit, Plotly, Power BI
- **Infraestructura**: Docker, Kubernetes, AWS/Azure

## 📦 Instalación

### Prerrequisitos
- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Docker (opcional)

### Setup Local

1. Clonar el repositorio:
\`\`\`bash
git clone https://github.com/tu-usuario/rgm-analytics.git
cd rgm-analytics
\`\`\`

2. Crear entorno virtual:
\`\`\`bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
\`\`\`

3. Instalar dependencias:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. Configurar variables de entorno:
\`\`\`bash
cp .env.example .env
# Editar .env con tus configuraciones
\`\`\`

5. Inicializar base de datos:
\`\`\`bash
python scripts/setup_database.py
\`\`\`

6. Generar datos de ejemplo:
\`\`\`bash
python scripts/generate_sample_data.py
\`\`\`

## 🚀 Uso Rápido

### Ejecutar API
\`\`\`bash
uvicorn src.api.main:app --reload
\`\`\`

### Ejecutar Dashboard
\`\`\`bash
streamlit run dashboards/streamlit/app.py
\`\`\`

### Ejecutar Pipeline ETL
\`\`\`bash
python scripts/run_daily_pipeline.py
\`\`\`

## 📊 Estructura de Datos

Ver [data_dictionary.md](docs/data_dictionary.md) para detalles completos.

## 🧪 Testing

\`\`\`bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=src tests/
\`\`\`

## 📈 Casos de Uso

1. **Optimización de Precios Base**
2. **ROI de Promociones**
3. **Mix de Portafolio**
4. **Forecast de Demanda**
5. **Análisis Competitivo**

## 📝 Documentación

- [Guía de Usuario](docs/guides/user_guide.md)
- [API Reference](docs/api/reference.md)
- [Arquitectura](docs/architecture/overview.md)

## 🤝 Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para detalles.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👥 Equipo

- Data Science Lead: [Tu Nombre]
- ML Engineer: [Nombre]
- Data Engineer: [Nombre]

## 📞 Contacto

- Email: rgm-analytics@empresa.com
- Slack: #rgm-analytics