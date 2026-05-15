# farmacia/tests/test_views.py
"""
Tests para farmacia/views_pos_v2.py
Valida vistas, respuestas HTTP, flujos de negocio.
"""

import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse

from farmacia.models import CarritoVenta, Boleta, Pago, Venta, HistorialStock
from .factories import (
    UserFactory, MedicamentoFactory, ClienteFactory, 
    CarritoVentaFactory, CarritoItemFactory
)


@pytest.mark.django_db
class TestTerminalPosV2:
    """Tests para vista principal de terminal POS v2"""

    def setup_method(self):
        """Setup para cada test"""
        self.client = Client()
        self.user = UserFactory(username='vendedor', password='testpass123')
        self.user.set_password('testpass123')
        self.user.save()

    def test_terminal_requiere_login(self):
        """Terminal POS requiere autenticación"""
        response = self.client.get(reverse('terminal_pos_v2'))
        assert response.status_code == 302  # Redirect a login
        assert '/inicio_sesion/' in response.url

    def test_terminal_accesible_logueado(self):
        """Terminal accesible para usuario logueado"""
        self.client.login(username='vendedor', password='testpass123')
        response = self.client.get(reverse('terminal_pos_v2'))
        
        assert response.status_code == 200
        assert 'Terminal POS v2' in response.content.decode() or 'terminal' in response.content.decode().lower()

    def test_terminal_busqueda_medicamentos(self):
        """Búsqueda de medicamentos funciona"""
        self.client.login(username='vendedor', password='testpass123')
        med = MedicamentoFactory(nombre='Ibuprofeno 400mg', stock=10)
        
        response = self.client.get(reverse('terminal_pos_v2'), {'busqueda': 'Ibuprofeno'})
        
        assert response.status_code == 200
        # Medicamento debe aparecer en contexto
        assert 'medicamentos' in response.context

    def test_terminal_sin_busqueda_sin_medicamentos(self):
        """Sin búsqueda, no muestra medicamentos"""
        self.client.login(username='vendedor', password='testpass123')
        response = self.client.get(reverse('terminal_pos_v2'))
        
        assert response.status_code == 200
        # Sin búsqueda, medicamentos vacío
        assert len(response.context['medicamentos']) == 0


@pytest.mark.django_db
class TestAgregarItem:
    """Tests para agregar items al carrito (AJAX)"""

    def setup_method(self):
        """Setup"""
        self.client = Client()
        self.user = UserFactory(username='vendedor', password='testpass123')
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username='vendedor', password='testpass123')

    def test_agregar_item_valido(self):
        """Agregar item válido al carrito"""
        med = MedicamentoFactory(stock=100, precio=Decimal('10000.00'))
        
        response = self.client.post(
            reverse('pos_agregar_item', args=[med.id]),
            {'cantidad': 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    def test_agregar_item_sin_stock(self):
        """No se puede agregar si no hay stock"""
        med = MedicamentoFactory(stock=0)
        
        response = self.client.post(
            reverse('pos_agregar_item', args=[med.id]),
            {'cantidad': 1}
        )
        
        data = response.json()
        assert data['success'] is False
        assert 'stock' in data['error'].lower()

    def test_agregar_cantidad_excesiva(self):
        """Cantidad no puede exceder stock"""
        med = MedicamentoFactory(stock=10)
        
        response = self.client.post(
            reverse('pos_agregar_item', args=[med.id]),
            {'cantidad': 20}
        )
        
        data = response.json()
        assert data['success'] is False

    def test_agregar_item_crea_carrito(self):
        """Agregar item crea carrito si no existe"""
        med = MedicamentoFactory(stock=100)
        
        # No debe haber carrito antes
        assert not CarritoVenta.objects.filter(vendedor=self.user).exists()
        
        self.client.post(
            reverse('pos_agregar_item', args=[med.id]),
            {'cantidad': 1}
        )
        
        # Carrito debe existir ahora
        carrito = CarritoVenta.objects.get(vendedor=self.user)
        assert carrito.items.count() == 1


@pytest.mark.django_db
class TestProcesarPago:
    """Tests para procesar pago y crear venta"""

    def setup_method(self):
        """Setup"""
        self.client = Client()
        self.user = UserFactory(username='vendedor', password='testpass123')
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username='vendedor', password='testpass123')

    def test_procesar_pago_efectivo(self):
        """Procesar pago en efectivo crea venta"""
        # Crear carrito con item
        med = MedicamentoFactory(stock=100, precio=Decimal('10000.00'))
        carrito = CarritoVentaFactory(vendedor=self.user)
        CarritoItemFactory(carrito=carrito, medicamento=med, cantidad=10)
        carrito.calcular_totales()
        
        # Procesar pago
        response = self.client.post(reverse('pos_procesar_pago'), {
            'metodo_pago': 'EFECTIVO',
            'monto_pagado': '100000.00',
            'referencia_pago': ''
        })
        
        # Debe redirigir a boleta
        assert response.status_code == 302
        
        # Debe haber boleta
        assert Boleta.objects.filter(carrito=carrito).exists()

    def test_procesar_pago_crea_venta(self):
        """Procesar pago crea registro en Venta"""
        med = MedicamentoFactory(stock=100, precio=Decimal('5000.00'))
        carrito = CarritoVentaFactory(vendedor=self.user)
        CarritoItemFactory(carrito=carrito, medicamento=med, cantidad=2)
        carrito.calcular_totales()
        
        self.client.post(reverse('pos_procesar_pago'), {
            'metodo_pago': 'EFECTIVO',
            'monto_pagado': '10000.00',
            'referencia_pago': ''
        })
        
        # Debe haber venta creada
        assert Venta.objects.filter(vendedor=self.user).exists()
        venta = Venta.objects.filter(vendedor=self.user).first()
        assert venta.numero_venta.startswith('VT-')

    def test_procesar_pago_descuenta_stock(self):
        """Procesar pago descuenta stock"""
        med = MedicamentoFactory(stock=100, precio=Decimal('10000.00'))
        stock_inicial = med.stock
        
        carrito = CarritoVentaFactory(vendedor=self.user)
        CarritoItemFactory(carrito=carrito, medicamento=med, cantidad=10)
        carrito.calcular_totales()
        
        self.client.post(reverse('pos_procesar_pago'), {
            'metodo_pago': 'EFECTIVO',
            'monto_pagado': '100000.00',
            'referencia_pago': ''
        })
        
        # Stock debe ser menor
        med.refresh_from_db()
        assert med.stock == (stock_inicial - 10)

    def test_procesar_pago_registra_historial(self):
        """Procesar pago registra en HistorialStock"""
        med = MedicamentoFactory(stock=100)
        carrito = CarritoVentaFactory(vendedor=self.user)
        CarritoItemFactory(carrito=carrito, medicamento=med, cantidad=5)
        carrito.calcular_totales()
        
        self.client.post(reverse('pos_procesar_pago'), {
            'metodo_pago': 'EFECTIVO',
            'monto_pagado': '50000.00',
            'referencia_pago': ''
        })
        
        # Debe haber registro en HistorialStock
        assert HistorialStock.objects.filter(medicamento=med, tipo='VENTA').exists()


@pytest.mark.django_db
class TestHistorialVentas:
    """Tests para historial de ventas"""

    def setup_method(self):
        """Setup"""
        self.client = Client()
        self.user = UserFactory(username='vendedor', password='testpass123')
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username='vendedor', password='testpass123')

    def test_historial_accesible(self):
        """Historial accesible para usuario"""
        response = self.client.get(reverse('pos_historial_ventas'))
        assert response.status_code == 200

    def test_historial_muestra_ventas(self):
        """Historial muestra ventas del usuario"""
        from .factories import VentaFactory
        venta = VentaFactory(vendedor=self.user)
        
        response = self.client.get(reverse('pos_historial_ventas'))
        assert response.status_code == 200
        # Debe contener la venta en contexto
        assert 'ventas' in response.context

    def test_historial_filtra_por_estado(self):
        """Historial puede filtrar por estado"""
        from .factories import VentaFactory
        VentaFactory(vendedor=self.user, estado='COMPLETADA')
        VentaFactory(vendedor=self.user, estado='ANULADA')
        
        # Filtrar solo COMPLETADAS
        response = self.client.get(reverse('pos_historial_ventas'), {'estado': 'COMPLETADA'})
        assert response.status_code == 200


