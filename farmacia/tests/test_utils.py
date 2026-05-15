# farmacia/tests/test_utils.py
"""
Tests para farmacia/utils.py
Valida generación de números, cálculos financieros, formatos.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from farmacia.utils import (
    generar_numero_venta, generar_numero_boleta, generar_folio_boleta,
    generar_numero_nota_credito, calcular_iva, calcular_total_con_iva,
    aplicar_descuento, calcular_cambio, formato_moneda, redondear_moneda
)
from farmacia.models import Venta, Boleta, NotaCredito
from .factories import UserFactory, VentaFactory, BouletaFactory, NotaCreditoFactory


@pytest.mark.django_db
class TestGenerarNumeros:
    """Tests para generadores de números secuenciales"""

    def test_generar_numero_venta_formato(self):
        """Verifica que numero_venta tenga formato VT-YYYY-NNNNN"""
        numero = generar_numero_venta()
        
        assert numero.startswith('VT-')
        assert len(numero) == 14  # VT-2026-00001
        parts = numero.split('-')
        assert len(parts) == 3
        assert parts[0] == 'VT'
        assert parts[1] == str(datetime.now().year)
        assert parts[2].isdigit() and len(parts[2]) == 5

    def test_generar_numero_venta_incremental(self):
        """Verifica que números venta incrementen secuencialmente"""
        VentaFactory(numero_venta='VT-2026-00001')
        
        numero2 = generar_numero_venta()
        assert numero2 == 'VT-2026-00002'
        
        VentaFactory(numero_venta=numero2)
        numero3 = generar_numero_venta()
        assert numero3 == 'VT-2026-00003'

    def test_generar_numero_boleta_formato(self):
        """Verifica formato BV-YYYY-NNNNN"""
        numero = generar_numero_boleta()
        
        assert numero.startswith('BV-')
        assert len(numero) == 14
        parts = numero.split('-')
        assert parts[0] == 'BV'
        assert parts[1] == str(datetime.now().year)

    def test_generar_folio_boleta(self):
        """Verifica que folio sea secuencial"""
        folio1 = generar_folio_boleta()
        assert folio1 == 1
        
        BouletaFactory(folio=1)
        folio2 = generar_folio_boleta()
        assert folio2 == 2

    def test_generar_numero_nota_credito_formato(self):
        """Verifica formato NC-YYYY-NNNNN"""
        numero = generar_numero_nota_credito()
        
        assert numero.startswith('NC-')
        parts = numero.split('-')
        assert parts[0] == 'NC'
        assert parts[1] == str(datetime.now().year)


@pytest.mark.django_db
class TestCalculosFinancieros:
    """Tests para cálculos de IVA, descuentos, cambio"""

    def test_calcular_iva_19_porciento(self):
        """Verifica cálculo de IVA al 19%"""
        monto = Decimal('100.00')
        iva = calcular_iva(monto, 19)
        
        assert iva == Decimal('19.00')

    def test_calcular_iva_en_rango(self):
        """Valida IVA con valores reales"""
        monto = Decimal('81000.00')  # Caso real chileno
        iva = calcular_iva(monto, 19)
        
        assert iva == Decimal('15390.00')

    def test_calcular_total_con_iva(self):
        """Verifica cálculo completo de base + IVA + total"""
        monto = Decimal('81000.00')
        base, iva, total = calcular_total_con_iva(monto)
        
        assert base == Decimal('81000.00')
        assert iva == Decimal('15390.00')
        assert total == Decimal('96390.00')

    def test_aplicar_descuento_porcentaje(self):
        """Aplica descuento por porcentaje"""
        monto = Decimal('100.00')
        original, descuento, final = aplicar_descuento(monto, descuento_porcentaje=10)
        
        assert original == Decimal('100.00')
        assert descuento == Decimal('10.00')
        assert final == Decimal('90.00')

    def test_aplicar_descuento_monto(self):
        """Aplica descuento por monto fijo"""
        monto = Decimal('100.00')
        original, descuento, final = aplicar_descuento(monto, descuento_monto=25)
        
        assert original == Decimal('100.00')
        assert descuento == Decimal('25.00')
        assert final == Decimal('75.00')

    def test_aplicar_descuento_excesivo(self):
        """Si descuento > monto, se limita al monto"""
        monto = Decimal('50.00')
        original, descuento, final = aplicar_descuento(monto, descuento_monto=100)
        
        assert descuento == Decimal('50.00')  # Limited
        assert final == Decimal('0.00')

    def test_calcular_cambio_efectivo(self):
        """Calcula cambio correctamente"""
        total = Decimal('96390.00')
        pagado = Decimal('100000.00')
        cambio = calcular_cambio(total, pagado)
        
        assert cambio == Decimal('3610.00')

    def test_calcular_cambio_negativo(self):
        """Cambio negativo si pago insuficiente"""
        total = Decimal('96390.00')
        pagado = Decimal('90000.00')
        cambio = calcular_cambio(total, pagado)
        
        assert cambio == Decimal('-6390.00')


@pytest.mark.django_db
class TestFormatos:
    """Tests para funciones de formato"""

    def test_formato_moneda_chilena(self):
        """Convierte número a formato $X.XXX.XXX (chileno)"""
        assert formato_moneda(1500000) == "$1.500.000"
        assert formato_moneda(96390) == "$96.390"
        assert formato_moneda(10000) == "$10.000"

    def test_redondear_moneda_a_10(self):
        """Redondea a múltiplo de 10 (standard CLP)"""
        # Redondea hacia arriba
        assert redondear_moneda(Decimal('96.39')) == Decimal('100.00')
        # Ya redondeado
        assert redondear_moneda(Decimal('100.00')) == Decimal('100.00')
        # Redondea hacia abajo
        assert redondear_moneda(Decimal('94.00')) == Decimal('90.00')

    def test_formato_moneda_con_ceros(self):
        """Maneja correctamente números pequeños"""
        assert formato_moneda(0) == "$0"
        assert formato_moneda(100) == "$100"
        assert formato_moneda(1000) == "$1.000"


@pytest.mark.django_db
class TestValidaciones:
    """Tests para validaciones"""

    def test_validar_stock_carrito_ok(self):
        """Valida que hay stock suficiente"""
        from farmacia.models import CarritoVenta
        from .factories import CarritoVentaFactory, CarritoItemFactory, MedicamentoFactory
        
        med = MedicamentoFactory(stock=100)
        carrito = CarritoVentaFactory()
        CarritoItemFactory(carrito=carrito, medicamento=med, cantidad=50)
        
        from farmacia.utils import validar_stock_carrito
        es_valido, mensajes = validar_stock_carrito(carrito)
        
        assert es_valido is True
        assert len(mensajes) == 0

    def test_validar_stock_carrito_insuficiente(self):
        """Detecta stock insuficiente"""
        from farmacia.models import CarritoVenta
        from .factories import CarritoVentaFactory, CarritoItemFactory, MedicamentoFactory
        
        med = MedicamentoFactory(stock=10)
        carrito = CarritoVentaFactory()
        CarritoItemFactory(carrito=carrito, medicamento=med, cantidad=50)
        
        from farmacia.utils import validar_stock_carrito
        es_valido, mensajes = validar_stock_carrito(carrito)
        
        assert es_valido is False
        assert len(mensajes) > 0
