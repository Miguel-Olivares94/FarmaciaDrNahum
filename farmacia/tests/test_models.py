# farmacia/tests/test_models.py
"""
Tests para farmacia/models.py
Valida modelos, relaciones, y métodos.
"""

import pytest
from decimal import Decimal

from farmacia.models import CarritoVenta, Medicamento, Venta
from .factories import (
    CarritoVentaFactory, CarritoItemFactory, MedicamentoFactory,
    UserFactory, ClienteFactory, VentaFactory, BouletaFactory
)


@pytest.mark.django_db
class TestCarritoVenta:
    """Tests para modelo CarritoVenta"""

    def test_crear_carrito(self):
        """Crear carrito nueva para vendedor"""
        vendedor = UserFactory()
        carrito = CarritoVentaFactory(vendedor=vendedor)
        
        assert carrito.vendedor == vendedor
        assert carrito.estado == 'EN_CONSTRUCCION'
        assert carrito.total == Decimal('0.00')

    def test_carrito_con_cliente(self):
        """Carrito puede tener cliente vinculado"""
        cliente = ClienteFactory()
        carrito = CarritoVentaFactory(cliente=cliente)
        
        assert carrito.cliente == cliente

    def test_agregar_item_a_carrito(self):
        """Agregar medicamento al carrito"""
        med = MedicamentoFactory(precio=Decimal('10000.00'))
        carrito = CarritoVentaFactory()
        
        carrito.agregar_item(med, cantidad=2)
        
        assert carrito.items.count() == 1
        item = carrito.items.first()
        assert item.cantidad == 2
        assert item.medicamento == med

    def test_carrito_calcular_subtotal(self):
        """Calcula subtotal correctamente"""
        med = MedicamentoFactory(precio=Decimal('10000.00'))
        carrito = CarritoVentaFactory()
        carrito.agregar_item(med, cantidad=5)
        
        carrito.calcular_totales()
        assert carrito.subtotal == Decimal('50000.00')

    def test_carrito_aplicar_descuento_porcentaje(self):
        """Aplica descuento por porcentaje"""
        med = MedicamentoFactory(precio=Decimal('10000.00'))
        carrito = CarritoVentaFactory()
        carrito.agregar_item(med, cantidad=10)
        carrito.calcular_totales()
        
        carrito.aplicar_descuento(porcentaje=Decimal('10'))
        carrito.calcular_totales()
        
        assert carrito.descuento_monto == Decimal('10000.00')
        # Base = 100.000 - 10.000 = 90.000
        assert carrito.base_imponible == Decimal('90000.00')
        # IVA = 90.000 * 0.19 = 17.100
        assert carrito.iva == Decimal('17100.00')
        # Total = 90.000 + 17.100 = 107.100
        assert carrito.total == Decimal('107100.00')

    def test_carrito_calcular_iva(self):
        """IVA calculado al 19%"""
        med = MedicamentoFactory(precio=Decimal('10000.00'))
        carrito = CarritoVentaFactory()
        carrito.agregar_item(med, cantidad=8.1)  # 81.000 subtotal
        carrito.calcular_totales()
        
        # Sin descuento
        expected_iva = Decimal('81000.00') * Decimal('0.19')
        assert carrito.iva == expected_iva

    def test_eliminar_item_carrito(self):
        """Eliminar item del carrito"""
        med = MedicamentoFactory()
        carrito = CarritoVentaFactory()
        carrito.agregar_item(med, cantidad=2)
        
        assert carrito.items.count() == 1
        carrito.eliminar_item(med.id)
        assert carrito.items.count() == 0

    def test_vaciar_carrito(self):
        """Vaciar todos los items"""
        med1 = MedicamentoFactory()
        med2 = MedicamentoFactory()
        carrito = CarritoVentaFactory()
        carrito.agregar_item(med1, 2)
        carrito.agregar_item(med2, 3)
        
        assert carrito.items.count() == 2
        carrito.vaciar_carrito()
        assert carrito.items.count() == 0