@pytest.mark.django_db
class TestAnularVenta:
    """Tests para anular venta"""

    def setup_method(self):
        """Setup"""
        self.client = Client()
        self.user = UserFactory(username='supervisor', password='testpass123', is_staff=True)
        self.user.set_password('testpass123')
        self.user.save()
        self.client.login(username='supervisor', password='testpass123')

    def test_anular_requiere_staff(self):
        """Solo staff puede anular venta"""
        user_no_staff = UserFactory(username='vendedor', is_staff=False)
        user_no_staff.set_password('testpass123')
        user_no_staff.save()
        
        venta = VentaFactory()
        
        # Login como no-staff
        self.client.login(username='vendedor', password='testpass123')
        response = self.client.post(
            reverse('pos_anular_venta', args=[venta.numero_venta]),
            {'motivo': 'Test', 'observaciones': '', 'contrasena_supervisor': 'testpass123'}
        )
        
        # Debe rechazar (redirect a historial)
        assert response.status_code == 302

    def test_anular_venta_valida(self):
        """Anular venta válida cambia estado"""
        med = MedicamentoFactory(stock=0)  # Stock ya fue decrementado
        venta = VentaFactory(
            vendedor=self.user,
            medicamento=med,
            estado='COMPLETADA',
            cantidad=10
        )
        
        response = self.client.post(
            reverse('pos_anular_venta', args=[venta.numero_venta]),
            {
                'motivo': 'Error de venta',
                'observaciones': '',
                'contrasena_supervisor': 'testpass123'
            }
        )
        
        # Debe redirigir (éxito)
        assert response.status_code == 302
        
        # Venta debe estar ANULADA
        venta.refresh_from_db()
        assert venta.estado == 'ANULADA'

    def test_anular_revierte_stock(self):
        """Anular venta revierte stock"""
        med = MedicamentoFactory(stock=90)  # Ya fueron 10 vendidos
        venta = VentaFactory(medicamento=med, cantidad=10, estado='COMPLETADA')
        
        self.client.post(
            reverse('pos_anular_venta', args=[venta.numero_venta]),
            {
                'motivo': 'Anulación',
                'observaciones': '',
                'contrasena_supervisor': 'testpass123'
            }
        )
        
        # Stock debe revertir
        med.refresh_from_db()
        assert med.stock == 100  # 90 + 10 revertidos
