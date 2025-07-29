#!/usr/bin/env python3
"""
Generate sample data for RGM Analytics Platform
This script creates realistic synthetic data for all tables
"""

import sys
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from faker import Faker
import click

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
fake = Faker('es_MX')  # Mexican Spanish locale


class RGMDataGenerator:
    """Generate synthetic RGM data"""
    
    def __init__(self, start_date: str = "2023-01-01", num_days: int = 365):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = self.start_date + timedelta(days=num_days)
        self.dates = pd.date_range(self.start_date, self.end_date, freq='D')
        
        # Initialize data containers
        self.products = []
        self.customers = []
        self.stores = []
        self.competitors = []
        self.transactions = []
        
    def generate_products(self, num_products: int = 100):
        """Generate product master data"""
        logger.info(f"Generating {num_products} products...")
        
        categories = {
            'CUIDADO_PERSONAL': {
                'subcats': ['SHAMPOO', 'JABON', 'CREMA_DENTAL', 'DESODORANTE'],
                'brands': ['BrandX', 'Premium+', 'ValueLine', 'EcoFresh'],
                'sizes': [250, 400, 500, 750, 1000],
                'price_range': (15, 150)
            },
            'LIMPIEZA_HOGAR': {
                'subcats': ['DETERGENTE', 'SUAVIZANTE', 'LIMPIADOR', 'DESINFECTANTE'],
                'brands': ['CleanMax', 'BrightHome', 'PowerClean', 'FreshAir'],
                'sizes': [500, 1000, 1500, 2000, 3000],
                'price_range': (20, 200)
            },
            'ALIMENTOS': {
                'subcats': ['ACEITE', 'CONDIMENTOS', 'CONSERVAS', 'PASTA'],
                'brands': ['Favorita', 'DelChef', 'CasaRica', 'Tradicional'],
                'sizes': [200, 500, 750, 1000],
                'price_range': (10, 100)
            }
        }
        
        product_id = 1000000
        
        for _ in range(num_products):
            category = random.choice(list(categories.keys()))
            cat_info = categories[category]
            
            product = {
                'id_sku': f"SKU-{product_id}",
                'id_producto': f"PROD-{product_id // 10}",
                'nombre_producto': self._generate_product_name(category, cat_info),
                'marca': random.choice(cat_info['brands']),
                'categoria_nivel1': category,
                'categoria_nivel2': random.choice(cat_info['subcats']),
                'tamano': random.choice(cat_info['sizes']),
                'unidad_medida': 'ML' if category == 'CUIDADO_PERSONAL' else 'GR',
                'precio_sugerido': round(random.uniform(*cat_info['price_range']), 2),
                'costo_unitario': None,  # Will be calculated
                'margen_objetivo': random.uniform(25, 40),
                'ciclo_vida': random.choice(['NUEVO', 'MADURO', 'MADURO', 'MADURO', 'DECLIVE']),
                'importancia_estrategica': random.choice(['INSIGNIA', 'CORE', 'CORE', 'CORE', 'TACTICO']),
                'fecha_lanzamiento': fake.date_between(start_date='-3y', end_date='today')
            }
            
            # Calculate cost based on target margin
            product['costo_unitario'] = round(
                product['precio_sugerido'] * (1 - product['margen_objetivo'] / 100), 2
            )
            
            self.products.append(product)
            product_id += random.randint(1, 10)
        
        self.products_df = pd.DataFrame(self.products)
        logger.info(f"✓ Generated {len(self.products)} products")
        
    def generate_customers(self, num_customers: int = 1000):
        """Generate customer master data"""
        logger.info(f"Generating {num_customers} customers...")
        
        customer_types = {
            'AUTOSERVICIO': {'weight': 0.1, 'avg_ticket': 50000, 'frequency': 7},
            'MAYORISTA': {'weight': 0.15, 'avg_ticket': 30000, 'frequency': 15},
            'TRADICIONAL': {'weight': 0.6, 'avg_ticket': 1000, 'frequency': 10},
            'CONVENIENCIA': {'weight': 0.15, 'avg_ticket': 5000, 'frequency': 5}
        }
        
        for i in range(num_customers):
            cust_type = random.choices(
                list(customer_types.keys()),
                weights=[v['weight'] for v in customer_types.values()]
            )[0]
            
            type_info = customer_types[cust_type]
            
            customer = {
                'id_cliente': f"CUST-{100000 + i}",
                'nombre_cliente': fake.company(),
                'tipo_cliente': cust_type,
                'rfc': fake.rfc(),
                'direccion': fake.address(),
                'ciudad': fake.city(),
                'estado': fake.state(),
                'codigo_postal': fake.postcode(),
                'telefono': fake.phone_number(),
                'email': fake.company_email(),
                'fecha_registro': fake.date_between(start_date='-5y', end_date='-1y'),
                'segmento_valor': random.choice(['ORO', 'PLATA', 'PLATA', 'BRONCE', 'BRONCE']),
                'ticket_promedio': round(type_info['avg_ticket'] * random.uniform(0.7, 1.3), 2),
                'frecuencia_compra_dias': round(type_info['frequency'] * random.uniform(0.8, 1.2), 1),
                'sensibilidad_precio': round(random.uniform(0.3, 0.9), 2),
                'afinidad_promociones': round(random.uniform(0.4, 0.95), 2),
                'canal_preferido': 'B2B_DIRECTO',
                'credito_limite': round(type_info['avg_ticket'] * random.uniform(10, 30), 2),
                'credito_dias': random.choice([15, 30, 45, 60]),
                'activo': True
            }
            
            self.customers.append(customer)
        
        self.customers_df = pd.DataFrame(self.customers)
        logger.info(f"✓ Generated {len(self.customers)} customers")
        
    def generate_stores(self, num_stores: int = 150):
        """Generate store/warehouse data"""
        logger.info(f"Generating {num_stores} stores...")
        
        regions = {
            'NORTE': ['Monterrey', 'Tijuana', 'Hermosillo', 'Chihuahua', 'Saltillo'],
            'CENTRO': ['CDMX', 'Guadalajara', 'Puebla', 'Querétaro', 'León'],
            'SUR': ['Mérida', 'Oaxaca', 'Tuxtla', 'Cancún', 'Veracruz'],
            'BAJIO': ['Aguascalientes', 'San Luis Potosí', 'Morelia', 'Celaya'],
            'OCCIDENTE': ['Tepic', 'Colima', 'Uruapan', 'Zamora']
        }
        
        store_types = {
            'TIENDA': {'count': int(num_stores * 0.85), 'prefix': 'STORE'},
            'CEDIS': {'count': int(num_stores * 0.1), 'prefix': 'DC'},
            'CEDIS_REGIONAL': {'count': int(num_stores * 0.05), 'prefix': 'RDC'}
        }
        
        store_id = 1
        
        for store_type, info in store_types.items():
            for _ in range(info['count']):
                region = random.choice(list(regions.keys()))
                ciudad = random.choice(regions[region])
                
                store = {
                    'id_ubicacion': f"{info['prefix']}-{store_id:03d}",
                    'nombre_ubicacion': f"{store_type} {ciudad} {store_id}",
                    'tipo_ubicacion': store_type,
                    'region': region,
                    'ciudad': ciudad,
                    'direccion': fake.street_address(),
                    'latitud': round(random.uniform(14.5, 32.7), 6),
                    'longitud': round(random.uniform(-117.0, -86.7), 6),
                    'metros_cuadrados': random.randint(200, 5000) if store_type == 'TIENDA' else random.randint(5000, 20000),
                    'capacidad_almacen': random.randint(1000, 50000),
                    'num_empleados': random.randint(5, 100),
                    'fecha_apertura': fake.date_between(start_date='-10y', end_date='-1y'),
                    'activo': True
                }
                
                self.stores.append(store)
                store_id += 1
        
        self.stores_df = pd.DataFrame(self.stores)
        logger.info(f"✓ Generated {len(self.stores)} stores")
        
    def generate_transactions(self, num_transactions: int = 100000):
        """Generate sales transactions"""
        logger.info(f"Generating {num_transactions} transactions...")
        
        # Get only active stores (tiendas)
        tiendas = [s for s in self.stores if s['tipo_ubicacion'] == 'TIENDA']
        
        for i in range(num_transactions):
            if i % 10000 == 0:
                logger.info(f"  Generated {i} transactions...")
            
            # Random date within range
            fecha = fake.date_time_between(start_date=self.start_date, end_date=self.end_date)
            
            # Select random customer and product
            customer = random.choice(self.customers)
            product = random.choice(self.products)
            store = random.choice(tiendas)
            
            # Determine if promotion
            has_promo = random.random() < 0.3
            if has_promo:
                promo_type = random.choice(['3X2', '2X1', 'DESC_20', 'DESC_30', 'DESC_50'])
                descuento = {'3X2': 33.33, '2X1': 50, 'DESC_20': 20, 'DESC_30': 30, 'DESC_50': 50}[promo_type]
            else:
                promo_type = None
                descuento = 0
            
            # Calculate quantities based on customer type
            base_qty = random.randint(1, 20) if customer['tipo_cliente'] == 'TRADICIONAL' else random.randint(10, 100)
            
            # Price variation (-5% to +5% from suggested price)
            precio_unitario = round(product['precio_sugerido'] * random.uniform(0.95, 1.05), 2)
            
            transaction = {
                'id_transaccion': f"TRX-{fecha.strftime('%Y%m%d')}-{i:06d}",
                'fecha_hora': fecha,
                'id_cliente': customer['id_cliente'],
                'id_sku': product['id_sku'],
                'id_tienda': store['id_ubicacion'],
                'id_vendedor': f"VEND-{random.randint(1, 50):03d}",
                'cantidad': base_qty,
                'precio_unitario': precio_unitario,
                'precio_regular': product['precio_sugerido'],
                'descuento_porcentaje': descuento,
                'descuento_monto': round(precio_unitario * base_qty * descuento / 100, 2),
                'id_promocion': f"PROMO-{promo_type}-{fecha.strftime('%Y%m')}" if has_promo else None,
                'subtotal': round(precio_unitario * base_qty, 2),
                'total': round(precio_unitario * base_qty * (1 - descuento / 100), 2),
                'metodo_pago': random.choice(['EFECTIVO', 'TRANSFERENCIA', 'CREDITO']),
                'tipo_transaccion': 'VENTA' if random.random() > 0.05 else 'DEVOLUCION',
                'canal': 'B2B_DIRECTO'
            }
            
            self.transactions.append(transaction)
        
        self.transactions_df = pd.DataFrame(self.transactions)
        logger.info(f"✓ Generated {len(self.transactions)} transactions")
        
    def generate_competitor_data(self):
        """Generate competitor intelligence data"""
        logger.info("Generating competitor data...")
        
        competitors = ['Competidor A', 'Competidor B', 'Competidor C', 'Marca Blanca']
        
        competitor_data = []
        
        # For each product, generate competitor prices
        for product in self.products[:50]:  # Top 50 products
            for competitor in competitors:
                for date in pd.date_range(self.start_date, self.end_date, freq='W'):
                    # Price variation vs our price
                    price_factor = random.uniform(0.85, 1.15)
                    competitor_price = round(product['precio_sugerido'] * price_factor, 2)
                    
                    # Random promotion
                    has_promo = random.random() < 0.25
                    
                    comp_record = {
                        'fecha_captura': date,
                        'competidor': competitor,
                        'sku_propio': product['id_sku'],
                        'nombre_producto_comp': f"{product['nombre_producto']} - {competitor}",
                        'precio_regular_comp': competitor_price,
                        'precio_actual_comp': competitor_price * 0.8 if has_promo else competitor_price,
                        'en_promocion': has_promo,
                        'tipo_promocion': random.choice(['2X1', '30% DESC', 'SEGUNDA 50%']) if has_promo else None,
                        'disponibilidad': random.choice(['EN_STOCK'] * 8 + ['LIMITADO'] * 1 + ['AGOTADO'] * 1),
                        'fuente_datos': random.choice(['WEB_SCRAPING', 'PANEL', 'MYSTERY_SHOPPER'])
                    }
                    
                    competitor_data.append(comp_record)
        
        self.competitor_df = pd.DataFrame(competitor_data)
        logger.info(f"✓ Generated {len(competitor_data)} competitor records")
        
    def generate_inventory_data(self):
        """Generate inventory levels"""
        logger.info("Generating inventory data...")
        
        inventory_data = []
        
        # For each product and location
        for product in self.products[:30]:  # Top 30 products
            for store in self.stores:
                if store['tipo_ubicacion'] == 'TIENDA':
                    # Daily snapshots for last 30 days
                    for days_ago in range(30):
                        date = self.end_date - timedelta(days=days_ago)
                        
                        # Base inventory based on store type
                        if store['tipo_ubicacion'] == 'CEDIS':
                            base_inventory = random.randint(1000, 5000)
                        else:
                            base_inventory = random.randint(50, 500)
                        
                        # Add some randomness
                        current_inventory = max(0, base_inventory + random.randint(-100, 100))
                        
                        inv_record = {
                            'fecha_corte': date,
                            'id_ubicacion': store['id_ubicacion'],
                            'id_sku': product['id_sku'],
                            'cantidad_disponible': current_inventory,
                            'cantidad_reservada': random.randint(0, int(current_inventory * 0.2)),
                            'cantidad_transito': random.randint(0, 200) if store['tipo_ubicacion'] == 'TIENDA' else 0,
                            'dias_inventario': round(current_inventory / random.uniform(5, 50), 1),
                            'costo_inventario': round(current_inventory * product['costo_unitario'], 2),
                            'indicador_quiebre': current_inventory < 10,
                            'indicador_exceso': current_inventory > base_inventory * 1.5
                        }
                        
                        inventory_data.append(inv_record)
        
        self.inventory_df = pd.DataFrame(inventory_data)
        logger.info(f"✓ Generated {len(inventory_data)} inventory records")
        
    def _generate_product_name(self, category: str, cat_info: dict) -> str:
        """Generate realistic product name"""
        templates = {
            'CUIDADO_PERSONAL': [
                "{brand} {subcat} {adjective} {size}ml",
                "{subcat} {brand} {benefit} {size}ml",
                "{brand} {subcat} {variant} {size}ml"
            ],
            'LIMPIEZA_HOGAR': [
                "{brand} {subcat} {power} {size}ml",
                "{subcat} {brand} {scent} {size}ml",
                "{brand} {subcat} Concentrado {size}ml"
            ],
            'ALIMENTOS': [
                "{brand} {subcat} {quality} {size}g",
                "{subcat} {brand} Premium {size}g",
                "{brand} {subcat} Tradicional {size}g"
            ]
        }
        
        adjectives = ['Ultra', 'Max', 'Plus', 'Pro', 'Fresh', 'Natural']
        benefits = ['Nutritivo', 'Reparador', 'Hidratante', 'Fortalecedor']
        variants = ['Original', 'Menta', 'Lavanda', 'Citrus', 'Aloe']
        power_words = ['Power', 'Ultra', 'Max Clean', 'Professional']
        scents = ['Limón', 'Lavanda', 'Primavera', 'Brisa Marina']
        quality = ['Extra Virgen', 'Primera Calidad', 'Selecto', 'Gourmet']
        
        template = random.choice(templates[category])
        
        return template.format(
            brand=random.choice(cat_info['brands']),
            subcat=random.choice(cat_info['subcats']),
            adjective=random.choice(adjectives),
            benefit=random.choice(benefits),
            variant=random.choice(variants),
            power=random.choice(power_words),
            scent=random.choice(scents),
            quality=random.choice(quality),
            size=random.choice(cat_info['sizes'])
        )
        
    def save_all_data(self):
        """Save all generated data to CSV files"""
        output_dir = settings.data_dir / 'synthetic'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        datasets = {
            'maestro_productos': self.products_df,
            'maestro_clientes': self.customers_df,
            'maestro_ubicaciones': self.stores_df,
            'transacciones_ventas': self.transactions_df,
            'inteligencia_competitiva': self.competitor_df,
            'niveles_inventario': self.inventory_df
        }
        
        for name, df in datasets.items():
            filepath = output_dir / f"{name}.csv"
            df.to_csv(filepath, index=False)
            logger.info(f"✓ Saved {name} to {filepath}")
            

@click.command()
@click.option('--products', default=100, help='Number of products to generate')
@click.option('--customers', default=1000, help='Number of customers to generate')
@click.option('--stores', default=150, help='Number of stores to generate')
@click.option('--transactions', default=100000, help='Number of transactions to generate')
@click.option('--start-date', default='2023-01-01', help='Start date for data generation')
@click.option('--days', default=365, help='Number of days to generate data for')
def main(products, customers, stores, transactions, start_date, days):
    """Generate sample data for RGM Analytics"""
    
    logger.info("="*50)
    logger.info("RGM Data Generator")
    logger.info("="*50)
    
    # Create generator
    generator = RGMDataGenerator(start_date=start_date, num_days=days)
    
    # Generate all data
    generator.generate_products(products)
    generator.generate_customers(customers)
    generator.generate_stores(stores)
    generator.generate_transactions(transactions)
    generator.generate_competitor_data()
    generator.generate_inventory_data()
    
    # Save to files
    generator.save_all_data()
    
    logger.info("="*50)
    logger.info("✅ Data generation completed successfully!")
    logger.info(f"📁 Data saved to: {settings.data_dir / 'synthetic'}")
    logger.info("="*50)


if __name__ == "__main__":
    main()