@pytest.mark.django_db
class TestVenta:
    """Tests para modelo Venta"""

    def test_crear_venta(self):
        """Crear venta correctamente"""
        venta = VentaFactory()
        
        assert venta.numero_venta.startswith('VT-')
        assert venta.estado == 'COMPLETADA'
        assert venta.cantidad > 0
        assert venta.precio > 0

    def test_venta_con_boleta(self):
        """Venta vinculada a boleta"""
        boleta = BouletaFactory()
        venta = VentaFactory(boleta=boleta)
        
        assert venta.boleta == boleta

    def test_venta_anulada(self):
        """Venta puede ser anulada"""
        venta = VentaFactory(estado='COMPLETADA')
        assert venta.estado == 'COMPLETADA'
        
        venta.estado = 'ANULADA'
        venta.save()
        
        venta.refresh_from_db()
        assert venta.estado == 'ANULADA'

    def test_venta_nunca_se_borra(self):
        """Venta se cambia a ANULADA, nunca se borra"""
        venta = VentaFactory()
        venta_id = venta.id
        
        # Simular anulación
        venta.estado = 'ANULADA'
        venta.save()
        
        # Venta debe existir con estado ANULADA
        venta_recuperada = Venta.objects.get(id=venta_id)
        assert venta_recuperada.estado == 'ANULADA'

    def test_venta_sin_cliente(self):
        """Venta puede ser sin cliente (anónima)"""
        venta = VentaFactory(cliente=None)
        assert venta.cliente is None

    def test_venta_con_cliente(self):
        """Venta vinculada a cliente"""
        cliente = ClienteFactory()
        venta = VentaFactory(cliente=cliente)
        
        assert venta.cliente == cliente


@pytest.mark.django_db
class TestMedicamento:
    """Tests para modelo Medicamento"""

    def test_crear_medicamento(self):
        """Crear medicamento"""
        med = MedicamentoFactory(
            nombre='Ibuprofeno 400mg',
            stock=100,
            precio=Decimal('5000.00')
        )
        
        assert med.nombre == 'Ibuprofeno 400mg'
        assert med.stock == 100
        assert med.precio == Decimal('5000.00')

    def test_medicamento_con_stock_bajo(self):
        """Medicamento con stock bajo"""
        med = MedicamentoFactory(stock=5)
        assert med.stock == 5

    def test_medicamento_sin_stock(self):
        """Medicamento sin stock"""
        med = MedicamentoFactory(stock=0)
        assert med.stock == 0

    def test_medicamento_vencimiento(self):
        """Medicamento tiene fecha vencimiento"""
        from datetime import datetime, timedelta
        fecha_vencimiento = (datetime.now() + timedelta(days=365)).date()
        med = MedicamentoFactory(fecha_vencimiento=fecha_vencimiento)
        
        assert med.fecha_vencimiento == fecha_vencimiento


@pytest.mark.django_db
class TestRelaciones:
    """Tests para relaciones entre modelos"""

    def test_carrito_items_reverse(self):
        """Relación inversa carrito → items"""
        carrito = CarritoVentaFactory()
        CarritoItemFactory(carrito=carrito)
        CarritoItemFactory(carrito=carrito)
        
        assert carrito.items.count() == 2

    def test_carrito_usuario_relacion(self):
        """Carrito está relacionado con usuario"""
        usuario = UserFactory()
        carrito = CarritoVentaFactory(vendedor=usuario)
        
        assert carrito.vendedor == usuario
        assert usuario.carritoventa_set.filter(id=carrito.id).exists()

    def test_venta_medicamento_relacion(self):
        """Venta está relacionada con medicamento"""
        med = MedicamentoFactory()
        venta = VentaFactory(medicamento=med)
        
        assert venta.medicamento == med
        assert med.venta_set.filter(id=venta.id).exists()

    def test_venta_vendedor_relacion(self):
        """Venta está asociada con vendedor"""
        vendedor = UserFactory()
        venta = VentaFactory(vendedor=vendedor)
        
        assert venta.vendedor == vendedor
        assert vendedor.ventas_realizadas.filter(id=venta.id).exists()
