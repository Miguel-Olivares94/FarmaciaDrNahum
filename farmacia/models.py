# farmacia/models.py
from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from django.db.models import F
from django.contrib.auth.models import User


class Medicamento(models.Model):
    # ---- Clasificación regulatoria ----
    TIPO_VENTA_LIBRE = 'libre'
    TIPO_VENTA_RECETA_SIMPLE = 'receta_simple'
    TIPO_VENTA_RECETA_RETENIDA = 'receta_retenida'
    TIPO_VENTA_CONTROLADO = 'controlado'

    TIPOS_VENTA = [
        (TIPO_VENTA_LIBRE,           'Venta libre (sin receta)'),
        (TIPO_VENTA_RECETA_SIMPLE,   'Receta simple'),
        (TIPO_VENTA_RECETA_RETENIDA, 'Receta retenida (se queda en farmacia)'),
        (TIPO_VENTA_CONTROLADO,      'Medicamento controlado (estupefaciente/psicotrópico)'),
    ]

    # Tipos que requieren receta en venta
    TIPOS_REQUIEREN_RECETA = [
        TIPO_VENTA_RECETA_SIMPLE,
        TIPO_VENTA_RECETA_RETENIDA,
        TIPO_VENTA_CONTROLADO,
    ]

    sku = models.CharField(max_length=20, unique=True, db_index=True)
    nombre = models.CharField(max_length=255)
    laboratorio = models.CharField(max_length=255)
    principio_activo = models.CharField(max_length=255)
    accion_terapeutica = models.CharField(max_length=255)
    presentacion = models.CharField(max_length=255)
    dosis = models.CharField(max_length=255)
    bioequivalente = models.CharField(max_length=255)
    stock = models.PositiveIntegerField(default=0, db_index=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_venta = models.CharField(
        max_length=20,
        choices=TIPOS_VENTA,
        default=TIPO_VENTA_LIBRE,
        db_index=True,
        help_text="Clasificación regulatoria del medicamento"
    )
    proveedor = models.ForeignKey(
        'Proveedor',
        on_delete=models.PROTECT,  # No permitir borrar proveedor si tiene medicamentos
        related_name='medicamentos',
        null=True,
        blank=True
    )
    nivel_stock = models.CharField(max_length=255, blank=True, null=True)
    fecha_ingreso = models.DateField()
    fecha_vencimiento = models.DateField()
    
    class Meta:
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['stock']),
            models.Index(fields=['proveedor', 'stock']),
            models.Index(fields=['fecha_vencimiento']),
        ]

    
    
    def save(self, *args, **kwargs):
        # Verifica si el campo stock ha cambiado antes de actualizar nivel_stock
        if self.pk is not None:  # Para asegurar que el objeto ya existe en la base de datos
            old_instance = Medicamento.objects.get(pk=self.pk)
            if self.stock != old_instance.stock:
                self.nivel_stock = self.get_nivel_stock()

        super().save(*args, **kwargs)

  
    def calcular_precio_total_vendido(self):
        return sum(detalle.precio_total() for detalle in self.detalleventa_set.all())

 

    def get_nivel_stock(self):
        if self.stock < 100:
            return 'Bajo'
        elif 100 <= self.stock < 700:
            return 'Medio'
        else:
            return 'Alto'

    def requiere_receta(self):
        return self.tipo_venta in self.TIPOS_REQUIEREN_RECETA

    def receta_debe_retenerse(self):
        return self.tipo_venta in [
            self.TIPO_VENTA_RECETA_RETENIDA,
            self.TIPO_VENTA_CONTROLADO,
        ]

    def __str__(self):
        return self.nombre

    



