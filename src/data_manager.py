"""
Sistema de almacenamiento de datos para el monitor de precios
"""
import pandas as pd
import json
from datetime import datetime
import os


class DataManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.csv_path = os.path.join(data_dir, 'price_history.csv')
        self.runs_path = os.path.join(data_dir, 'scrape_runs.json')
        
        # Crear directorio si no existe
        os.makedirs(data_dir, exist_ok=True)
        
    def save_results(self, results, property_name='unknown'):
        """
        Guarda los resultados del scraping en CSV
        
        Args:
            results: lista de dicts con los datos de precios
            property_name: nombre de la propiedad
        """
        if not results:
            return
        
        # Convertir a DataFrame
        df = pd.DataFrame(results)
        
        # Agregar nombre de propiedad
        df['property_name'] = property_name
        
        # Si el archivo existe, agregar los datos
        if os.path.exists(self.csv_path):
            existing_df = pd.read_csv(self.csv_path)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        # Guardar
        df.to_csv(self.csv_path, index=False)
        
        print(f"✓ Datos guardados en {self.csv_path}")
        
    def load_data(self):
        """
        Carga los datos históricos
        
        Returns:
            DataFrame con todos los datos o None si no existe
        """
        if os.path.exists(self.csv_path):
            return pd.read_csv(self.csv_path)
        return None

    # ====== Gestión de ejecuciones (anti-duplicado 48h) ======
    def _load_runs(self):
        """Carga el log de ejecuciones de scraping"""
        try:
            if os.path.exists(self.runs_path):
                with open(self.runs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_runs(self, runs):
        """Guarda el log de ejecuciones de scraping"""
        try:
            with open(self.runs_path, 'w', encoding='utf-8') as f:
                json.dump(runs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo guardar runs log: {e}")

    def log_scrape_run(self, property_name, start_date, end_date, nights, guests, platforms):
        """Registra una ejecución de scraping exitosa"""
        runs = self._load_runs()
        record = {
            'property_name': property_name,
            'start_date': pd.to_datetime(start_date).strftime('%Y-%m-%d'),
            'end_date': pd.to_datetime(end_date).strftime('%Y-%m-%d'),
            'nights': int(nights),
            'guests': int(guests),
            'platforms': sorted(list(platforms)),
            'ts': datetime.now().isoformat(timespec='seconds')
        }
        runs.append(record)
        self._save_runs(runs)
        return record

    def is_recent_same_run(self, property_name, start_date, end_date, nights, guests, platforms, window_hours=48):
        """Verifica si ya se ejecutó la misma configuración en las últimas window_hours horas"""
        runs = self._load_runs()
        if not runs:
            return False

        start_s = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_s = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        plat_sorted = sorted(list(platforms))
        now = datetime.now()

        for r in reversed(runs):  # revisar más recientes primero
            try:
                if (
                    r.get('property_name') == property_name and
                    r.get('start_date') == start_s and
                    r.get('end_date') == end_s and
                    int(r.get('nights', -1)) == int(nights) and
                    int(r.get('guests', -1)) == int(guests) and
                    sorted(r.get('platforms', [])) == plat_sorted
                ):
                    ts = pd.to_datetime(r.get('ts'))
                    if (now - ts).total_seconds() <= window_hours * 3600:
                        return True
            except Exception:
                continue
        return False
    
    def get_property_data(self, property_name):
        """
        Obtiene datos de una propiedad específica
        
        Args:
            property_name: nombre de la propiedad
            
        Returns:
            DataFrame filtrado o None
        """
        df = self.load_data()
        if df is not None:
            return df[df['property_name'] == property_name]
        return None
    
    def get_platform_comparison(self, property_name):
        """
        Compara precios entre plataformas para una propiedad
        
        Args:
            property_name: nombre de la propiedad
            
        Returns:
            DataFrame pivotado por plataforma
        """
        df = self.get_property_data(property_name)
        if df is not None and not df.empty:
            # Filtrar solo registros con precio válido
            df = df[df['price_usd'].notna()]
            
            # Crear pivot table
            pivot = df.pivot_table(
                values='price_usd',
                index='checkin',
                columns='platform',
                aggfunc='first'
            )
            return pivot
        return None
    
    def export_to_excel(self, property_name, output_path=None):
        """
        Exporta los datos a Excel con múltiples hojas
        
        Args:
            property_name: nombre de la propiedad
            output_path: ruta del archivo de salida
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.data_dir, f'{property_name}_{timestamp}.xlsx')
        
        df = self.get_property_data(property_name)
        
        if df is not None and not df.empty:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Hoja con todos los datos
                df.to_excel(writer, sheet_name='Datos Completos', index=False)
                
                # Hoja con comparación de plataformas
                comparison = self.get_platform_comparison(property_name)
                if comparison is not None:
                    comparison.to_excel(writer, sheet_name='Comparación Plataformas')
            
            print(f"✓ Datos exportados a {output_path}")
            return output_path
        
        return None
    
    def get_summary_stats(self, property_name):
        """
        Obtiene estadísticas resumidas por plataforma
        
        Args:
            property_name: nombre de la propiedad
            
        Returns:
            DataFrame con estadísticas
        """
        df = self.get_property_data(property_name)
        
        if df is not None and not df.empty:
            # Filtrar precios válidos
            df = df[df['price_usd'].notna()]
            
            # Calcular estadísticas por plataforma
            stats = df.groupby('platform')['price_usd'].agg([
                ('Precio Mínimo', 'min'),
                ('Precio Máximo', 'max'),
                ('Precio Promedio', 'mean'),
                ('Precio Mediano', 'median'),
                ('Cantidad Datos', 'count')
            ]).round(2)
            
            return stats
        
        return None
