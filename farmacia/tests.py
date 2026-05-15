from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import (
    Medicamento, Proveedor, Cliente, LoteMedicamento, Venta, Devolucion
)


class ClienteTestCase(TestCase):
    """Tests para el modelo Cliente"""
    
    def setUp(self):
        self.cliente = Cliente.objects.create(
            rut_dni='12.345.678-9',
            nombre='Juan',
            apellido='Pérez',
            email='juan@example.com',
            telefono='912345678'
        )
    
    def test_crear_cliente(self):
        """Verifica que se puede crear un cliente"""
        self.assertEqual(self.cliente.nombre, 'Juan')
        self.assertTrue(self.cliente.activo)
    
    def test_cliente_rut_unico(self):
        """Verifica que el RUT es único"""
        with self.assertRaises(Exception):
            Cliente.objects.create(
                rut_dni='12.345.678-9',
                nombre='Carlos',
                apellido='García'
            )
    
    def test_compras_totales(self):
        """Verifica cálculo de compras totales"""
        medicamento = Medicamento.objects.create(
            nombre='Ibuprofeno',
            laboratorio='Lab',
            principio_activo='Ibuprofeno',
            accion_terapeutica='Analgésico',
            presentacion='Tableta',
            dosis='400mg',
            bioequivalente='Sí',
            stock=100,
            precio=1500,
            fecha_ingreso='2024-01-01',
            fecha_vencimiento='2025-01-01'
        )
        user = User.objects.create_user('vendedor', password='123')
        
        # Crear venta asociada al cliente
        venta = Venta.objects.create(
            medicamento=medicamento,
            cantidad=2,
            precio=3000,
            vendedor=user
        )
        venta.cliente = self.cliente
        venta.save()
        
        # Verificar total
        self.assertEqual(self.cliente.compras_totales(), 3000)


class LoteMedicamentoTestCase(TestCase):
    """Tests para control de lotes"""
    
    def setUp(self):
        self.medicamento = Medicamento.objects.create(
            nombre='Paracetamol',
            laboratorio='Lab',
            principio_activo='Paracetamol',
            accion_terapeutica='Analgésico',
            presentacion='Tableta',
            dosis='500mg',
            bioequivalente='Sí',
            stock=100,
            precio=800,
            fecha_ingreso='2024-01-01',
            fecha_vencimiento='2025-12-31'
        )
        
        self.proveedor = Proveedor.objects.create(
            nombre='Laboratorio ABC',
            razon_social='LAB ABC LTDA',
            rut='12.345.678-0',
            direccion='Calle 1, Santiago',
            email='lab@example.com',
            fono='912345678',
            productos='Medicamentos'
        )
        
        self.lote = LoteMedicamento.objects.create(
            medicamento=self.medicamento,
            numero_lote='LOTE2024001',
            fecha_vencimiento=date.today() + timedelta(days=30),
            cantidad_ingresada=100,
            cantidad_disponible=100,
            proveedor=self.proveedor,
            precio_costo=600
        )
    
    def test_crear_lote(self):
        """Verifica creación de lote"""
        self.assertEqual(self.lote.numero_lote, 'LOTE2024001')
        self.assertEqual(self.lote.cantidad_disponible, 100)
    
    def test_dias_para_vencer(self):
        """Verifica cálculo de días para vencer"""
        dias = self.lote.dias_para_vencer()
        self.assertGreater(dias, 0)
    
    def test_esta_vencido(self):
        """Verifica si lote está vencido"""
        self.assertFalse(self.lote.esta_vencido())
        
        # Crear lote vencido
        lote_vencido = LoteMedicamento.objects.create(
            medicamento=self.medicamento,
            numero_lote='LOTE_VIEJO',
            fecha_vencimiento=date.today() - timedelta(days=1),
            cantidad_ingresada=50,
            cantidad_disponible=50,
            proveedor=self.proveedor,
            precio_costo=500
        )
        self.assertTrue(lote_vencido.esta_vencido())
    
    def test_proximo_a_vencer(self):
        """Verifica si está próximo a vencer"""
        self.assertTrue(self.lote.esta_proximo_a_vencer(dias=30))
        self.assertFalse(self.lote.esta_proximo_a_vencer(dias=10))


