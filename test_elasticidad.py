#!/usr/bin/env python3
"""
Test rapido de analisis de elasticidad con muestra de datos
"""

import pandas as pd
import numpy as np
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

# Cargar muestra de datos
print("Cargando muestra de datos...")
df_ventas = pd.read_csv('data/processed/datos_limpios.csv', nrows=50000)  # Solo 50k registros
print(f"Datos cargados: {len(df_ventas):,} registros")

# Limpiar datos numericos
print("Limpiando formato numerico...")
numeric_columns = ['PRECIO', 'QTY_ENTREGADA', 'IMPORTE']
df_ventas = clean_numeric_columns(df_ventas, numeric_columns)

# Filtrar datos validos
print("Filtrando datos validos...")
df_clean = df_ventas[
    (df_ventas['PRECIO'] > 0) & 
    (df_ventas['QTY_ENTREGADA'] > 0) & 
    (df_ventas['IMPORTE'] > 0) &
    df_ventas['PRECIO'].notna() & 
    df_ventas['QTY_ENTREGADA'].notna() & 
    df_ventas['IMPORTE'].notna()
].copy()

print(f"Registros validos: {len(df_clean):,} de {len(df_ventas):,}")

# Analizar variabilidad por producto
print("Analizando variabilidad de precios...")
price_stats = df_clean.groupby('SKU')['PRECIO'].agg([
    'count', 'mean', 'std', 'min', 'max', 'nunique'
]).reset_index()

# Calcular métricas de variabilidad
price_stats['CV'] = price_stats['std'] / price_stats['mean']
price_stats['Rango_Pct'] = (price_stats['max'] - price_stats['min']) / price_stats['mean'] * 100

# Filtrar productos viables
viable_skus = price_stats[
    (price_stats['count'] >= 10) &  # Reducir criterios para muestra pequeña
    (price_stats['CV'] >= 0.05) &
    (price_stats['nunique'] >= 3)
]

print(f"Productos viables para elasticidad: {len(viable_skus)}")

if len(viable_skus) > 0:
    print("\nTop 5 productos con mayor variabilidad:")
    top_products = viable_skus.nlargest(5, 'CV')[['SKU', 'count', 'mean', 'CV', 'Rango_Pct', 'nunique']]
    for _, row in top_products.iterrows():
        print(f"   {row['SKU'][:15]:15} | Transacciones: {row['count']:3.0f} | CV: {row['CV']:.3f} | Rango: {row['Rango_Pct']:.1f}%")
    
    # Ejemplo de calculo de elasticidad para el primer producto
    test_sku = viable_skus.iloc[0]['SKU']
    sku_data = df_clean[df_clean['SKU'] == test_sku].copy()
    
    print(f"\nEjemplo de calculo de elasticidad para: {test_sku}")
    print(f"Transacciones: {len(sku_data)}")
    print(f"Precio min: ${sku_data['PRECIO'].min():.2f}")
    print(f"Precio max: ${sku_data['PRECIO'].max():.2f}")
    print(f"Cantidad total: {sku_data['QTY_ENTREGADA'].sum():.0f}")
    
    # Crear segmentos de precios usando percentiles más flexibles
    price_unique = sku_data['PRECIO'].nunique()
    if price_unique >= 5:
        sku_data['Precio_Segment'] = pd.qcut(sku_data['PRECIO'], q=5, labels=False, duplicates='drop')
    elif price_unique >= 3:
        sku_data['Precio_Segment'] = pd.qcut(sku_data['PRECIO'], q=3, labels=False, duplicates='drop')
    else:
        # Usar bins fijos si hay pocos precios únicos
        sku_data['Precio_Segment'] = pd.cut(sku_data['PRECIO'], bins=3, labels=False)
    
    # Agregar por segmento
    agg_data = sku_data.groupby('Precio_Segment').agg({
        'PRECIO': 'mean',
        'QTY_ENTREGADA': 'sum',
        'IMPORTE': 'sum'
    }).reset_index()
    
    # Filtrar segmentos con datos válidos
    agg_data = agg_data.dropna()
    
    print(f"\nDatos agregados por segmento:")
    for _, row in agg_data.iterrows():
        print(f"   Segmento {row['Precio_Segment']}: Precio=${row['PRECIO']:.2f}, Cantidad={row['QTY_ENTREGADA']:.0f}")
    
    # Calcular elasticidad
    if len(agg_data) >= 3 and agg_data['PRECIO'].std() > 0:
        log_price = np.log(agg_data['PRECIO'])
        log_qty = np.log(agg_data['QTY_ENTREGADA'])
        
        X = log_price.values.reshape(-1, 1)
        y = log_qty.values
        
        model = LinearRegression().fit(X, y)
        elasticity = model.coef_[0]
        r2 = model.score(X, y)
        
        print(f"\nElasticidad calculada: {elasticity:.3f}")
        print(f"R-cuadrado: {r2:.3f}")
        
        if elasticity < 0:
            if elasticity > -0.5:
                categoria = "Inelastico"
            elif elasticity > -1:
                categoria = "Poco Elastico"
            elif elasticity > -2:
                categoria = "Elastico"
            else:
                categoria = "Muy Elastico"
            
            print(f"Categoria: {categoria}")
        else:
            print("Elasticidad positiva (resultado inusual)")
    else:
        print("No hay suficientes datos para calcular elasticidad")