class Venta(models.Model):
    """
    Venta de medicamento. Puede ser venta simple o parte de una venta múltiple (carrito).
    Cada venta tiene un número único para auditoría.
    """
    ESTADOS_VENTA = [
        ('COMPLETADA', 'Completada'),
        ('ANULADA', 'Anulada'),
        ('DEVUELTA', 'Devuelta'),
    ]
    
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2)  # Precio TOTAL (no unitario)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventas_realizadas')
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='venta_set',
        help_text="Cliente que realizó la compra (opcional)"
    )
    # WEEK 3: Rastreo de lotes para FIFO
    lote = models.ForeignKey(
        'LoteMedicamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas',
        help_text="Lote medicamento (para FIFO)"
    )
    
    # NUEVOS CAMPOS PARA POS v2
    numero_venta = models.CharField(
        max_length=15, 
        unique=True, 
        db_index=True,
        null=True,
        blank=True,
        help_text="Número único de venta (VT-2026-00001)"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_VENTA,
        default='COMPLETADA',
        db_index=True
    )
    
    # NUEVA RELACIÓN CON BOLETA (para POS v2)
    boleta = models.ForeignKey(
        'Boleta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas',
        help_text="Boleta asociada a esta venta"
    )
    # Receta que autorizó la venta (null para medicamentos de venta libre)
    receta_venta = models.ForeignKey(
        'Receta',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ventas_autorizadas',
        help_text="Receta médica que autorizó esta venta"
    )

    class Meta:
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['numero_venta']),
            models.Index(fields=['vendedor', 'fecha']),
            models.Index(fields=['estado']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.medicamento.stock < self.cantidad:
            raise ValidationError(
                f'Stock insuficiente. Disponible: {self.medicamento.stock}, Solicitado: {self.cantidad}'
            )

    def save(self, *args, **kwargs):
        # NO restar stock aquí - hacerlo en la vista con transacción
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_venta} - {self.medicamento.nombre} ({self.cantidad})"
 

class DetalleVenta(models.Model):
    venta = models.ForeignKey('Venta', on_delete=models.CASCADE)
    medicamento = models.ForeignKey('Medicamento', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    

    def precio_total(self):
        return self.cantidad * self.precio_unitario


    def __str__(self):
        return f'Detalle de Venta {self.id}'


# Proveedores
class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    razon_social = models.CharField(max_length=255)
    rut = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    email = models.EmailField()
    fono = models.CharField(max_length=20)
    productos = models.TextField()

    def get_absolute_url(self):
        return reverse('proveedor_detail', args=[str(self.id)])

    def __str__(self):
        return self.nombre


class HistorialStock(models.Model):
    """
    Modelo para registrar todas las operaciones que afectan el stock de medicamentos.
    Permite auditoría completa y rastreo de cambios.
    """
    TIPO_OPERACION = [
        ('VENTA', 'Venta'),
        ('AJUSTE', 'Ajuste'),
        ('INGRESO', 'Ingreso'),
        ('DEVOLUCION', 'Devolución'),
    ]
    
    medicamento = models.ForeignKey(
        'Medicamento',
        on_delete=models.CASCADE,
        related_name='historial_stock'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_OPERACION,
        db_index=True
    )
    cantidad = models.IntegerField()  # Positivo (ingreso) o negativo (salida)
    stock_anterior = models.PositiveIntegerField()
    stock_posterior = models.PositiveIntegerField()
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cambios_stock'
    )
    venta = models.ForeignKey(
        'Venta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historial'
    )
    motivo = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Historial de Stock'
        verbose_name_plural = 'Historiales de Stock'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['medicamento', 'fecha_creacion']),
            models.Index(fields=['usuario', 'fecha_creacion']),
            models.Index(fields=['tipo', 'fecha_creacion']),
        ]
    
    def __str__(self):
        return f'{self.get_tipo_display()} - {self.medicamento.nombre} ({self.cantidad})'


# ==================== NUEVOS MODELOS SEMANA 1 ====================

class Cliente(models.Model):
    """
    Registro de clientes para historial de compras y descuentos
    """
    rut_dni = models.CharField(
        max_length=20,
        unique=True,
        help_text="Ej: 12.345.678-9 o 12345678"
    )
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    alergias = models.TextField(blank=True, help_text="Ej: Penicilina, Aspirina")
    medicamentos_contraindicados = models.TextField(
        blank=True,
        help_text="Medicamentos que no puede comprar"
    )
    cliente_vip = models.BooleanField(default=False)
    descuento_vip = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Descuento en % para cliente VIP"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        indexes = [
            models.Index(fields=['rut_dni']),
            models.Index(fields=['email']),
        ]
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut_dni})"
    
    def compras_totales(self):
        """Retorna el total gastado por este cliente"""
        return self.venta_set.aggregate(total=models.Sum('precio'))['total'] or 0
    
    def cantidad_compras(self):
        """Retorna la cantidad de compras realizadas"""
        return self.venta_set.count()


