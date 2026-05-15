# farmacia/tests/test_forms.py
"""
Tests para farmacia/forms.py
Valida validaciones de formularios POS v2.
"""

import pytest
from decimal import Decimal

from farmacia.forms import (
    ProcesarPagoV2Form, AplicarDescuentoForm, SeleccionarClienteV2Form,
    AnularVentaForm, ProcesarDevolucionForm
)
from .factories import ClienteFactory, UserFactory


@pytest.mark.django_db
class TestProcesarPagoV2Form:
    """Tests para formulario de pago"""

    def test_formulario_valido_efectivo(self):
        """Formulario válido con método Efectivo"""
        data = {
            'metodo_pago': 'EFECTIVO',
            'monto_pagado': Decimal('11900.00'),
            'referencia_pago': ''
        }
        form = ProcesarPagoV2Form(data)
        assert form.is_valid()

    def test_formulario_valido_debito_con_referencia(self):
        """Débito requiere referencia"""
        data = {
            'metodo_pago': 'DEBITO',
            'monto_pagado': Decimal('11900.00'),
            'referencia_pago': 'Últimos 4: 1234'
        }
        form = ProcesarPagoV2Form(data)
        assert form.is_valid()

    def test_formulario_debito_sin_referencia_invalido(self):
        """Débito sin referencia es inválido"""
        data = {
            'metodo_pago': 'DEBITO',
            'monto_pagado': Decimal('11900.00'),
            'referencia_pago': ''
        }
        form = ProcesarPagoV2Form(data)
        assert not form.is_valid()

    def test_formulario_transferencia_requiere_referencia(self):
        """Transferencia requiere referencia"""
        data = {
            'metodo_pago': 'TRANSFERENCIA',
            'monto_pagado': Decimal('11900.00'),
            'referencia_pago': ''
        }
        form = ProcesarPagoV2Form(data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestAplicarDescuentoForm:
    """Tests para formulario de descuento"""

    def test_descuento_porcentaje_valido(self):
        """Descuento por porcentaje válido"""
        data = {
            'tipo_descuento': 'PORCENTAJE',
            'valor': Decimal('10.00'),
            'motivo': 'Cliente VIP'
        }
        form = AplicarDescuentoForm(data)
        assert form.is_valid()

    def test_descuento_monto_valido(self):
        """Descuento por monto fijo válido"""
        data = {
            'tipo_descuento': 'MONTO',
            'valor': Decimal('5000.00'),
            'motivo': 'Promoción'
        }
        form = AplicarDescuentoForm(data)
        assert form.is_valid()

    def test_porcentaje_no_puede_exceder_100(self):
        """Porcentaje no puede ser > 100%"""
        data = {
            'tipo_descuento': 'PORCENTAJE',
            'valor': Decimal('150.00'),
            'motivo': ''
        }
        form = AplicarDescuentoForm(data)
        assert not form.is_valid()

    def test_valor_negativo_invalido(self):
        """Descuento negativo es inválido"""
        data = {
            'tipo_descuento': 'PORCENTAJE',
            'valor': Decimal('-10.00'),
            'motivo': ''
        }
        form = AplicarDescuentoForm(data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestSeleccionarClienteV2Form:
    """Tests para formulario de selección de cliente"""

    def test_cliente_opcional(self):
        """Cliente es opcional"""
        data = {
            'cliente': '',
            'rut_busqueda': ''
        }
        form = SeleccionarClienteV2Form(data)
        assert form.is_valid()

    def test_cliente_seleccionado(self):
        """Cliente seleccionado del dropdown"""
        cliente = ClienteFactory()
        data = {
            'cliente': cliente.id,
            'rut_busqueda': ''
        }
        form = SeleccionarClienteV2Form(data)
        assert form.is_valid()
        assert form.cleaned_data['cliente'] == cliente

    def test_rut_busqueda_opcional(self):
        """RUT búsqueda es campo opcional"""
        data = {
            'cliente': '',
            'rut_busqueda': '12.345.678-9'
        }
        form = SeleccionarClienteV2Form(data)
        # Debería ser válido aunque RUT no se busque
        # (búsqueda se hace en vista, no en form)
        assert form.is_valid()


@pytest.mark.django_db
class TestAnularVentaForm:
    """Tests para formulario de anulación"""

    def test_anulacion_valida(self):
        """Anulación con motivo y contraseña"""
        data = {
            'motivo': 'Error de venta',
            'observaciones': 'Cliente cambió de opinión',
            'contrasena_supervisor': 'testpass123'
        }
        form = AnularVentaForm(data)
        assert form.is_valid()

    def test_motivo_requerido(self):
        """Motivo es requerido"""
        data = {
            'motivo': '',
            'observaciones': 'Alguna observación',
            'contrasena_supervisor': 'testpass123'
        }
        form = AnularVentaForm(data)
        assert not form.is_valid()

    def test_contrasena_requerida(self):
        """Contraseña supervisor es requerida"""
        data = {
            'motivo': 'Error de venta',
            'observaciones': '',
            'contrasena_supervisor': ''
        }
        form = AnularVentaForm(data)
        assert not form.is_valid()

    def test_observaciones_opcional(self):
        """Observaciones son opcionales"""
        data = {
            'motivo': 'Error',
            'observaciones': '',
            'contrasena_supervisor': 'testpass123'
        }
        form = AnularVentaForm(data)
        assert form.is_valid()


@pytest.mark.django_db
class TestProcesarDevolucionForm:
    """Tests para formulario de devolución"""

    def test_devolucion_valida(self):
        """Devolución con cantidad y motivo"""
        data = {
            'cantidad': 2,
            'motivo': 'DEFECTO',
            'observaciones': 'Producto dañado'
        }
        form = ProcesarDevolucionForm(data)
        assert form.is_valid()

    def test_cantidad_requerida(self):
        """Cantidad es requerida"""
        data = {
            'cantidad': '',
            'motivo': 'DEFECTO',
            'observaciones': ''
        }
        form = ProcesarDevolucionForm(data)
        assert not form.is_valid()

    def test_cantidad_minima_1(self):
        """Cantidad mínima es 1"""
        data = {
            'cantidad': 0,
            'motivo': 'DEFECTO',
            'observaciones': ''
        }
        form = ProcesarDevolucionForm(data)
        assert not form.is_valid()

    def test_motivo_requerido(self):
        """Motivo es requerido"""
        data = {
            'cantidad': 1,
            'motivo': '',
            'observaciones': ''
        }
        form = ProcesarDevolucionForm(data)
        assert not form.is_valid()

    def test_motivos_validos(self):
        """Todos los motivos válidos se aceptan"""
        motivos = ['DEFECTO', 'CAMBIO', 'ALERGIA', 'VENCIDO', 'ERROR', 'OTRO']
        for motivo in motivos:
            data = {
                'cantidad': 1,
                'motivo': motivo,
                'observaciones': ''
            }
            form = ProcesarDevolucionForm(data)
            assert form.is_valid(), f"Motivo {motivo} debería ser válido"