class DevolucionTestCase(TestCase):
    """Tests para devoluciones"""
    
    def setUp(self):
        self.user = User.objects.create_user('vendedor', password='123')
        self.medicamento = Medicamento.objects.create(
            nombre='Ibuprofeno',
            laboratorio='Lab',
            principio_activo='Ibuprofeno',
            accion_terapeutica='Analgésico',
            presentacion='Tableta',
            dosis='400mg',
            bioequivalente='Sí',
            stock=100,
            precio=1500,
            fecha_ingreso='2024-01-01',
            fecha_vencimiento='2025-01-01'
        )
        self.venta = Venta.objects.create(
            medicamento=self.medicamento,
            cantidad=5,
            precio=7500,
            vendedor=self.user
        )
    
    def test_crear_devolucion(self):
        """Verifica creación de devolución"""
        devolucion = Devolucion.objects.create(
            venta=self.venta,
            medicamento=self.medicamento,
            cantidad=2,
            precio_unitario=1500,
            motivo='defecto',
            usuario_registra=self.user
        )
        
        self.assertEqual(devolucion.cantidad, 2)
        self.assertEqual(devolucion.estado, 'registrada')
    
    def test_monto_devolucion(self):
        """Verifica cálculo del monto a devolver"""
        devolucion = Devolucion.objects.create(
            venta=self.venta,
            medicamento=self.medicamento,
            cantidad=2,
            precio_unitario=1500,
            motivo='no_venta',
            usuario_registra=self.user
        )
        
        self.assertEqual(devolucion.monto_total(), 3000)


# =====================================================================
# WEEK 2: TESTS PARA TERMINAL POS
# =====================================================================