class LoteMedicamento(models.Model):
    """
    Control de lotes de medicamentos con vencimiento.
    Permite rastreo FIFO (first in, first out) y alertas de vencimiento.
    """
    medicamento = models.ForeignKey(
        'Medicamento',
        on_delete=models.CASCADE,
        related_name='lotes'
    )
    numero_lote = models.CharField(max_length=50)
    fecha_vencimiento = models.DateField(db_index=True)
    cantidad_ingresada = models.PositiveIntegerField()
    cantidad_disponible = models.PositiveIntegerField()
    proveedor = models.ForeignKey(
        'Proveedor',
        on_delete=models.SET_NULL,
        null=True
    )
    precio_costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio de costo de este lote"
    )
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Lote de Medicamento'
        verbose_name_plural = 'Lotes de Medicamentos'
        unique_together = ('medicamento', 'numero_lote')
        indexes = [
            models.Index(fields=['medicamento', 'fecha_vencimiento']),
            models.Index(fields=['fecha_vencimiento']),
        ]
        ordering = ['fecha_vencimiento']  # FIFO: vence primero aparece primero
    
    def __str__(self):
        return f"{self.medicamento.nombre} - Lote {self.numero_lote} (Vence: {self.fecha_vencimiento})"
    
    def dias_para_vencer(self):
        """Calcula días para el vencimiento"""
        from datetime import date
        delta = self.fecha_vencimiento - date.today()
        return delta.days
    
    def esta_vencido(self):
        """Verifica si el lote está vencido"""
        from datetime import date
        return self.fecha_vencimiento < date.today()
    
    def esta_proximo_a_vencer(self, dias=30):
        """Verifica si vence en los próximos X días"""
        dias_faltantes = self.dias_para_vencer()
        return 0 <= dias_faltantes <= dias


class Devolucion(models.Model):
    """
    Registro de devoluciones de medicamentos con motivo.
    Permite reintegro a proveedor o acreedor cliente.
    """
    MOTIVOS = [
        ('vencido', 'Medicamento Vencido'),
        ('defecto', 'Defecto/Dañado'),
        ('no_venta', 'Cambio de Opinión'),
        ('error_venta', 'Error de Vendedor'),
        ('otro', 'Otro Motivo'),
    ]
    
    ESTADO = [
        ('registrada', 'Registrada'),
        ('aprobada', 'Aprobada'),
        ('devuelta_proveedor', 'Devuelta a Proveedor'),
        ('acreedor_cliente', 'Acreedor al Cliente'),
    ]
    
    venta = models.ForeignKey(
        'Venta',
        on_delete=models.CASCADE,
        related_name='devoluciones'
    )
    medicamento = models.ForeignKey('Medicamento', on_delete=models.CASCADE)
    lote = models.ForeignKey(
        'LoteMedicamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.CharField(max_length=20, choices=MOTIVOS)
    observaciones = models.TextField(blank=True)
    usuario_registra = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='devoluciones_registradas'
    )
    usuario_aprueba = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devoluciones_aprobadas'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO,
        default='registrada'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['venta']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"Devolución {self.id} - {self.medicamento.nombre} ({self.cantidad} unidades)"
    
    def monto_total(self):
        """Total a devolver al cliente o a proveedor"""
        return self.cantidad * self.precio_unitario
    
    def puede_aprobarse(self):
        """Verifica si puede aprobarse"""
        return self.estado == 'registrada'


# =====================================================================
# NUEVOS MODELOS PARA POS v2 (FASE 1-2)
# =====================================================================