else:
    print("No hay productos viables con los criterios establecidos")

# Calcular elasticidad para múltiples productos
def calculate_elasticity_batch(df, skus_to_analyze):
    """
    Calcula elasticidad para múltiples SKUs
    """
    results = []
    
    for sku in skus_to_analyze:
        try:
            sku_data = df[df['SKU'] == sku].copy()
            
            # Crear segmentos dinámicamente
            price_unique = sku_data['PRECIO'].nunique()
            if price_unique < 3:
                continue
                
            if price_unique >= 5:
                sku_data['Precio_Segment'] = pd.qcut(sku_data['PRECIO'], q=5, labels=False, duplicates='drop')
            else:
                sku_data['Precio_Segment'] = pd.qcut(sku_data['PRECIO'], q=3, labels=False, duplicates='drop')
            
            # Agregar datos
            agg_data = sku_data.groupby('Precio_Segment').agg({
                'PRECIO': 'mean',
                'QTY_ENTREGADA': 'sum'
            }).reset_index().dropna()
            
            if len(agg_data) < 3 or agg_data['PRECIO'].std() == 0:
                continue
            
            # Calcular elasticidad
            log_price = np.log(agg_data['PRECIO'])
            log_qty = np.log(agg_data['QTY_ENTREGADA'])
            
            X = log_price.values.reshape(-1, 1)
            y = log_qty.values
            
            model = LinearRegression().fit(X, y)
            elasticity = model.coef_[0]
            r2 = model.score(X, y)
            
            # Categorizar
            if elasticity < 0:
                if elasticity > -0.5:
                    categoria = "Inelástico"
                elif elasticity > -1:
                    categoria = "Poco Elástico"
                elif elasticity > -2:
                    categoria = "Elástico"
                else:
                    categoria = "Muy Elástico"
            else:
                categoria = "Anómalo (positivo)"
            
            results.append({
                'SKU': sku,
                'Elasticidad': elasticity,
                'R2': r2,
                'Categoria': categoria,
                'Segmentos': len(agg_data),
                'Transacciones': len(sku_data),
                'Precio_Promedio': sku_data['PRECIO'].mean(),
                'CV_Precio': sku_data['PRECIO'].std() / sku_data['PRECIO'].mean()
            })
            
        except Exception as e:
            continue
    
    return pd.DataFrame(results)

# Calcular elasticidades para los top productos
if len(viable_skus) > 0:
    print(f"\n{'='*60}")
    print("CALCULANDO ELASTICIDADES PARA MÚLTIPLES PRODUCTOS")
    print(f"{'='*60}")
    
    top_skus = viable_skus.nlargest(10, 'CV')['SKU'].tolist()
    elasticity_results = calculate_elasticity_batch(df_clean, top_skus)
    
    if len(elasticity_results) > 0:
        # Filtrar resultados válidos
        valid_results = elasticity_results[
            (elasticity_results['R2'] > 0.3) &  # R² mínimo
            (elasticity_results['Elasticidad'] < 0) &  # Elasticidad negativa
            (elasticity_results['Elasticidad'] > -10)  # Elasticidad razonable
        ]
        
        if len(valid_results) > 0:
            print(f"\nProductos con elasticidad válida: {len(valid_results)}")
            print("\nRESULTADOS DE ELASTICIDAD:")
            print("-" * 100)
            print(f"{'SKU':<15} {'Elasticidad':<12} {'R²':<8} {'Categoría':<15} {'Trans':<8} {'Precio$':<10}")
            print("-" * 100)
            
            for _, row in valid_results.sort_values('Elasticidad').iterrows():
                print(f"{row['SKU'][:14]:<15} {row['Elasticidad']:<12.3f} {row['R2']:<8.3f} {row['Categoria']:<15} {row['Transacciones']:<8.0f} {row['Precio_Promedio']:<10.2f}")
            
            # Estadísticas resumen
            print(f"\nESTADISTICAS RESUMEN:")
            print(f"   - Elasticidad promedio: {valid_results['Elasticidad'].mean():.3f}")
            print(f"   - Elasticidad mediana: {valid_results['Elasticidad'].median():.3f}")
            print(f"   - R² promedio: {valid_results['R2'].mean():.3f}")
            print(f"   - Productos inelásticos (|E| < 1): {(valid_results['Elasticidad'] > -1).sum()}/{len(valid_results)}")
            print(f"   - Productos elásticos (|E| > 1): {(valid_results['Elasticidad'] <= -1).sum()}/{len(valid_results)}")
            
        else:
            print(">> No se encontraron productos con elasticidad válida después del filtrado")
    else:
        print(">> No se pudieron calcular elasticidades")

print("\n>> Test completado exitosamente")