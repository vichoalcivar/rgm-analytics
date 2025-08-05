#!/usr/bin/env python3
"""
Análisis de elasticidad mejorado con datos reales
Incluye múltiples enfoques para obtener resultados más robustos
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def clean_numeric_columns(df, numeric_cols):
    """Convierte columnas numéricas que usan coma como separador decimal"""
    df_clean = df.copy()
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str)
            df_clean[col] = df_clean[col].str.replace(',', '.', regex=False)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    return df_clean

def calculate_elasticity_advanced(sku_data, method='percentile'):
    """
    Calcula elasticidad usando diferentes métodos de segmentación
    """
    if len(sku_data) < 10:  # Mínimo de datos
        return None
        
    # Método 1: Segmentación por percentiles
    if method == 'percentile':
        # Crear múltiples segmentos basados en percentiles
        percentiles = [0, 20, 40, 60, 80, 100]
        sku_data['Precio_Bin'] = pd.cut(
            sku_data['PRECIO'], 
            bins=np.percentile(sku_data['PRECIO'], percentiles),
            labels=False,
            include_lowest=True,
            duplicates='drop'
        )
        
    # Método 2: Segmentación por rangos fijos
    elif method == 'fixed_bins':
        n_bins = min(5, sku_data['PRECIO'].nunique())
        sku_data['Precio_Bin'] = pd.cut(sku_data['PRECIO'], bins=n_bins, labels=False)
        
    # Método 3: Segmentación por desviación estándar
    elif method == 'std_based':
        mean_price = sku_data['PRECIO'].mean()
        std_price = sku_data['PRECIO'].std()
        
        bins = [
            sku_data['PRECIO'].min(),
            mean_price - std_price,
            mean_price,
            mean_price + std_price,
            sku_data['PRECIO'].max()
        ]
        bins = sorted(list(set(bins)))  # Remover duplicados
        
        if len(bins) < 3:
            return None
            
        sku_data['Precio_Bin'] = pd.cut(sku_data['PRECIO'], bins=bins, labels=False, include_lowest=True)
    
    # Agregar datos por segmento
    agg_data = sku_data.groupby('Precio_Bin').agg({
        'PRECIO': ['mean', 'count'],
        'QTY_ENTREGADA': 'sum',
        'IMPORTE': 'sum'
    }).reset_index()
    
    # Aplanar columnas
    agg_data.columns = ['Precio_Bin', 'Precio_Medio', 'Transacciones', 'Cantidad_Total', 'Importe_Total']
    agg_data = agg_data.dropna()
    
    # Filtrar segmentos con datos insuficientes
    agg_data = agg_data[agg_data['Transacciones'] >= 2]
    
    if len(agg_data) < 3 or agg_data['Precio_Medio'].std() == 0:
        return None
    
    try:
        # Calcular elasticidad usando regresión log-log
        log_price = np.log(agg_data['Precio_Medio'])
        log_qty = np.log(agg_data['Cantidad_Total'])
        
        # Verificar que los logs son válidos
        if log_price.isna().any() or log_qty.isna().any():
            return None
        
        X = log_price.values.reshape(-1, 1)
        y = log_qty.values
        
        model = LinearRegression().fit(X, y)
        elasticity = model.coef_[0]
        r2 = model.score(X, y)
        
        return {
            'elasticity': elasticity,
            'r2': r2,
            'segments': len(agg_data),
            'method': method,
            'agg_data': agg_data
        }
        
    except Exception as e:
        return None

def analyze_product_elasticity(df, sku):
    """Analiza elasticidad de un producto usando múltiples métodos"""
    sku_data = df[df['SKU'] == sku].copy()
    
    if len(sku_data) < 10:
        return None
    
    results = {}
    methods = ['percentile', 'fixed_bins', 'std_based']
    
    for method in methods:
        result = calculate_elasticity_advanced(sku_data, method)
        if result is not None:
            results[method] = result
    
    if not results:
        return None
    
    # Seleccionar mejor resultado (mayor R²)
    best_method = max(results.keys(), key=lambda x: results[x]['r2'])
    best_result = results[best_method]
    
    return {
        'SKU': sku,
        'elasticity': best_result['elasticity'],
        'r2': best_result['r2'],
        'segments': best_result['segments'],
        'method': best_result['method'],
        'transactions': len(sku_data),
        'price_mean': sku_data['PRECIO'].mean(),
        'price_std': sku_data['PRECIO'].std(),
        'price_cv': sku_data['PRECIO'].std() / sku_data['PRECIO'].mean(),
        'qty_total': sku_data['QTY_ENTREGADA'].sum(),
        'all_methods': {k: v['elasticity'] for k, v in results.items()}
    }

# ============================================================================
# ANÁLISIS PRINCIPAL
# ============================================================================

print("="*70)
print("ANÁLISIS AVANZADO DE ELASTICIDAD PRECIO-DEMANDA")
print("="*70)

# Cargar datos
print("\n1. Cargando datos...")
df_ventas = pd.read_csv('data/processed/datos_limpios.csv', nrows=100000)  # Más datos
print(f"   Datos cargados: {len(df_ventas):,} registros")

# Limpiar datos
print("\n2. Limpiando datos...")
numeric_columns = ['PRECIO', 'QTY_ENTREGADA', 'IMPORTE']
df_ventas = clean_numeric_columns(df_ventas, numeric_columns)

# Filtrar datos válidos
df_clean = df_ventas[
    (df_ventas['PRECIO'] > 0) & 
    (df_ventas['QTY_ENTREGADA'] > 0) & 
    (df_ventas['IMPORTE'] > 0) &
    df_ventas['PRECIO'].notna() & 
    df_ventas['QTY_ENTREGADA'].notna()
].copy()

print(f"   Registros válidos: {len(df_clean):,}")

# Análisis de productos candidatos
print("\n3. Identificando productos candidatos...")
product_stats = df_clean.groupby('SKU').agg({
    'PRECIO': ['count', 'mean', 'std', 'min', 'max', 'nunique'],
    'QTY_ENTREGADA': 'sum',
    'IMPORTE': 'sum'
}).reset_index()

# Aplanar columnas
product_stats.columns = ['SKU', 'transacciones', 'precio_medio', 'precio_std', 
                        'precio_min', 'precio_max', 'precios_unicos', 
                        'cantidad_total', 'importe_total']

# Calcular métricas
product_stats['precio_cv'] = product_stats['precio_std'] / product_stats['precio_medio']
product_stats['rango_precio_pct'] = (product_stats['precio_max'] - product_stats['precio_min']) / product_stats['precio_medio']

# Criterios más flexibles
candidates = product_stats[
    (product_stats['transacciones'] >= 15) &  # Mínimo 15 transacciones
    (product_stats['precio_cv'] >= 0.1) &     # CV mínimo 10%
    (product_stats['precios_unicos'] >= 3) &  # Al menos 3 precios diferentes
    (product_stats['rango_precio_pct'] >= 0.2)  # Rango mínimo 20%
]

print(f"   Productos candidatos: {len(candidates)}")

if len(candidates) == 0:
    print("   >> Relajando criterios...")
    candidates = product_stats[
        (product_stats['transacciones'] >= 10) &
        (product_stats['precio_cv'] >= 0.05) &
        (product_stats['precios_unicos'] >= 2)
    ]
    print(f"   Productos candidatos (criterios relajados): {len(candidates)}")

if len(candidates) > 0:
    # Mostrar top candidatos
    print(f"\n   Top 10 candidatos por variabilidad de precio:")
    top_candidates = candidates.nlargest(10, 'precio_cv')
    print(f"   {'SKU':<15} {'Trans':<8} {'CV':<8} {'Rango%':<10} {'Precios':<8} {'Precio$':<10}")
    print("   " + "-"*65)
    
    for _, row in top_candidates.iterrows():
        print(f"   {row['SKU'][:14]:<15} {row['transacciones']:<8.0f} {row['precio_cv']:<8.3f} {row['rango_precio_pct']*100:<10.1f} {row['precios_unicos']:<8.0f} {row['precio_medio']:<10.2f}")

    # Calcular elasticidades
    print(f"\n4. Calculando elasticidades...")
    elasticity_results = []
    
    # Analizar top 20 productos
    skus_to_analyze = candidates.nlargest(20, 'precio_cv')['SKU'].tolist()
    
    for i, sku in enumerate(skus_to_analyze):
        print(f"   Analizando {i+1}/{len(skus_to_analyze)}: {sku}")
        result = analyze_product_elasticity(df_clean, sku)
        if result is not None:
            elasticity_results.append(result)
    
    print(f"   Elasticidades calculadas: {len(elasticity_results)}")
    
    if len(elasticity_results) > 0:
        # Crear DataFrame de resultados
        results_df = pd.DataFrame(elasticity_results)
        
        # Filtrar resultados válidos
        valid_results = results_df[
            (results_df['r2'] >= 0.4) &  # R² mínimo 0.4
            (results_df['elasticity'] < 0) &  # Elasticidad negativa (normal)
            (results_df['elasticity'] > -5) &  # Elasticidad razonable
            (results_df['segments'] >= 3)  # Mínimo 3 segmentos
        ]
        
        if len(valid_results) > 0:
            print(f"\n5. RESULTADOS FINALES ({len(valid_results)} productos)")
            print("="*100)
            print(f"{'SKU':<15} {'Elasticidad':<12} {'R²':<8} {'Método':<12} {'Segms':<8} {'Trans':<8} {'Precio$':<10}")
            print("-"*100)
            
            for _, row in valid_results.sort_values('elasticity').iterrows():
                print(f"{row['SKU'][:14]:<15} {row['elasticity']:<12.3f} {row['r2']:<8.3f} {row['method']:<12} {row['segments']:<8} {row['transactions']:<8} {row['price_mean']:<10.2f}")
            
            # Estadísticas
            print(f"\nRESUMEN ESTADÍSTICO:")
            print(f"- Elasticidad promedio: {valid_results['elasticity'].mean():.3f}")
            print(f"- Elasticidad mediana: {valid_results['elasticity'].median():.3f}")
            print(f"- R² promedio: {valid_results['r2'].mean():.3f}")
            
            # Categorización
            inelastic = (valid_results['elasticity'] > -1).sum()
            moderate = ((valid_results['elasticity'] <= -1) & (valid_results['elasticity'] > -2)).sum()
            elastic = (valid_results['elasticity'] <= -2).sum()
            
            print(f"- Inelásticos (|E| < 1): {inelastic}/{len(valid_results)} ({inelastic/len(valid_results)*100:.1f}%)")
            print(f"- Moderadamente elásticos (1 < |E| < 2): {moderate}/{len(valid_results)} ({moderate/len(valid_results)*100:.1f}%)")
            print(f"- Elásticos (|E| > 2): {elastic}/{len(valid_results)} ({elastic/len(valid_results)*100:.1f}%)")
            
            # Guardar resultados
            valid_results.to_csv('resultados_elasticidad.csv', index=False)
            print(f"\n>> Resultados guardados en 'resultados_elasticidad.csv'")
            
        else:
            print("\n>> No se encontraron productos con elasticidad válida")
            print("   Mostrando todos los resultados calculados:")
            
            if len(results_df) > 0:
                print(f"\n{'SKU':<15} {'Elasticidad':<12} {'R²':<8} {'Método':<12}")
                print("-"*50)
                for _, row in results_df.iterrows():
                    print(f"{row['SKU'][:14]:<15} {row['elasticity']:<12.3f} {row['r2']:<8.3f} {row['method']:<12}")
    else:
        print("\n>> No se pudieron calcular elasticidades")
else:
    print("\n>> No hay productos viables con los criterios establecidos")

print(f"\n{'='*70}")
print("ANÁLISIS COMPLETADO")
print(f"{'='*70}")