class CarritoVenta(models.Model):
    """
    Carrito temporal de venta almacenado en BD (no en sesión).
    Permite multi-usuario y recuperación de carritos.
    """
    ESTADOS_CARRITO = [
        ('EN_CONSTRUCCION', 'En construcción'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='carritos_venta',
        db_index=True
    )
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carritos'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CARRITO,
        default='EN_CONSTRUCCION',
        db_index=True
    )
    
    # Cálculos automáticos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento_monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Porcentaje de descuento aplicado"
    )
    base_imponible = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # 19%
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_completacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Carrito de Venta'
        verbose_name_plural = 'Carritos de Venta'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['vendedor', 'estado']),
            models.Index(fields=['estado', 'fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Carrito {self.id} - {self.vendedor.username} ({self.estado})"
    
    def calcular_totales(self):
        """Recalcula todos los totales desde los items"""
        items = self.items.all()
        
        # Subtotal (siempre Decimal, nunca int)
        self.subtotal = sum(
            (item.cantidad * item.precio_unitario for item in items),
            Decimal('0.00')
        )
        
        # Base imponible
        self.base_imponible = self.subtotal - self.descuento_monto
        
        # IVA (19%)
        self.iva = (self.base_imponible * Decimal('0.19')).quantize(Decimal('0.01'))
        
        # Total
        self.total = self.base_imponible + self.iva
        
        self.save(update_fields=['subtotal', 'base_imponible', 'iva', 'total'])
    
    def aplicar_descuento(self, porcentaje=0, monto=0):
        """Aplica descuento (porcentaje O monto, no ambos)"""
        if porcentaje > 0:
            self.descuento_porcentaje = porcentaje
            self.descuento_monto = self.subtotal * (porcentaje / 100)
        elif monto > 0:
            self.descuento_monto = monto
            self.descuento_porcentaje = (monto / self.subtotal * 100) if self.subtotal > 0 else 0
        
        self.calcular_totales()
    
    def agregar_item(self, medicamento, cantidad):
        """Agrega o actualiza item en el carrito"""
        if cantidad <= 0:
            raise ValueError('Cantidad debe ser mayor a 0')
        
        if cantidad > medicamento.stock:
            raise ValueError(f'Stock insuficiente. Disponible: {medicamento.stock}')
        
        item, created = CarritoItem.objects.get_or_create(
            carrito=self,
            medicamento=medicamento,
            defaults={
                'cantidad': cantidad,
                'precio_unitario': medicamento.precio
            }
        )
        
        if not created:
            item.cantidad += cantidad
            item.save()
        
        self.calcular_totales()
        return item
    
    def eliminar_item(self, medicamento_id):
        """Elimina un item del carrito"""
        self.items.filter(medicamento_id=medicamento_id).delete()
        self.calcular_totales()
    
    def vaciar_carrito(self):
        """Limpia todos los items"""
        self.items.all().delete()
        self.descuento_monto = 0
        self.descuento_porcentaje = 0
        self.calcular_totales()


class CarritoItem(models.Model):
    """Items dentro del carrito de venta"""
    carrito = models.ForeignKey(
        CarritoVenta, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    # Receta asociada a este ítem (requerida si el medicamento la exige)
    receta = models.ForeignKey(
        'Receta',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='items_carrito',
        help_text="Receta que autoriza la venta de este medicamento"
    )

    class Meta:
        unique_together = ('carrito', 'medicamento')
        verbose_name = 'Item Carrito'
        verbose_name_plural = 'Items Carrito'
    
    def __str__(self):
        return f"{self.medicamento.nombre} x{self.cantidad}"
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class Boleta(models.Model):
    """
    Comprobante fiscal de venta. Representa el recibido que se entrega al cliente.
    Contiene número único, información fiscal, etc.
    """
    METODOS_PAGO = [
        ('EFECTIVO', '💵 Efectivo'),
        ('DEBITO', '🏧 Débito'),
        ('CREDITO', '💳 Crédito'),
        ('TRANSFERENCIA', '🏦 Transferencia'),
    ]
    
    ESTADOS_BOLETA = [
        ('EMITIDA', 'Emitida'),
        ('ANULADA', 'Anulada'),
        ('IMPRESA', 'Impresa'),
    ]
    
    # Números únicos
    numero_boleta = models.CharField(
        max_length=15, 
        unique=True, 
        db_index=True,
        help_text="Formato: BV-2026-00001"
    )
    folio = models.PositiveIntegerField(
        unique=True,
        db_index=True,
        help_text="Número secuencial (1, 2, 3...)"
    )
    
    # Relación con venta
    carrito = models.OneToOneField(
        CarritoVenta,
        on_delete=models.CASCADE,
        related_name='boleta'
    )
    
    # Datos de la farmacia
    rut_farmacia = models.CharField(max_length=20)
    nombre_farmacia = models.CharField(max_length=255, default='FARMACIA DR. NAHUM')
    direccion_farmacia = models.CharField(max_length=255)
    telefono_farmacia = models.CharField(max_length=20, blank=True)
    
    # Datos del cliente
    cliente_rut = models.CharField(max_length=20, null=True, blank=True)
    cliente_nombre = models.CharField(max_length=255, null=True, blank=True)
    
    # Montos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    base_imponible = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(max_digits=12, decimal_places=2)  # 19%
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Pago
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO
    )
    referencia_pago = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Ref. transacción, últimos 4 dígitos, etc"
    )
    
    # Vendedor
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Comprobante digital
    archivo_pdf = models.FileField(
        upload_to='boletas/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_BOLETA,
        default='EMITIDA',
        db_index=True
    )
    
    # Auditoría
    fecha_emision = models.DateTimeField(auto_now_add=True, db_index=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Boleta'
        verbose_name_plural = 'Boletas'
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['numero_boleta']),
            models.Index(fields=['folio']),
            models.Index(fields=['vendedor', 'fecha_emision']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.numero_boleta}"


class Pago(models.Model):
    """Registro de pago de una venta (detalles)"""
    carrito = models.OneToOneField(
        CarritoVenta,
        on_delete=models.CASCADE,
        related_name='pago',
        null=True,
        blank=True
    )
    boleta = models.OneToOneField(
        Boleta,
        on_delete=models.CASCADE,
        related_name='pago'
    )
    
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('EFECTIVO', 'Efectivo'),
            ('DEBITO', 'Débito'),
            ('CREDITO', 'Crédito'),
            ('TRANSFERENCIA', 'Transferencia'),
        ]
    )
    
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    cambio = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Solo para efectivo"
    )
    referencia = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Ref. débito, número cheque, etc"
    )
    
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
    
    def __str__(self):
        return f"Pago {self.metodo_pago} - ${self.monto}"


