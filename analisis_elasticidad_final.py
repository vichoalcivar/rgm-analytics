#!/usr/bin/env python3
"""
Análisis de Elasticidad Precio-Demanda - Versión Final Optimizada
Para uso con datos reales de RGM Analytics
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class ElasticityAnalyzer:
    """Analizador de elasticidad precio-demanda optimizado para datos reales"""
    
    def __init__(self, min_transactions=20, min_r2=0.3):
        self.min_transactions = min_transactions
        self.min_r2 = min_r2
        self.results = []
        
    def clean_numeric_data(self, df, columns):
        """Limpia columnas numéricas"""
        df_clean = df.copy()
        for col in columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '.', regex=False)
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        return df_clean
    
    def create_price_segments(self, prices, method='dynamic'):
        """Crea segmentos de precios optimizados"""
        unique_prices = prices.nunique()
        
        if method == 'dynamic':
            if unique_prices >= 8:
                # Usar deciles para muchos precios únicos
                return pd.qcut(prices, q=5, labels=False, duplicates='drop')
            elif unique_prices >= 5:
                # Usar cuartiles
                return pd.qcut(prices, q=4, labels=False, duplicates='drop')
            elif unique_prices >= 3:
                # Usar terciles
                return pd.qcut(prices, q=3, labels=False, duplicates='drop')
            else:
                return None
                
        elif method == 'percentile':
            # Usar percentiles específicos
            percentiles = [0, 25, 50, 75, 100]
            try:
                return pd.cut(prices, bins=np.percentile(prices, percentiles), 
                            labels=False, include_lowest=True, duplicates='drop')
            except:
                return None
                
        elif method == 'equal_width':
            # Bins de ancho igual
            try:
                return pd.cut(prices, bins=5, labels=False)
            except:
                return None
                
    def calculate_elasticity_robust(self, sku_data):
        """Calcula elasticidad usando método robusto"""
        methods = ['dynamic', 'percentile', 'equal_width']
        best_result = None
        best_r2 = -1
        
        for method in methods:
            try:
                # Crear segmentos
                segments = self.create_price_segments(sku_data['PRECIO'], method)
                if segments is None:
                    continue
                    
                sku_data_temp = sku_data.copy()
                sku_data_temp['Price_Segment'] = segments
                
                # Agregar por segmento
                agg_data = sku_data_temp.groupby('Price_Segment').agg({
                    'PRECIO': 'mean',
                    'QTY_ENTREGADA': 'sum',
                    'IMPORTE': 'sum'
                }).reset_index()
                
                # Filtrar segmentos válidos
                agg_data = agg_data[
                    (agg_data['PRECIO'] > 0) & 
                    (agg_data['QTY_ENTREGADA'] > 0)
                ].dropna()
                
                if len(agg_data) < 3:
                    continue
                
                # Calcular elasticidad
                log_price = np.log(agg_data['PRECIO'])
                log_qty = np.log(agg_data['QTY_ENTREGADA'])
                
                if log_price.std() == 0 or log_qty.std() == 0:
                    continue
                
                X = log_price.values.reshape(-1, 1)
                y = log_qty.values
                
                model = LinearRegression().fit(X, y)
                elasticity = model.coef_[0]
                r2 = model.score(X, y)
                
                if r2 > best_r2:
                    best_r2 = r2
                    best_result = {
                        'elasticity': elasticity,
                        'r2': r2,
                        'method': method,
                        'segments': len(agg_data),
                        'agg_data': agg_data
                    }
                    
            except Exception as e:
                continue
        
        return best_result
    
    def analyze_product(self, df, sku):
        """Analiza elasticidad de un producto específico"""
        sku_data = df[df['SKU'] == sku].copy()
        
        if len(sku_data) < self.min_transactions:
            return None
            
        # Estadísticas básicas
        price_stats = {
            'mean': sku_data['PRECIO'].mean(),
            'std': sku_data['PRECIO'].std(),
            'cv': sku_data['PRECIO'].std() / sku_data['PRECIO'].mean(),
            'min': sku_data['PRECIO'].min(),
            'max': sku_data['PRECIO'].max(),
            'unique': sku_data['PRECIO'].nunique(),
            'range_pct': (sku_data['PRECIO'].max() - sku_data['PRECIO'].min()) / sku_data['PRECIO'].mean()
        }
        
        # Calcular elasticidad
        elasticity_result = self.calculate_elasticity_robust(sku_data)
        
        if elasticity_result is None or elasticity_result['r2'] < self.min_r2:
            return None
        
        return {
            'SKU': sku,
            'elasticity': elasticity_result['elasticity'],
            'r2': elasticity_result['r2'],
            'method': elasticity_result['method'],
            'segments': elasticity_result['segments'],
            'transactions': len(sku_data),
            'price_mean': price_stats['mean'],
            'price_cv': price_stats['cv'],
            'price_range_pct': price_stats['range_pct'],
            'quantity_total': sku_data['QTY_ENTREGADA'].sum(),
            'revenue_total': sku_data['IMPORTE'].sum()
        }
    
    def run_analysis(self, df, max_products=50):
        """Ejecuta análisis completo"""
        print("="*80)
        print("ANÁLISIS DE ELASTICIDAD PRECIO-DEMANDA - RGM ANALYTICS")
        print("="*80)
        
        # Limpiar datos
        print("\n1. Preparando datos...")
        numeric_cols = ['PRECIO', 'QTY_ENTREGADA', 'IMPORTE']
        df_clean = self.clean_numeric_data(df, numeric_cols)
        
        # Filtrar datos válidos
        df_valid = df_clean[
            (df_clean['PRECIO'] > 0) & 
            (df_clean['QTY_ENTREGADA'] > 0) & 
            (df_clean['IMPORTE'] > 0) &
            df_clean['PRECIO'].notna() & 
            df_clean['QTY_ENTREGADA'].notna()
        ].copy()
        
        print(f"   Registros válidos: {len(df_valid):,} de {len(df):,}")
        
        # Identificar productos candidatos
        print("\n2. Identificando productos candidatos...")
        product_summary = df_valid.groupby('SKU').agg({
            'PRECIO': ['count', 'mean', 'std', 'nunique', 'min', 'max'],
            'QTY_ENTREGADA': 'sum',
            'IMPORTE': 'sum'
        }).reset_index()
        
        # Aplanar columnas
        product_summary.columns = ['SKU', 'transactions', 'price_mean', 'price_std', 
                                 'price_unique', 'price_min', 'price_max', 
                                 'qty_total', 'revenue_total']
        
        # Calcular métricas
        product_summary['price_cv'] = product_summary['price_std'] / product_summary['price_mean']
        product_summary['price_range_pct'] = (product_summary['price_max'] - product_summary['price_min']) / product_summary['price_mean']
        
        # Filtros progresivos
        candidates = product_summary[
            (product_summary['transactions'] >= self.min_transactions) &
            (product_summary['price_cv'] >= 0.15) &  # CV mínimo 15%
            (product_summary['price_unique'] >= 4) &  # Al menos 4 precios únicos
            (product_summary['price_range_pct'] >= 0.3)  # Rango mínimo 30%
        ]
        
        if len(candidates) < 5:
            print("   >> Relajando criterios...")
            candidates = product_summary[
                (product_summary['transactions'] >= 15) &
                (product_summary['price_cv'] >= 0.1) &
                (product_summary['price_unique'] >= 3) &
                (product_summary['price_range_pct'] >= 0.2)
            ]
        
        if len(candidates) < 3:
            print("   >> Relajando más criterios...")
            candidates = product_summary[
                (product_summary['transactions'] >= 10) &
                (product_summary['price_cv'] >= 0.05) &
                (product_summary['price_unique'] >= 2)
            ]
        
        print(f"   Productos candidatos: {len(candidates)}")
        
        if len(candidates) == 0:
            print("   >> No hay productos viables")
            return pd.DataFrame()
        
        # Mostrar top candidatos
        top_candidates = candidates.nlargest(min(15, len(candidates)), 'price_cv')
        print(f"\n   Top candidatos:")
        print(f"   {'SKU':<15} {'Trans':<8} {'CV':<8} {'Rango%':<8} {'Precios':<8} {'Precio$':<10}")
        print("   " + "-"*65)
        
        for _, row in top_candidates.iterrows():
            print(f"   {row['SKU'][:14]:<15} {row['transactions']:<8.0f} {row['price_cv']:<8.3f} {row['price_range_pct']*100:<8.1f} {row['price_unique']:<8.0f} {row['price_mean']:<10.2f}")
        
        # Análisis de elasticidad
        print(f"\n3. Calculando elasticidades...")
        skus_to_analyze = candidates.nlargest(max_products, 'price_cv')['SKU'].tolist()
        
        results = []
        for i, sku in enumerate(skus_to_analyze):
            if i % 10 == 0:
                print(f"   Progreso: {i+1}/{len(skus_to_analyze)}")
            
            result = self.analyze_product(df_valid, sku)
            if result is not None:
                results.append(result)
        
        if not results:
            print("   >> No se calcularon elasticidades válidas")
            return pd.DataFrame()
        
        results_df = pd.DataFrame(results)
        
        # Filtros más permisivos para datos reales
        valid_results = results_df[
            (results_df['elasticity'] > -20) &  # Eliminar valores extremos
            (results_df['elasticity'] < 20) &   # Tanto negativos como positivos
            (results_df['r2'] >= 0.05)  # R² muy bajo pero aceptable
        ].copy()
        
        if len(valid_results) == 0:
            print("   >> No hay resultados que pasen los filtros mínimos")
            print("   Mostrando todos los resultados calculados:")
            valid_results = results_df.copy()
        else:
            print(f"   >> Resultados válidos encontrados: {len(valid_results)}")
            
            # Separar resultados por tipo de elasticidad
            negative_elasticity = valid_results[valid_results['elasticity'] < 0]
            positive_elasticity = valid_results[valid_results['elasticity'] > 0]
            
            if len(negative_elasticity) > 0:
                print(f"   >> Productos con elasticidad negativa (normal): {len(negative_elasticity)}")
            if len(positive_elasticity) > 0:
                print(f"   >> Productos con elasticidad positiva (atípica): {len(positive_elasticity)}")
                
            # Priorizar resultados con elasticidad negativa si existen
            if len(negative_elasticity) > 0:
                valid_results = negative_elasticity.copy()
        
        # Categorizar elasticidades
        def categorize_elasticity(e):
            if e > -0.5:
                return "Muy Inelástico"
            elif e > -1.0:
                return "Inelástico"
            elif e > -2.0:
                return "Elástico"
            else:
                return "Muy Elástico"
        
        valid_results['category'] = valid_results['elasticity'].apply(categorize_elasticity)
        
        self.results = valid_results.copy()
        return valid_results
    
    def print_results(self):
        """Imprime resultados formateados"""
        if len(self.results) == 0:
            print("No hay resultados para mostrar")
            return
        
        print(f"\n4. RESULTADOS DE ELASTICIDAD ({len(self.results)} productos)")
        print("="*100)
        print(f"{'SKU':<15} {'Elasticidad':<12} {'R²':<8} {'Categoría':<15} {'Método':<12} {'Trans':<8} {'Precio$':<10}")
        print("-"*100)
        
        for _, row in self.results.sort_values('elasticity').iterrows():
            print(f"{row['SKU'][:14]:<15} {row['elasticity']:<12.3f} {row['r2']:<8.3f} {row['category']:<15} {row['method']:<12} {row['transactions']:<8.0f} {row['price_mean']:<10.2f}")
        
        # Estadísticas
        print(f"\nRESUMEN ESTADÍSTICO:")
        print(f"   - Elasticidad promedio: {self.results['elasticity'].mean():.3f}")
        print(f"   - Elasticidad mediana: {self.results['elasticity'].median():.3f}")
        print(f"   - Desviación estándar: {self.results['elasticity'].std():.3f}")
        print(f"   - R² promedio: {self.results['r2'].mean():.3f}")
        
        # Distribución por categorías
        cat_dist = self.results['category'].value_counts()
        print(f"\nDISTRIBUCIÓN POR CATEGORÍA:")
        for cat, count in cat_dist.items():
            pct = count / len(self.results) * 100
            print(f"   - {cat}: {count} productos ({pct:.1f}%)")
        
        # Insights de negocio
        print(f"\nINSIGHTS DE NEGOCIO:")
        avg_elasticity = self.results['elasticity'].mean()
        if avg_elasticity > -1:
            print("   - La mayoría de productos son relativamente inelásticos")
            print("   - Hay oportunidad para aumentos de precio moderados")
        else:
            print("   - Los productos muestran elasticidad significativa")
            print("   - Los cambios de precio tendrán impacto notable en la demanda")
        
        most_elastic = self.results.loc[self.results['elasticity'].idxmin()]
        least_elastic = self.results.loc[self.results['elasticity'].idxmax()]
        
        print(f"   - Producto más elástico: {most_elastic['SKU']} (E = {most_elastic['elasticity']:.3f})")
        print(f"   - Producto menos elástico: {least_elastic['SKU']} (E = {least_elastic['elasticity']:.3f})")
    
    def save_results(self, filename='elasticidad_resultados.csv'):
        """Guarda resultados en CSV"""
        if len(self.results) > 0:
            self.results.to_csv(filename, index=False)
            print(f"\nResultados guardados en: {filename}")

# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    # Cargar datos
    print("Cargando datos...")
    try:
        # Usar más datos para mejor análisis
        df = pd.read_csv('data/processed/datos_limpios.csv', nrows=200000)
        print(f"Datos cargados: {len(df):,} registros")
        
        # Crear analizador con parámetros muy flexibles para datos reales
        analyzer = ElasticityAnalyzer(min_transactions=10, min_r2=0.1)
        
        # Ejecutar análisis
        results = analyzer.run_analysis(df, max_products=30)
        
        # Mostrar resultados
        analyzer.print_results()
        
        # Guardar resultados
        analyzer.save_results()
        
        print(f"\n{'='*80}")
        print("ANÁLISIS COMPLETADO EXITOSAMENTE")
        print(f"{'='*80}")
        
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'data/processed/datos_limpios.csv'")
    except Exception as e:
        print(f"Error durante el análisis: {str(e)}")