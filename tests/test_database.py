"""
Tests básicos para el Database Manager
"""
import pytest
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager


@pytest.fixture
def db():
    """Fixture para crear una BD en memoria para tests"""
    db = DatabaseManager(':memory:')
    yield db


def test_crear_establecimiento(db):
    """Test: Crear un establecimiento"""
    id_est = db.create_establecimiento("Test Hotel")
    assert id_est > 0
    
    establecimiento = db.get_establecimiento_by_id(id_est)
    assert establecimiento['nombre_personalizado'] == "Test Hotel"


def test_crear_plataforma_url(db):
    """Test: Crear una URL de plataforma"""
    id_est = db.create_establecimiento("Test Hotel")
    id_url = db.create_plataforma_url(
        id_est,
        "Booking",
        "https://booking.com/test"
    )
    
    assert id_url > 0
    urls = db.get_urls_by_establecimiento(id_est)
    assert len(urls) == 1
    assert urls[0]['plataforma'] == "Booking"


def test_upsert_precio(db):
    """Test: UPSERT de precio"""
    id_est = db.create_establecimiento("Test Hotel")
    id_url = db.create_plataforma_url(id_est, "Booking", "https://booking.com/test")
    
    fecha = datetime.now()
    
    # Primer insert
    db.upsert_precio(
        id_plataforma_url=id_url,
        fecha_noche=fecha,
        precio_base=100.0,
        noches_encontradas=3
    )
    
    # Verificar
    datos = db.get_precios_by_filters(
        ids_establecimiento=[id_est],
        fecha_noche_inicio=fecha,
        fecha_noche_fin=fecha
    )
    
    assert len(datos) == 1
    assert datos[0]['precio_base'] == 100.0
    
    # Update (UPSERT)
    db.upsert_precio(
        id_plataforma_url=id_url,
        fecha_noche=fecha,
        precio_base=120.0,
        noches_encontradas=2
    )
    
    # Verificar update
    datos = db.get_precios_by_filters(
        ids_establecimiento=[id_est],
        fecha_noche_inicio=fecha,
        fecha_noche_fin=fecha
    )
    
    assert len(datos) == 1  # Debe seguir siendo 1 registro
    assert datos[0]['precio_base'] == 120.0  # Precio actualizado
    assert datos[0]['noches_encontradas'] == 2


def test_logica_48h(db):
    """Test: Lógica de frescura de 48 horas"""
    id_est = db.create_establecimiento("Test Hotel")
    id_url = db.create_plataforma_url(id_est, "Booking", "https://booking.com/test")
    
    fecha_hoy = datetime.now()
    fecha_manana = fecha_hoy + timedelta(days=1)
    fecha_pasado_manana = fecha_hoy + timedelta(days=2)
    
    # Insertar dato FRESCO (hoy)
    db.upsert_precio(id_url, fecha_manana, 100.0, 3)
    
    # Verificar que NO se necesita scrapear (dato fresco)
    fechas_a_scrapear = db.get_fechas_a_scrapear(
        id_url,
        fecha_manana,
        fecha_manana
    )
    
    assert len(fechas_a_scrapear) == 0  # No debe scrapear, dato fresco
    
    # Verificar que SÍ se necesita scrapear (fecha sin datos)
    fechas_a_scrapear = db.get_fechas_a_scrapear(
        id_url,
        fecha_pasado_manana,
        fecha_pasado_manana
    )
    
    assert len(fechas_a_scrapear) == 1  # Debe scrapear


def test_logica_ocupacion(db):
    """Test: Lógica de ocupación (precio=0 => ocupado=TRUE)"""
    id_est = db.create_establecimiento("Test Hotel")
    id_url = db.create_plataforma_url(id_est, "Booking", "https://booking.com/test")
    
    fecha = datetime.now()
    
    # Insertar precio = 0
    db.upsert_precio(id_url, fecha, 0.0, 0)
    
    # Verificar que esta_ocupado = TRUE
    datos = db.get_precios_by_filters(
        ids_establecimiento=[id_est],
        fecha_noche_inicio=fecha,
        fecha_noche_fin=fecha
    )
    
    assert len(datos) == 1
    assert datos[0]['precio_base'] == 0.0
    assert datos[0]['esta_ocupado'] == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