class NotaCredito(models.Model):
    """
    Nota de crédito por anulación o devolución.
    Se emite cuando se anula una venta o se devuelve medicamento.
    """
    MOTIVOS_NOTA = [
        ('ANULACION', 'Anulación de venta'),
        ('DEVOLUCION', 'Devolución de medicamento'),
        ('DESCUENTO', 'Descuento especial'),
        ('AJUSTE', 'Ajuste de precio'),
    ]
    
    # Números únicos
    numero_nota = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        help_text="Formato: NC-2026-00001"
    )
    folio = models.PositiveIntegerField(
        unique=True,
        db_index=True,
        help_text="Número secuencial"
    )
    
    # Relación con boleta original
    boleta_original = models.ForeignKey(
        Boleta,
        on_delete=models.CASCADE,
        related_name='notas_credito'
    )
    
    # Motivo
    motivo = models.CharField(
        max_length=20,
        choices=MOTIVOS_NOTA
    )
    observaciones = models.TextField(
        blank=True,
        help_text="Detalles del motivo"
    )
    
    # Monto
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto a acreditar"
    )
    
    # Aprobación
    usuario_registra = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notas_credito_registradas'
    )
    usuario_aprueba = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_credito_aprobadas'
    )
    requiere_aprobacion = models.BooleanField(
        default=False,
        help_text="¿Necesita aprobación supervisor?"
    )
    aprobada = models.BooleanField(default=False, db_index=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Nota de Crédito'
        verbose_name_plural = 'Notas de Crédito'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['numero_nota']),
            models.Index(fields=['aprobada']),
            models.Index(fields=['usuario_registra']),
        ]
    
    def __str__(self):
        return f"{self.numero_nota}"


