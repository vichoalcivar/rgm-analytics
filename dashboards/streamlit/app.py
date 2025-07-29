"""
Streamlit Dashboard for RGM Analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Page config
st.set_page_config(
    page_title="RGM Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎯 RGM Analytics Dashboard</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100?text=RGM+Analytics", use_column_width=True)
    st.markdown("---")
    
    # Date filter
    st.subheader("📅 Filtros de Fecha")
    date_range = st.date_input(
        "Seleccionar rango de fechas",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now()
    )
    
    # Category filter
    st.subheader("📦 Filtros de Producto")
    categories = st.multiselect(
        "Categorías",
        options=['CUIDADO_PERSONAL', 'LIMPIEZA_HOGAR', 'ALIMENTOS'],
        default=['CUIDADO_PERSONAL']
    )
    
    # Analysis type
    st.subheader("📊 Tipo de Análisis")
    analysis_type = st.radio(
        "Seleccionar análisis",
        options=['Pricing', 'Promociones', 'Portafolio', 'Competencia', 'Forecast']
    )

# Main content
if analysis_type == 'Pricing':
    st.header("💰 Análisis de Precios")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Price Realization",
            value="94.2%",
            delta="+2.1%"
        )
    
    with col2:
        st.metric(
            label="Margen Promedio",
            value="32.5%",
            delta="+1.8%"
        )
    
    with col3:
        st.metric(
            label="Elasticidad Promedio",
            value="-1.35",
            delta="-0.05"
        )
    
    with col4:
        st.metric(
            label="SKUs Optimizados",
            value="78/100",
            delta="+12"
        )
    
    # Price optimization chart
    st.subheader("🎯 Oportunidades de Optimización de Precio")
    
    # Sample data
    optimization_data = pd.DataFrame({
        'SKU': [f'SKU-{i}' for i in range(10)],
        'Precio_Actual': [45, 32, 78, 23, 56, 89, 34, 67, 45, 90],
        'Precio_Optimo': [48, 35, 75, 25, 60, 85, 38, 70, 47, 88],
        'Impacto_Margen': [150, 230, -120, 180, 340, -200, 290, 160, 120, -140]
    })
    
    fig = go.Figure()
    
    # Add bars for current vs optimal price
    fig.add_trace(go.Bar(
        name='Precio Actual',
        x=optimization_data['SKU'],
        y=optimization_data['Precio_Actual'],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Precio Óptimo',
        x=optimization_data['SKU'],
        y=optimization_data['Precio_Optimo'],
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='Precio Actual vs Óptimo por SKU',
        xaxis_title='SKU',
        yaxis_title='Precio ($)',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Elasticity matrix
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Matriz de Elasticidad")
        
        # Sample elasticity data
        elasticity_data = pd.DataFrame({
            'Categoria': ['SHAMPOO', 'JABON', 'DETERGENTE', 'ACEITE', 'PASTA'],
            'Elasticidad': [-1.2, -0.8, -1.5, -0.5, -1.8],
            'Volumen': [10000, 15000, 8000, 20000, 5000]
        })
        
        fig2 = px.scatter(elasticity_data, 
                         x='Elasticidad', 
                         y='Volumen',
                         size='Volumen',
                         color='Categoria',
                         title='Elasticidad vs Volumen por Categoría',
                         hover_data=['Categoria'])
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Recomendaciones de Precio")
        
        recommendations = pd.DataFrame({
            'SKU': ['SKU-001', 'SKU-002', 'SKU-003'],
            'Acción': ['Subir 5%', 'Mantener', 'Bajar 3%'],
            'Impacto': ['+$15,000', '$0', '-$8,000'],
            'Confianza': ['Alta', 'Media', 'Alta']
        })
        
        st.dataframe(recommendations, use_container_width=True)

elif analysis_type == 'Promociones':
    st.header("🎁 Análisis de Promociones")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="ROI Promocional",
            value="1.25x",
            delta="+0.15x"
        )
    
    with col2:
        st.metric(
            label="Incrementalidad",
            value="68%",
            delta="+5%"
        )
    
    with col3:
        st.metric(
            label="Inversión Trade",
            value="$2.5M",
            delta="-$200K"
        )
    
    with col4:
        st.metric(
            label="Efectividad",
            value="82%",
            delta="+8%"
        )
    
    # Promotion effectiveness chart
    st.subheader("📈 Efectividad por Mecánica Promocional")
    
    promo_data = pd.DataFrame({
        'Mecanica': ['3x2', '2x1', '30% Desc', '50% Desc', 'Regalo'],
        'ROI': [1.5, 1.2, 0.9, 0.7, 1.3],
        'Incrementalidad': [75, 65, 45, 30, 70],
        'Frecuencia': [150, 200, 300, 100, 80]
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=promo_data['Incrementalidad'],
        y=promo_data['ROI'],
        mode='markers+text',
        marker=dict(
            size=promo_data['Frecuencia']/10,
            color=promo_data['ROI'],
            colorscale='RdYlGn',
            showscale=True
        ),
        text=promo_data['Mecanica'],
        textposition="top center"
    ))
    
    fig.update_layout(
        title='ROI vs Incrementalidad por Mecánica',
        xaxis_title='Incrementalidad (%)',
        yaxis_title='ROI',
        height=500
    )
    
    # Add quadrant lines
    fig.add_hline(y=1, line_dash="dash", line_color="gray")
    fig.add_vline(x=50, line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>RGM Analytics Platform v0.1.0 | © 2024 | 
        <a href='mailto:support@rgm-analytics.com'>Soporte</a></p>
    </div>
    """,
    unsafe_allow_html=True
)