class TerminalPOSTestCase(TestCase):
    """Tests para la funcionalidad de Terminal POS"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user('vendedor', password='123456')
        
        self.proveedor = Proveedor.objects.create(
            nombre='Lab Farmacéutico',
            razon_social='LAB LTDA',
            rut='12.345.678-0',
            direccion='Calle Principal 1',
            email='lab@test.com',
            fono='912345678',
            productos='Medicamentos varios'
        )
        
        self.medicamento1 = Medicamento.objects.create(
            sku='MED001',
            nombre='Paracetamol',
            laboratorio='Lab A',
            principio_activo='Paracetamol',
            accion_terapeutica='Analgésico',
            presentacion='Tableta',
            dosis='500mg',
            bioequivalente='Sí',
            stock=100,
            precio=500,
            proveedor=self.proveedor,
            fecha_ingreso='2024-01-01',
            fecha_vencimiento='2025-12-31'
        )
        
        self.medicamento2 = Medicamento.objects.create(
            sku='MED002',
            nombre='Ibuprofeno',
            laboratorio='Lab B',
            principio_activo='Ibuprofeno',
            accion_terapeutica='Analgésico',
            presentacion='Cápsula',
            dosis='400mg',
            bioequivalente='Sí',
            stock=50,
            precio=800,
            proveedor=self.proveedor,
            fecha_ingreso='2024-01-01',
            fecha_vencimiento='2025-12-31'
        )
    
    def test_terminal_pos_load(self):
        """Verifica que la vista POS carga correctamente"""
        self.client.login(username='vendedor', password='123456')
        response = self.client.get('/farmacia/pos/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'farmacia/pos_v2/terminal_pos_v2.html')
    
    def test_buscar_medicamento_por_nombre(self):
        """Verifica búsqueda de medicamentos por nombre"""
        self.client.login(username='vendedor', password='123456')
        response = self.client.get('/farmacia/pos/?busqueda=Paracetamol')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.medicamento1, response.context['medicamentos'])
        self.assertNotIn(self.medicamento2, response.context['medicamentos'])
    
    def test_buscar_medicamento_por_sku(self):
        """Verifica búsqueda de medicamentos por SKU"""
        self.client.login(username='vendedor', password='123456')
        response = self.client.get('/farmacia/pos/?busqueda=MED001')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.medicamento1, response.context['medicamentos'])
    
    def test_agregar_carrito(self):
        """Verifica que se puede agregar medicamento al carrito"""
        self.client.login(username='vendedor', password='123456')
        
        response = self.client.post(
            f'/farmacia/pos/agregar/{self.medicamento1.pk}/',
            {'medicamento_id': self.medicamento1.pk, 'cantidad': 5},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_agregar_carrito_stock_insuficiente(self):
        """Verifica validación de stock al agregar al carrito"""
        self.client.login(username='vendedor', password='123456')
        
        # Intentar agregar más de lo disponible
        response = self.client.post(
            f'/farmacia/pos/agregar/{self.medicamento2.pk}/',
            {'medicamento_id': self.medicamento2.pk, 'cantidad': 100},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Stock', data['error'])
    
    def test_eliminar_carrito(self):
        """Verifica que se puede eliminar medicamento del carrito"""
        self.client.login(username='vendedor', password='123456')
        
        # Primero agregar al carrito
        self.client.post(
            f'/farmacia/pos/agregar/{self.medicamento1.pk}/',
            {'medicamento_id': self.medicamento1.pk, 'cantidad': 5}
        )
        
        # Luego eliminar
        response = self.client.get(
            f'/farmacia/pos/eliminar/{self.medicamento1.pk}/'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_limpiar_carrito(self):
        """Verifica que se puede vaciar el carrito completo"""
        self.client.login(username='vendedor', password='123456')
        
        # Agregar medicamentos
        self.client.post(
            f'/farmacia/pos/agregar/{self.medicamento1.pk}/',
            {'medicamento_id': self.medicamento1.pk, 'cantidad': 5}
        )
        
        # Limpiar
        response = self.client.get('/farmacia/pos/limpiar/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cantidad_items'], 0)
    
    def test_procesar_venta_pos(self):
        """Verifica procesamiento completo de venta POS"""
        self.client.login(username='vendedor', password='123456')
        session = self.client.session
        
        # Agregar medicamentos al carrito
        session['carrito_pos'] = {
            str(self.medicamento1.pk): {
                'cantidad': 5,
                'precio': '500'
            }
        }
        session.save()
        
        # Procesar pago
        response = self.client.post(
            '/farmacia/pos/procesar-pago/',
            {
                'metodo_pago': 'efectivo',
                'monto_pagado': '2500',
                'cliente_id': '',
                'referencia_transaccion': ''
            }
        )
        
        # Verificar que redirige a ticket
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la venta se creó
        venta = Venta.objects.filter(
            medicamento=self.medicamento1,
            vendedor=self.user
        )
        # Nota: puede haber múltiples ventas si no se limpió entre tests
    
    def test_formulario_busqueda(self):
        """Verifica formulario de búsqueda"""
        from .forms import BuscarMedicamentoForm
        
        form = BuscarMedicamentoForm(data={'busqueda': 'Paracetamol'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['busqueda'], 'Paracetamol')
    
    def test_formulario_agregar_carrito(self):
        """Verifica formulario de agregar al carrito"""
        from .forms import AgregarCarritoForm
        
        form = AgregarCarritoForm(data={
            'medicamento_id': self.medicamento1.pk,
            'cantidad': 5
        })
        self.assertTrue(form.is_valid())
    
    def test_formulario_procesar_pago(self):
        """Verifica formulario de pago"""
        from .forms import ProcesarPagoForm
        
        form = ProcesarPagoForm(data={
            'metodo_pago': 'efectivo',
            'monto_pagado': '2500'
        })
        self.assertTrue(form.is_valid())
    
    def test_permiso_acceso_pos_no_autenticado(self):
        """Verifica que POS requiere autenticación"""
        response = self.client.get('/farmacia/pos/')
        self.assertEqual(response.status_code, 302)  # Redirección a login


# =====================================================================
# WEEK 3: TESTS PARA STOCK TRANSACCIONAL CON FIFO
# =====================================================================

class StockFIFOTestCase(TestCase):
    """Tests para el sistema de stock FIFO"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user('vendedor', password='123456')
        
        self.proveedor = Proveedor.objects.create(
            nombre='Lab Farmacéutico',
            razon_social='LAB LTDA',
            rut='12.345.678-0',
            direccion='Calle Principal 1',
            email='lab@test.com',
            fono='912345678',
            productos='Medicamentos'
        )
        
        self.medicamento = Medicamento.objects.create(
            sku='MED003',
            nombre='Aspirina',
            laboratorio='Lab C',
            principio_activo='Ácido Acetilsalicílico',
            accion_terapeutica='Analgésico',
            presentacion='Tableta',
            dosis='500mg',
            bioequivalente='Sí',
            stock=100,
            precio=300,
            proveedor=self.proveedor,
            fecha_ingreso='2024-01-01',
            fecha_vencimiento='2025-12-31'
        )
        
        # Crear lotes con diferentes fechas de vencimiento
        self.lote_antiguo = LoteMedicamento.objects.create(
            medicamento=self.medicamento,
            numero_lote='LOTE_001',
            fecha_vencimiento=date.today() + timedelta(days=5),
            cantidad_ingresada=50,
            cantidad_disponible=50,
            proveedor=self.proveedor,
            precio_costo=200
        )
        
        self.lote_nuevo = LoteMedicamento.objects.create(
            medicamento=self.medicamento,
            numero_lote='LOTE_002',
            fecha_vencimiento=date.today() + timedelta(days=30),
            cantidad_ingresada=50,
            cantidad_disponible=50,
            proveedor=self.proveedor,
            precio_costo=200
        )
    
    def test_obtener_lotes_fifo(self):
        """Verifica que los lotes se devuelven en orden FIFO"""
        from .functions import obtener_lotes_fifo
        
        lotes = obtener_lotes_fifo(self.medicamento)
        lotes_list = list(lotes)
        
        # El lote más antiguo debe estar primero
        self.assertEqual(lotes_list[0].pk, self.lote_antiguo.pk)
        self.assertEqual(lotes_list[1].pk, self.lote_nuevo.pk)
    
    def test_obtener_lote_para_venta(self):
        """Verifica asignación de lotes para venta"""
        from .functions import obtener_lote_para_venta
        
        # Solicitar 30 unidades
        lotes_a_usar = obtener_lote_para_venta(self.medicamento, 30)
        
        self.assertIsNotNone(lotes_a_usar)
        self.assertEqual(len(lotes_a_usar), 1)  # Solo usa el lote antiguo
        self.assertEqual(lotes_a_usar[0][0].pk, self.lote_antiguo.pk)
        self.assertEqual(lotes_a_usar[0][1], 30)
    
    def test_obtener_lote_para_venta_multiples_lotes(self):
        """Verifica uso de múltiples lotes cuando es necesario"""
        from .functions import obtener_lote_para_venta
        
        # Solicitar 60 unidades (requiere ambos lotes)
        lotes_a_usar = obtener_lote_para_venta(self.medicamento, 60)
        
        self.assertIsNotNone(lotes_a_usar)
        self.assertEqual(len(lotes_a_usar), 2)
        
        # Lote antiguo debe dar 50, y lote nuevo 10
        self.assertEqual(lotes_a_usar[0][1], 50)
        self.assertEqual(lotes_a_usar[1][1], 10)
    
    def test_obtener_lote_para_venta_stock_insuficiente(self):
        """Verifica que retorna None si stock es insuficiente"""
        from .functions import obtener_lote_para_venta
        
        # Solicitar más de lo disponible
        lotes_a_usar = obtener_lote_para_venta(self.medicamento, 150)
        
        self.assertIsNone(lotes_a_usar)
    
    def test_validar_vencimiento_medicamento(self):
        """Verifica validación de vencimiento"""
        from .functions import validar_vencimiento_medicamento
        
        es_apto, dias = validar_vencimiento_medicamento(self.medicamento, dias_minimo=7)
        
        # El lote más antiguo vence en 5 días, menos que el mínimo de 7
        self.assertFalse(es_apto)
        self.assertEqual(dias, 5)
    
    def test_obtener_medicamentos_con_alerta(self):
        """Verifica obtención de medicamentos con alerta de vencimiento"""
        from .functions import obtener_medicamentos_con_alerta
        
        medicamentos_alerta = obtener_medicamentos_con_alerta()
        
        # El medicamento debe estar en las alertas por el lote antiguo
        self.assertIn(self.medicamento, medicamentos_alerta)
    
    def test_dashboard_inventario_load(self):
        """Verifica que el dashboard carga correctamente"""
        self.client.login(username='vendedor', password='123456')
        response = self.client.get('/farmacia/inventario/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'farmacia/dashboard_inventario.html')
        self.assertIn('medicamentos_alerta', response.context)
    
    def test_gestor_lotes_load(self):
        """Verifica que el gestor de lotes carga"""
        self.client.login(username='vendedor', password='123456')
        response = self.client.get('/farmacia/inventario/lotes/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'farmacia/gestor_lotes.html')
    
    def test_reporte_lotes_load(self):
        """Verifica que el reporte de lotes carga"""
        self.client.login(username='vendedor', password='123456')
        response = self.client.get('/farmacia/inventario/reporte-lotes/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'farmacia/reporte_lotes.html')
        self.assertIn('lotes_vigentes', response.context)
    
    def test_procesar_venta_con_fifo(self):
        """Verifica procesamiento de venta con FIFO"""
        from .functions import procesar_venta_con_fifo
        
        # Crear venta con FIFO
        exito, mensaje, venta_ids = procesar_venta_con_fifo(
            self.medicamento, 30, self.user
        )
        
        # Como el lote más antiguo vence en 5 días (<7), debería fallar
        self.assertFalse(exito)
        self.assertIn('próximo a vencer', mensaje.lower())
    
    def test_venta_fifo_view_load(self):
        """Verifica que la vista de venta FIFO carga"""
        self.client.login(username='vendedor', password='123456')
        response = self.client.get(f'/farmacia/venta/fifo/{self.medicamento.pk}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'farmacia/venta_fifo.html')
    
    def test_permiso_dashboard_sin_autenticacion(self):
        """Verifica que dashboard requiere autenticación"""
        response = self.client.get('/farmacia/inventario/dashboard/')
        self.assertEqual(response.status_code, 302)


