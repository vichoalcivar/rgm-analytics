#!/usr/bin/env python3
"""
Análisis Completo de Elasticidad de Precios para RGM
Autor: Claude Code Assistant
Fecha: 2025-01-05
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

def clean_numeric_columns(df, numeric_cols):
    """
    Convierte columnas numéricas que usan coma como separador decimal
    """
    df_clean = df.copy()
    for col in numeric_cols:
        if col in df_clean.columns:
            # Convertir a string primero para manejar valores no string
            df_clean[col] = df_clean[col].astype(str)
            # Reemplazar comas por puntos decimales
            df_clean[col] = df_clean[col].str.replace(',', '.', regex=False)
            # Manejar valores vacíos o no numéricos
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    return df_clean

def analisis_elasticidad_completo(df_ventas_raw, data_path='../data/processed/'):
    """
    Función principal para análisis completo de elasticidad de precios
    """
    print('ANALISIS COMPLETO DE ELASTICIDAD DE PRECIOS')
    print('=' * 60)

    # Paso 1: Limpiar datos numéricos
    print('Limpiando formato numerico...')
    numeric_columns = ['PRECIO', 'QTY_ENTREGADA', 'QTY_PEDIDA', 'QTY_SUGERIDA', 'QTY_KILOS', 
                      'IMPORTE', 'IMPORTE_DSCTO', 'PRECIO_COSTOSTD', 'PCTJ_DSCTO']
    
    df_ventas = clean_numeric_columns(df_ventas_raw, numeric_columns)

    # Paso 2: Filtrar y preparar datos
    print('Preparando datos para analisis de elasticidad...')
    df_ventas_clean = df_ventas[
        (df_ventas['PRECIO'] > 0) & 
        (df_ventas['QTY_ENTREGADA'] > 0) & 
        (df_ventas['IMPORTE'] > 0) &
        df_ventas['PRECIO'].notna() & 
        df_ventas['QTY_ENTREGADA'].notna() & 
        df_ventas['IMPORTE'].notna()
    ].copy()

    print(f'Registros validos: {len(df_ventas_clean):,} de {len(df_ventas):,} ({len(df_ventas_clean)/len(df_ventas)*100:.1f}%)')

    # Paso 3: Análisis de variabilidad de precios por producto
    print('\nAnalizando variabilidad de precios por producto...')
    price_stats = df_ventas_clean.groupby('SKU')['PRECIO'].agg([
        'count', 'mean', 'std', 'min', 'max', 'nunique'
    ]).reset_index()

    # Calcular métricas de variabilidad
    price_stats['CV'] = price_stats['std'] / price_stats['mean']  # Coeficiente de variación
    price_stats['Rango_Pct'] = (price_stats['max'] - price_stats['min']) / price_stats['mean'] * 100
    price_stats['Densidad_Precios'] = price_stats['nunique'] / price_stats['count']

    # Criterios para productos viables para elasticidad
    MIN_TRANSACTIONS = 100  # Mínimo transacciones
    MIN_CV = 0.10          # Mínimo 10% coeficiente de variación
    MIN_UNIQUE_PRICES = 5   # Mínimo 5 precios únicos
    MIN_PRICE_RANGE = 15    # Mínimo 15% rango de precios

    viable_skus = price_stats[
        (price_stats['count'] >= MIN_TRANSACTIONS) &
        (price_stats['CV'] >= MIN_CV) &
        (price_stats['nunique'] >= MIN_UNIQUE_PRICES) &
        (price_stats['Rango_Pct'] >= MIN_PRICE_RANGE)
    ]

    print(f'Resultados del analisis de variabilidad:')
    print(f'   - Total productos: {len(price_stats):,}')
    print(f'   - Con >100 transacciones: {(price_stats["count"] >= 100).sum():,}')
    print(f'   - Con CV >10%: {(price_stats["CV"] >= 0.10).sum():,}')
    print(f'   - Con >5 precios unicos: {(price_stats["nunique"] >= 5).sum():,}')
    print(f'   - Con rango >15%: {(price_stats["Rango_Pct"] >= 15).sum():,}')
    print(f'   - Productos viables para elasticidad: {len(viable_skus):,}')

    if len(viable_skus) == 0:
        print('\nNo hay productos con suficiente variabilidad de precios')
        print('Recomendaciones:')
        print('   - Reducir criterios minimos')
        print('   - Analizar datos por periodo temporal mas largo')
        print('   - Considerar factores externos (promociones, estacionalidad)')
        
        # Mostrar estadísticas para diagnóstico
        print('\nEstadisticas generales de precios:')
        print(f'   CV promedio: {price_stats["CV"].mean():.3f}')
        print(f'   CV mediano: {price_stats["CV"].median():.3f}')
        print(f'   Rango % promedio: {price_stats["Rango_Pct"].mean():.1f}%')
        
        return pd.DataFrame(), pd.DataFrame(), price_stats
        
    else:
        print(f'\nTop 10 productos con mayor variabilidad:')
        top_products = viable_skus.nlargest(10, 'CV')[['SKU', 'count', 'mean', 'CV', 'Rango_Pct', 'nunique']]
        for _, row in top_products.iterrows():
            print(f'   {row["SKU"][:15]:15} | Transacciones: {row["count"]:5.0f} | CV: {row["CV"]:.3f} | Rango: {row["Rango_Pct"]:.1f}% | Precios unicos: {row["nunique"]:3.0f}')
        
        # Paso 4: Crear datos agregados para elasticidad
        print(f'\nCreando datos agregados para {len(viable_skus)} productos...')
        
        def create_price_segments(sku_data, n_segments=5):
            """Crea segmentos de precios inteligentes para un producto"""
            prices = sku_data['PRECIO'].values
            
            # Si hay pocos precios únicos, usar todos
            unique_prices = len(np.unique(prices))
            if unique_prices <= n_segments:
                n_segments = max(3, unique_prices - 1)
            
            # Crear bins usando quantiles
            try:
                sku_data['Precio_Segment'] = pd.qcut(
                    sku_data['PRECIO'], 
                    q=n_segments, 
                    labels=False, 
                    duplicates='drop'
                )
            except:
                # Fallback: usar bins manuales
                sku_data['Precio_Segment'] = pd.cut(
                    sku_data['PRECIO'], 
                    bins=n_segments, 
                    labels=False, 
                    include_lowest=True
                )
            
            return sku_data
        
        # Crear datos agregados
        aggregated_data = []
        processed_count = 0
        
        for sku in viable_skus['SKU'].head(10):  # Limitar a top 10 para performance
            sku_data = df_ventas_clean[df_ventas_clean['SKU'] == sku].copy()
            
            # Crear segmentos de precios
            sku_data = create_price_segments(sku_data)
            
            # Agregar por segmento
            sku_agg = sku_data.groupby(['SKU', 'Precio_Segment']).agg({
                'PRECIO': 'mean',
                'QTY_ENTREGADA': 'sum',
                'IMPORTE': 'sum'
            }).reset_index()
            
            # Solo incluir si hay al menos 3 segmentos con datos válidos
            if len(sku_agg) >= 3 and sku_agg['PRECIO'].std() > 0:
                aggregated_data.append(sku_agg)
                processed_count += 1
        
        if aggregated_data:
            elasticity_data = pd.concat(aggregated_data, ignore_index=True)
            print(f'Datos agregados creados: {len(elasticity_data):,} observaciones de {processed_count} productos')
            
            # Mostrar muestra
            print('\nMuestra de datos agregados:')
            sample_data = elasticity_data.head(10)[['SKU', 'Precio_Segment', 'PRECIO', 'QTY_ENTREGADA', 'IMPORTE']]
            for _, row in sample_data.iterrows():
                print(f'   {row["SKU"][:15]:15} | Seg: {row["Precio_Segment"]} | Precio: ${row["PRECIO"]:8.2f} | Qty: {row["QTY_ENTREGADA"]:8.0f} | Venta: ${row["IMPORTE"]:10.2f}')
            
            # Paso 5: Calcular elasticidades
            print(f'\nCalculando elasticidades precio-demanda...')
            elasticity_results = calcular_elasticidades(elasticity_data)
            
            return elasticity_data, elasticity_results, price_stats
        else:
            print('No se pudieron crear datos agregados')
            return pd.DataFrame(), pd.DataFrame(), price_stats

def calcular_elasticidades(elasticity_data):
    """
    Calcula elasticidades precio-demanda para productos
    """
    def calculate_elasticity_for_product(product_data):
        """Calcula elasticidad para un producto usando regresión log-log"""
        # Filtrar datos válidos
        valid_data = product_data[
            (product_data['PRECIO'] > 0) & 
            (product_data['QTY_ENTREGADA'] > 0)
        ].copy()
        
        if len(valid_data) < 3:
            return None
        
        # Verificar variación
        if valid_data['PRECIO'].std() == 0 or valid_data['QTY_ENTREGADA'].std() == 0:
            return None
        
        try:
            # Transformación log-log
            log_price = np.log(valid_data['PRECIO'])
            log_qty = np.log(valid_data['QTY_ENTREGADA'])
            
            # Regresión
            X = log_price.values.reshape(-1, 1)
            y = log_qty.values
            
            model = LinearRegression().fit(X, y)
            elasticity = model.coef_[0]
            r2 = model.score(X, y)
            
            # Calcular intervalo de confianza básico
            residuals = y - model.predict(X)
            mse = np.mean(residuals**2)
            
            return {
                'SKU': valid_data['SKU'].iloc[0],
                'Elasticidad': elasticity,
                'R2': r2,
                'MSE': mse,
                'Observaciones': len(valid_data),
                'Precio_Min': valid_data['PRECIO'].min(),
                'Precio_Max': valid_data['PRECIO'].max(),
                'Precio_Promedio': valid_data['PRECIO'].mean(),
                'Cantidad_Total': valid_data['QTY_ENTREGADA'].sum(),
                'Venta_Total': valid_data['IMPORTE'].sum()
            }
        except Exception as e:
            return None
    
    # Calcular elasticidades para cada producto
    elasticity_results = []
    for sku in elasticity_data['SKU'].unique():
        product_data = elasticity_data[elasticity_data['SKU'] == sku]
        result = calculate_elasticity_for_product(product_data)
        if result:
            elasticity_results.append(result)
    
    if elasticity_results:
        elasticity_results = pd.DataFrame(elasticity_results)
        
        # Filtrar resultados válidos
        valid_elasticities = elasticity_results[
            (elasticity_results['R2'] > 0.3) &  # R² mínimo del 30%
            (elasticity_results['Elasticidad'] < 0) &  # Elasticidad negativa
            (elasticity_results['Elasticidad'] > -5) &  # Elasticidad razonable
            (elasticity_results['Observaciones'] >= 3)
        ]
        
        print(f'Resultados del analisis de elasticidad:')
        print(f'   - Productos procesados: {len(elasticity_results)}')
        print(f'   - Elasticidades validas: {len(valid_elasticities)}')
        
        if len(valid_elasticities) > 0:
            print(f'   - Elasticidad promedio: {valid_elasticities["Elasticidad"].mean():.3f}')
            print(f'   - R2 promedio: {valid_elasticities["R2"].mean():.3f}')
            print(f'   - Rango elasticidades: {valid_elasticities["Elasticidad"].min():.3f} a {valid_elasticities["Elasticidad"].max():.3f}')
            
            # Categorizar elasticidades
            def categorize_elasticity(e):
                if e > -0.5:
                    return 'Inelástico'
                elif e > -1:
                    return 'Poco Elástico'
                elif e > -2:
                    return 'Elástico'
                else:
                    return 'Muy Elástico'
            
            valid_elasticities['Categoria'] = valid_elasticities['Elasticidad'].apply(categorize_elasticity)
            
            print(f'\nCategorizacion de productos:')
            category_counts = valid_elasticities['Categoria'].value_counts()
            for cat, count in category_counts.items():
                pct = count / len(valid_elasticities) * 100
                print(f'   - {cat}: {count} productos ({pct:.1f}%)')
            
            print(f'\nTop 5 productos mas elasticos:')
            top_elastic = valid_elasticities.nsmallest(5, 'Elasticidad')
            for _, row in top_elastic.iterrows():
                print(f'   {row["SKU"][:20]:20} | E: {row["Elasticidad"]:6.3f} | R2: {row["R2"]:5.3f} | ${row["Precio_Promedio"]:8.2f}')
            
            print(f'\nTop 5 productos menos elasticos:')
            least_elastic = valid_elasticities.nlargest(5, 'Elasticidad') 
            for _, row in least_elastic.iterrows():
                print(f'   {row["SKU"][:20]:20} | E: {row["Elasticidad"]:6.3f} | R²: {row["R2"]:5.3f} | ${row["Precio_Promedio"]:8.2f}')
            
            return valid_elasticities
        else:
            print('No se encontraron elasticidades validas despues del filtrado')
            return pd.DataFrame()
    else:
        print('No se pudieron calcular elasticidades')
        return pd.DataFrame()

def crear_visualizaciones_elasticidad(elasticity_results):
    """
    Crea dashboard de visualizaciones para análisis de elasticidad
    """
    if len(elasticity_results) == 0:
        print('No hay datos de elasticidad para visualizar')
        return
    
    print('CREANDO VISUALIZACIONES DE ELASTICIDAD')
    print('=' * 50)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Dashboard de Analisis de Elasticidad Precio-Demanda', fontsize=16, fontweight='bold')
    
    # 1. Distribución de elasticidades
    axes[0,0].hist(elasticity_results['Elasticidad'], bins=20, alpha=0.7, color='steelblue', edgecolor='black')
    axes[0,0].axvline(elasticity_results['Elasticidad'].mean(), color='red', linestyle='--', linewidth=2,
                      label=f'Media: {elasticity_results["Elasticidad"].mean():.3f}')
    axes[0,0].axvline(-1, color='orange', linestyle='--', linewidth=2, label='Elasticidad Unitaria')
    axes[0,0].set_title('Distribución de Elasticidades')
    axes[0,0].set_xlabel('Elasticidad Precio-Demanda')
    axes[0,0].set_ylabel('Frecuencia')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. R² vs Elasticidad
    scatter = axes[0,1].scatter(elasticity_results['Elasticidad'], elasticity_results['R2'], 
                               alpha=0.7, c=elasticity_results['Precio_Promedio'], 
                               cmap='viridis', s=60, edgecolors='black', linewidth=0.5)
    axes[0,1].set_title('Calidad del Modelo vs Elasticidad')
    axes[0,1].set_xlabel('Elasticidad')
    axes[0,1].set_ylabel('R² (Calidad del ajuste)')
    axes[0,1].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[0,1], label='Precio Promedio ($)')
    
    # 3. Categorización por elasticidad
    if 'Categoria' in elasticity_results.columns:
        cat_counts = elasticity_results['Categoria'].value_counts()
        colors_pie = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        wedges, texts, autotexts = axes[0,2].pie(cat_counts.values, labels=cat_counts.index, 
                                                 autopct='%1.1f%%', startangle=90, colors=colors_pie)
        axes[0,2].set_title('Categorización por Elasticidad')
        
        # Mejorar texto
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    # 4. Elasticidad vs Precio Promedio
    axes[1,0].scatter(elasticity_results['Precio_Promedio'], elasticity_results['Elasticidad'], 
                     alpha=0.7, c=elasticity_results['R2'], cmap='plasma', s=60, 
                     edgecolors='black', linewidth=0.5)
    axes[1,0].set_title('Elasticidad vs Precio Promedio')
    axes[1,0].set_xlabel('Precio Promedio ($)')
    axes[1,0].set_ylabel('Elasticidad')
    axes[1,0].grid(True, alpha=0.3)
    
    # 5. Volumen vs Elasticidad
    axes[1,1].scatter(elasticity_results['Cantidad_Total'], elasticity_results['Elasticidad'], 
                     alpha=0.7, c=elasticity_results['Venta_Total'], cmap='coolwarm', s=60,
                     edgecolors='black', linewidth=0.5)
    axes[1,1].set_title('Volumen vs Elasticidad')
    axes[1,1].set_xlabel('Cantidad Total Vendida')
    axes[1,1].set_ylabel('Elasticidad')
    axes[1,1].set_xscale('log')
    axes[1,1].grid(True, alpha=0.3)
    
    # 6. Top productos por elasticidad
    top_products = elasticity_results.nsmallest(10, 'Elasticidad')
    y_pos = np.arange(len(top_products))
    
    bars = axes[1,2].barh(y_pos, top_products['Elasticidad'], 
                         color=plt.cm.RdYlBu(np.linspace(0.2, 0.8, len(top_products))))
    axes[1,2].set_yticks(y_pos)
    axes[1,2].set_yticklabels([f'{sku[:12]}...' for sku in top_products['SKU']], fontsize=8)
    axes[1,2].set_title('Top 10 Productos Más Elásticos')
    axes[1,2].set_xlabel('Elasticidad')
    axes[1,2].grid(True, alpha=0.3)
    
    # Agregar valores en las barras
    for i, (bar, val) in enumerate(zip(bars, top_products['Elasticidad'])):
        axes[1,2].text(val - 0.1, bar.get_y() + bar.get_height()/2, 
                      f'{val:.2f}', ha='right', va='center', fontweight='bold', fontsize=8)
    
    plt.tight_layout()
    plt.show()

# Ejemplo de uso
if __name__ == "__main__":
    # Cargar datos con ruta correcta
    import os
    data_path = 'data/processed/datos_limpios.csv'
    
    if not os.path.exists(data_path):
        print(f"ERROR: No se encontro el archivo: {data_path}")
        print("Archivos disponibles en data/processed/:")
        if os.path.exists('data/processed/'):
            for file in os.listdir('data/processed/'):
                print(f"   - {file}")
        else:
            print("   - El directorio data/processed/ no existe")
        exit(1)
    
    print(f"Cargando datos desde: {data_path}")
    df_ventas = pd.read_csv(data_path)
    print(f"Datos cargados: {len(df_ventas):,} registros")
    
    # Ejecutar análisis completo
    elasticity_data, elasticity_results, price_stats = analisis_elasticidad_completo(df_ventas)
    
    # Crear visualizaciones
    if len(elasticity_results) > 0:
        crear_visualizaciones_elasticidad(elasticity_results)
    
    print('\nAnalisis completado')