# =====================================================================
# MODELOS DE ROLES, PERMISOS Y AUDITORÍA (ARQUITECTURA DE SEGURIDAD)
# =====================================================================

class RolPermiso(models.Model):
    """Define el rol y permisos de cada usuario"""
    
    ROLES_CHOICES = [
        ('ADMIN', 'Administrador / Dueño'),
        ('VENDEDOR', 'Vendedor'),
        ('GERENTE', 'Gerente de Tienda'),
        ('CONTADOR', 'Contador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rol_permiso')
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES, default='VENDEDOR')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado_activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Rol y Permiso"
        verbose_name_plural = "Roles y Permisos"
        indexes = [
            models.Index(fields=['rol']),
            models.Index(fields=['estado_activo']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"
    
    def es_admin(self):
        return self.rol == 'ADMIN'
    
    def es_vendedor(self):
        return self.rol == 'VENDEDOR'
    
    def puede_ver_ventas_globales(self):
        return self.rol in ['ADMIN', 'CONTADOR', 'GERENTE']
    
    def puede_eliminar_venta(self):
        return self.rol == 'ADMIN'
    
    def puede_editar_venta(self, venta):
        """Determina si puede editar una venta"""
        if self.rol == 'ADMIN':
            return True
        
        if self.rol == 'VENDEDOR':
            # Solo puede editar si es suya y está dentro de 24h
            if venta.vendedor != self.user:
                return False
            
            tiempo_transcurrido = timezone.now() - venta.fecha
            return tiempo_transcurrido.total_seconds() < 86400  # 24 horas
        
        return False


class AuditoriaLog(models.Model):
    """Registra todas las acciones importantes para auditoría"""
    
    ACCIONES_CHOICES = [
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
        ('VER', 'Ver'),
        ('EXPORTAR', 'Exportar'),
        ('INTENTOFALLIDO', 'Intento fallido de acceso'),
        ('ACCESODENEGADO', 'Acceso denegado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='auditorias')
    accion = models.CharField(max_length=20, choices=ACCIONES_CHOICES)
    objeto = models.CharField(max_length=50)  # 'Venta', 'Cliente', etc
    objeto_id = models.IntegerField()
    detalles = models.TextField()
    resultado = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Auditoría Log'
        verbose_name_plural = 'Auditorías Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['accion', 'timestamp']),
            models.Index(fields=['objeto', 'objeto_id']),
        ]
    
    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.objeto} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"


# =====================================================================
# CONTROL DE RECETAS MÉDICAS
# =====================================================================

class Receta(models.Model):
    """
    Receta médica adjunta a una venta.
    Cubre receta simple, retenida y medicamentos controlados.
    """
    TIPO_RECETA_SIMPLE     = 'simple'
    TIPO_RECETA_RETENIDA   = 'retenida'
    TIPO_RECETA_CONTROLADA = 'controlada'

    TIPOS_RECETA = [
        (TIPO_RECETA_SIMPLE,     'Receta simple'),
        (TIPO_RECETA_RETENIDA,   'Receta retenida'),
        (TIPO_RECETA_CONTROLADA, 'Receta de medicamento controlado'),
    ]

    ESTADO_PENDIENTE  = 'pendiente'
    ESTADO_VERIFICADA = 'verificada'
    ESTADO_RECHAZADA  = 'rechazada'

    ESTADOS = [
        (ESTADO_PENDIENTE,  'Pendiente de verificación'),
        (ESTADO_VERIFICADA, 'Verificada'),
        (ESTADO_RECHAZADA,  'Rechazada'),
    ]

    # Tipo
    tipo = models.CharField(max_length=20, choices=TIPOS_RECETA, db_index=True)
    estado = models.CharField(
        max_length=20, choices=ESTADOS,
        default=ESTADO_PENDIENTE, db_index=True
    )

    # Datos del médico
    nombre_medico    = models.CharField(max_length=255)
    rut_medico       = models.CharField(max_length=20, blank=True)
    especialidad     = models.CharField(max_length=100, blank=True)
    codigo_prestador = models.CharField(
        max_length=50, blank=True,
        help_text="Código/RUN ISP del médico tratante"
    )

    # Datos del paciente
    nombre_paciente = models.CharField(max_length=255)
    rut_paciente    = models.CharField(max_length=20)

    # Datos de la receta
    numero_receta   = models.CharField(max_length=50, blank=True)
    fecha_emision   = models.DateField(help_text="Fecha en que fue emitida la receta")
    fecha_vencimiento_receta = models.DateField(
        null=True, blank=True,
        help_text="Fecha máxima para usar la receta (por defecto 30 días)"
    )

    # Archivo físico digitalizado
    archivo_receta = models.FileField(
        upload_to='recetas/%Y/%m/',
        null=True, blank=True,
        help_text="Imagen o PDF de la receta (obligatorio para controlados)"
    )

    # Quién registró y verificó
    registrada_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='recetas_registradas'
    )
    verificada_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recetas_verificadas'
    )
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    motivo_rechazo     = models.TextField(blank=True)

    # Relación con venta (se asigna al completar la venta)
    venta = models.OneToOneField(
        'Venta', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='receta'
    )
    carrito = models.OneToOneField(
        'CarritoVenta', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='receta'
    )

    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Receta Médica'
        verbose_name_plural = 'Recetas Médicas'
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['tipo', 'estado']),
            models.Index(fields=['rut_paciente']),
            models.Index(fields=['fecha_emision']),
        ]

    def __str__(self):
        return f"Receta {self.id} - {self.nombre_paciente} ({self.get_tipo_display()})"

    def esta_vigente(self):
        """Verifica si la receta aún está dentro de su plazo de validez."""
        from datetime import date
        if self.fecha_vencimiento_receta:
            return date.today() <= self.fecha_vencimiento_receta
        # Sin vencimiento explícito: válida 30 días desde emisión
        from datetime import timedelta
        return date.today() <= self.fecha_emision + timedelta(days=30)

    def debe_retenerse(self):
        return self.tipo in [self.TIPO_RECETA_RETENIDA, self.TIPO_RECETA_CONTROLADA]

    def requiere_archivo(self):
        return self.tipo == self.TIPO_RECETA_CONTROLADA


