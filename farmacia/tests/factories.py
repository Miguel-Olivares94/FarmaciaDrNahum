# farmacia/tests/factories.py
"""
Factory Boy factories para crear objetos de test.
Permite generar datos consistentes para tests.
"""

import factory
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime, timedelta

from farmacia.models import (
    Medicamento, Proveedor, Cliente, Venta, CarritoVenta, 
    CarritoItem, Boleta, Pago, NotaCredito
)


class UserFactory(factory.django.DjangoModelFactory):
    """Factory para crear usuarios de prueba"""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = 'Test'
    last_name = 'User'
    is_staff = False
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')
        obj.save()


class ProveedorFactory(factory.django.DjangoModelFactory):
    """Factory para crear proveedores"""
    class Meta:
        model = Proveedor

    nombre = factory.Sequence(lambda n: f'Proveedor{n}')
    rut_empresa = factory.Sequence(lambda n: f'{n:02d}.000.000-0')
    email = factory.Sequence(lambda n: f'proveedor{n}@example.com')
    telefono = '562123456'
    direccion = 'Calle Test 123'
    ciudad = 'Collico'
    activo = True


class ClienteFactory(factory.django.DjangoModelFactory):
    """Factory para crear clientes"""
    class Meta:
        model = Cliente

    nombre = factory.Sequence(lambda n: f'Cliente{n}')
    apellido = 'TestApellido'
    rut_dni = factory.Sequence(lambda n: f'{n:02d}.000.000-0')
    email = factory.Sequence(lambda n: f'cliente{n}@example.com')
    numero_celular = '56912345678'
    activo = True


class MedicamentoFactory(factory.django.DjangoModelFactory):
    """Factory para crear medicamentos"""
    class Meta:
        model = Medicamento

    nombre = factory.Sequence(lambda n: f'Medicamento{n}')
    laboratorio = 'Lab Test'
    sku = factory.Sequence(lambda n: f'SKU{n:05d}')
    descripcion = 'Medicamento de prueba'
    precio = Decimal('10000.00')
    stock = 100
    fecha_vencimiento = datetime.now().date() + timedelta(days=365)
    fecha_ingreso = datetime.now().date()
    proveedor = factory.SubFactory(ProveedorFactory)


class CarritoVentaFactory(factory.django.DjangoModelFactory):
    """Factory para crear carritos de venta"""
    class Meta:
        model = CarritoVenta

    vendedor = factory.SubFactory(UserFactory)
    cliente = None  # Opcional
    estado = 'EN_CONSTRUCCION'
    subtotal = Decimal('0.00')
    descuento_porcentaje = Decimal('0.00')
    descuento_monto = Decimal('0.00')
    base_imponible = Decimal('0.00')
    iva = Decimal('0.00')
    total = Decimal('0.00')


class CarritoItemFactory(factory.django.DjangoModelFactory):
    """Factory para items del carrito"""
    class Meta:
        model = CarritoItem

    carrito = factory.SubFactory(CarritoVentaFactory)
    medicamento = factory.SubFactory(MedicamentoFactory)
    cantidad = 2
    precio_unitario = Decimal('10000.00')


class BouletaFactory(factory.django.DjangoModelFactory):
    """Factory para crear boletas"""
    class Meta:
        model = Boleta

    numero_boleta = factory.Sequence(lambda n: f'BV-2026-{n:05d}')
    folio = factory.Sequence(lambda n: n + 1)
    carrito = factory.SubFactory(CarritoVentaFactory)
    rut_farmacia = '12.345.678-9'
    nombre_farmacia = 'FARMACIA COLLICO'
    direccion_farmacia = 'Collico, Biobío'
    cliente_rut = None
    cliente_nombre = None
    subtotal = Decimal('10000.00')
    descuento = Decimal('0.00')
    base_imponible = Decimal('10000.00')
    iva = Decimal('1900.00')
    total = Decimal('11900.00')
    metodo_pago = 'EFECTIVO'
    referencia_pago = ''
    vendedor = factory.SubFactory(UserFactory)
    archivo_pdf = None


class PagoFactory(factory.django.DjangoModelFactory):
    """Factory para crear pagos"""
    class Meta:
        model = Pago

    boleta = factory.SubFactory(BouletaFactory)
    carrito = factory.SubFactory(CarritoVentaFactory)
    metodo_pago = 'EFECTIVO'
    monto = Decimal('11900.00')
    cambio = Decimal('0.00')
    referencia = ''


class VentaFactory(factory.django.DjangoModelFactory):
    """Factory para crear ventas"""
    class Meta:
        model = Venta

    medicamento = factory.SubFactory(MedicamentoFactory)
    cantidad = 2
    precio = Decimal('20000.00')
    vendedor = factory.SubFactory(UserFactory)
    cliente = factory.SubFactory(ClienteFactory)
    numero_venta = factory.Sequence(lambda n: f'VT-2026-{n:05d}')
    estado = 'COMPLETADA'
    boleta = factory.SubFactory(BouletaFactory)


class NotaCreditoFactory(factory.django.DjangoModelFactory):
    """Factory para crear notas de crédito"""
    class Meta:
        model = NotaCredito

    numero_nota = factory.Sequence(lambda n: f'NC-2026-{n:05d}')
    folio = factory.Sequence(lambda n: n + 1)
    boleta_original = factory.SubFactory(BouletaFactory)
    motivo = 'ANULACION'
    observaciones = 'Anulación de prueba'
    monto = Decimal('11900.00')
    usuario_registra = factory.SubFactory(UserFactory)
    usuario_aprueba = factory.SubFactory(UserFactory)
    aprobada = True