class AuditoriaReceta(models.Model):
    """
    Historial inmutable de cada acción sobre una receta o intento de venta
    con medicamento controlado/con receta.
    """
    EVENTO_RECETA_REGISTRADA  = 'receta_registrada'
    EVENTO_RECETA_VERIFICADA  = 'receta_verificada'
    EVENTO_RECETA_RECHAZADA   = 'receta_rechazada'
    EVENTO_VENTA_BLOQUEADA    = 'venta_bloqueada'
    EVENTO_VENTA_CON_RECETA   = 'venta_con_receta'
    EVENTO_RECETA_RETENIDA    = 'receta_retenida'

    EVENTOS = [
        (EVENTO_RECETA_REGISTRADA, 'Receta registrada'),
        (EVENTO_RECETA_VERIFICADA, 'Receta verificada'),
        (EVENTO_RECETA_RECHAZADA,  'Receta rechazada'),
        (EVENTO_VENTA_BLOQUEADA,   'Venta bloqueada por falta de receta'),
        (EVENTO_VENTA_CON_RECETA,  'Venta realizada con receta'),
        (EVENTO_RECETA_RETENIDA,   'Receta física retenida en farmacia'),
    ]

    receta = models.ForeignKey(
        Receta, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='auditoria'
    )
    medicamento = models.ForeignKey(
        'Medicamento', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='auditoria_recetas'
    )
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='auditoria_recetas'
    )
    evento      = models.CharField(max_length=30, choices=EVENTOS, db_index=True)
    detalle     = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Auditoría de Receta'
        verbose_name_plural = 'Auditorías de Recetas'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['evento', 'timestamp']),
            models.Index(fields=['medicamento', 'timestamp']),
            models.Index(fields=['usuario', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.get_evento_display()} - {self.usuario} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"
