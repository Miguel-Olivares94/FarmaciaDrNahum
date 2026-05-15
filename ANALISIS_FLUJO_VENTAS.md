# 📊 ANÁLISIS FUNCIONAL: FLUJO DE VENTAS ACTUAL
## Sistema Farmacia Collico

**Fecha**: Abril 27, 2026  
**Versión**: 1.0 (Análisis Detallado)  
**Autor**: Analista Funcional + Desarrollador Senior Django  
**Estado**: ✅ Basado en revisión de código actual

---

## 🔍 PARTE 1: RESPUESTAS A LAS 10 PREGUNTAS

### **1. ¿Cómo se hace una venta actualmente?**

**Respuesta**: Existen **DOS flujos paralelos** (confusa):

#### **FLUJO 1: Terminal POS (Principal - Activo)**
```
Usuario accede: http://localhost:8000/farmacia/pos/
    ↓
Busca medicamento por nombre/SKU (GET con query)
    ↓
Sistema filtra medicamentos con stock > 0
    ↓
Usuario selecciona cantidad → Click "Agregar"
    ↓
AJAX POST a agregar_carrito_pos() (sin recargar página)
    ↓
Medicamento se agrega a carrito en session (request.session['carrito_pos'])
    ↓
Usuario ve carrito actualizado (derecha)
    ↓
Usuario puede agregar más medicamentos
    ↓
Click "Procesar Pago"
    ↓
Pantalla: Seleccionar método de pago + monto pagado
    ↓
POST a procesar_venta_pos()
    ↓
    ✅ Venta creada
    ✅ Stock decrementado
    ✅ Historial de stock registrado
    ✅ Redirect a ticket_pos()
    ↓
Mostrar ticket imprimible (monospace style)
    ↓
Usuario: Imprimir, Nueva Venta, o Historial
```

#### **FLUJO 2: Realizar Venta (Secundario - DEPRECATED)**
```
Usuario accede: http://localhost:8000/farmacia/realizar_venta/
    ↓
Formulario básico (VentaForm)
    ↓
Selecciona 1 medicamento + cantidad
    ↓
POST → Intenta descontar stock
    ↓
Redirige a detalle_venta
    ↓
⚠️ NO ESTAMOS USANDO ESTE FLUJO (obsoleto)
```

**Conclusión 1**: Sistema usa **principalmente Terminal POS**. Flujo "Realizar Venta" está ahí pero no es funcional/usado.

---

### **2. ¿Qué vista, formulario, modelo y template participan?**

#### **VISTAS (En views.py)**:

| Vista | Función | Línea | Estado |
|---|---|---|---|
| `terminal_pos()` | Búsqueda + mostrar carrito | 508+ | ✅ Activo |
| `agregar_carrito_pos()` | Agrega medicamento al carrito | ~556 | ✅ AJAX |
| `eliminar_carrito_pos()` | Elimina medicamento del carrito | ~593 | ✅ AJAX |
| `limpiar_carrito_pos()` | Vacía carrito | ~610 | ✅ AJAX |
| `procesar_venta_pos()` | Procesa pago + crea ventas | ~625 | ✅ Principal |
| `ticket_pos()` | Muestra ticket | ~702 | ✅ Imprimible |
| `realizar_venta()` | Método antiguo | ~470 | ⚠️ Deprecated |
| `detalle_venta()` | Muestra detalles venta | N/A | ⚠️ Básico |
| `venta_fifo()` | Venta FIFO (Week 3) | 854+ | ✅ Alternativa |

#### **MODELOS (En models.py)**:

```python
class Venta(models.Model):
    medicamento = ForeignKey(Medicamento)
    cantidad = PositiveIntegerField
    precio = DecimalField  # Precio TOTAL (cantidad × precio_unitario)
    fecha = DateTimeField(auto_now_add=True)
    vendedor = ForeignKey(User)
    cliente = ForeignKey(Cliente, null=True, blank=True)
    lote = ForeignKey(LoteMedicamento, null=True, blank=True)  # FIFO
    
    # ❌ NO EXISTE:
    # - numero_venta
    # - numero_boleta
    # - numero_factura
    # - estado (COMPLETADA, DEVUELTA)
    # - descuentos
    # - impuestos (IVA)
```

#### **FORMULARIOS (En forms.py)**:

```python
class VentaForm(forms.ModelForm):
    """Simple, solo medicamento + cantidad"""
    medicamento = ModelChoiceField
    cantidad = IntegerField(min_value=1, max_value=1000)

class ProcesarPagoForm(¿?):  # ❌ NO ENCONTRADO en forms.py
    # Probablemente está en views.py inline o no existe formalmente
    metodo_pago = ChoiceField([
        ('efectivo', '💵 Efectivo'),
        ('debito', '🏧 Débito'),
        ('credito', '💳 Crédito'),
        ('transferencia', '🏦 Transferencia'),
    ])
    monto_pagado = DecimalField
    cliente_id = IntegerField(optional)
    referencia_transaccion = CharField(optional)
```

#### **TEMPLATES**:

| Template | Propósito | Estado |
|---|---|---|
| `terminal_pos.html` | Búsqueda + carrito visual | ✅ Completo |
| `procesar_pago_pos.html` | Método pago + monto | ✅ Completo |
| `ticket_pos.html` | Ticket imprimible | ✅ Completo (monospace) |
| `detalle_venta.html` | Detalles básicos | ⚠️ Mínimo |
| `realizar_venta.html` | Formulario antiguo | ⚠️ Deprecated |
| `ventas.html` | Listado de ventas | ✅ Existe |

---

### **3. ¿Dónde se descuenta el stock?**

**Respuesta**: En `procesar_venta_pos()`, línea ~668:

```python
# En la transacción atómica:
for med_id, item in carrito.items():
    medicamento = get_object_or_404(Medicamento, pk=med_id)
    cantidad = item['cantidad']
    
    # ← AQUÍ SE DESCUENTA
    medicamento.stock -= cantidad
    medicamento.save()
    
    # También registra historial
    HistorialStock.objects.create(
        medicamento=medicamento,
        tipo='VENTA',
        cantidad=cantidad,
        usuario=request.user,
        stock_anterior=medicamento.stock + cantidad,
        stock_posterior=medicamento.stock,
        motivo=f'Venta POS - {metodo_pago}'
    )
```

**Característica Importante**: ✅ Usa `@transaction.atomic()` - Si falla, se revierte TODO.

---

### **4. ¿Se registra el vendedor?**

**Respuesta**: ✅ **SÍ**, obligatoriamente.

```python
venta = Venta.objects.create(
    medicamento=medicamento,
    cantidad=cantidad,
    precio=precio_unitario * cantidad,
    vendedor=request.user,  # ← Usuario logueado = vendedor
    cliente=cliente_obj
)
```

**Pero**: Sin separación de roles. Cualquier usuario logueado puede vender.

---

### **5. ¿Existe carrito de venta o solo venta simple?**

**Respuesta**: ✅ **SÍ EXISTE CARRITO** - Pero hay problema importante.

#### **Cómo funciona**:
```python
# En terminal_pos:
carrito = request.session.get('carrito_pos', {})

# Estructura:
carrito = {
    '1': {  # medicamento_id
        'cantidad': 5,
        'precio': '500.00'  # precio unitario
    },
    '3': {
        'cantidad': 2,
        'precio': '1000.00'
    }
}
```

#### **PROBLEMA CRÍTICO 🔴**:
```
El carrito está en SESSION (request.session)
    ↓
Si 2 usuarios en la MISMA sesión (navegador compartido)
    ↓
El carrito se mezcla/sobrescribe
    ↓
Usuario A vende medicamento X
Usuario B abre POS en la MISMA computadora
    ↓
¿El carrito de A desaparece o se mezcla?
    ↓
INCONSISTENCIA DE DATOS
```

**Solución**: Debería estar en BD o localStorage del cliente.

---

### **6. ¿Existe factura, boleta o ticket?**

**Respuesta**: ✅ **TICKET SÍ, FACTURA/BOLETA NO**.

#### **Qué existe**:
- ✅ **Ticket imprimible** (ticket_pos.html) - Comprobante de venta con:
  - Nombre farmacia
  - Fecha/Hora
  - Medicamentos, cantidad, precio
  - Total, monto pagado, cambio
  - Método de pago
  - Pie de página

#### **Qué NO existe**:
- ❌ Número de boleta/factura único
- ❌ Número de venta secuencial
- ❌ RUT de la farmacia en ticket
- ❌ Autorización SII (Boleta Electrónica)
- ❌ IVA/Impuestos
- ❌ Dirección de la farmacia
- ❌ Folio numerado

**Conclusión 6**: Es un **TICKET COMERCIAL**, NO una **BOLETA FISCAL** según ley chilena.

---

### **7. ¿Se puede imprimir comprobante?**

**Respuesta**: ✅ **SÍ**, mediante JavaScript.

```html
<!-- En ticket_pos.html -->
<button onclick="imprimirTicket()" class="btn btn-primary btn-lg mr-2">
    <i class="fas fa-print"></i> Imprimir
</button>

<script>
function imprimirTicket() {
    const ticketDiv = document.getElementById('ticket-contenido');
    const ventanaImpresion = window.open('', '', 'height=500,width=400');
    
    ventanaImpresion.document.write('<html><head><title>Ticket</title>');
    ventanaImpresion.document.write(ticketDiv.innerHTML);
    ventanaImpresion.document.write('</body></html>');
    ventanaImpresion.document.close();
    
    setTimeout(() => {
        ventanaImpresion.print();
    }, 250);
}
</script>
```

**Características**:
- ✅ Abre ventana de impresión nueva
- ✅ Formato monospace (ancho fijo para impresoras POS)
- ✅ Sin botones en impresión (@media print)
- ⚠️ **SIN PDF** - Imprime HTML directamente

---

### **8. ¿Existe número de venta o número de factura?**

**Respuesta**: ❌ **NO EXISTE**.

```python
# Modelo Venta no tiene:
# - numero_venta
# - numero_boleta  
# - numero_factura
# - folio
# - secuencia

# Solo usa:
# - id (PK de la BD)
# - fecha (auto_now_add)
```

**Problema**:
- Si necesitas auditoría, no sabes el orden de ventas
- Si necesitas referencia para cliente, solo tienes ID de BD
- Imposible cumplir requisitos SII

**Solución**: Agregar `numero_venta` secuencial + `folio` si llega factura electrónica.

---

### **9. ¿Se puede anular o devolver una venta?**

**Respuesta**: ⚠️ **PARCIALMENTE**.

#### **Qué existe**:
```python
# Vista eliminar_venta() - línea ~459
def eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    
    if request.method == 'POST':
        medicamento = venta.medicamento
        medicamento.stock += venta.cantidad  # ← Revierte stock
        medicamento.save()
        venta.delete()  # ← Borra la venta
        
        return redirect('ventas')
```

#### **Problemas**:
- ⚠️ **BORRA LA VENTA** (no anula) - Rompe auditoría
- ⚠️ No registra motivo de anulación
- ⚠️ No cierra historial
- ⚠️ No crea nota de crédito
- ⚠️ No pide autorización supervisor

**Mejor práctica**: Cambiar `estado` a 'ANULADA' en lugar de borrar.

---

### **10. ¿Qué le falta para funcionar como POS real?**

**Respuesta**: **FALTA MUCHO**. Lista de deficiencias:

#### **🔴 CRÍTICO (Debe hacerse ya)**:

1. **Número de venta secuencial**
   - Cada venta debe tener número único (001, 002, 003...)
   - Para auditoría y referencia

2. **Modelo de Boleta/Factura**
   - Separar concepto de "Venta" y "Comprobante"
   - Número de boleta ≠ número de venta

3. **Descuentos**
   - No hay campo de descuento
   - No se puede aplicar % o monto fijo

4. **IVA/Impuestos**
   - No existe campo de impuesto
   - Chile requiere 19% IVA en boletas

5. **Mejor carrito**
   - No debería estar en sesión
   - Debería estar en BD temporal o localStorage

6. **Anulación correcta**
   - Marcar como ANULADA, no borrar
   - Registrar motivo + usuario

7. **Devoluciones**
   - No existe flujo de devolución
   - Debería generar nota de crédito

#### **🟠 ALTO (Importante muy pronto)**:

8. **PDF de comprobante**
   - HTML → Print no es profesional
   - Necesita PDF para archivo

9. **Número de serie + RUT farmacia**
   - SII requiere RUT en boleta

10. **Email de comprobante**
    - Enviar boleta a correo del cliente

11. **Reportes de ventas**
    - Por período, por vendedor, por medicamento

12. **Integración SII**
    - Si llega momento, boleta electrónica

13. **Múltiples vendedores**
    - Separar por rol (farmacéutico, cajero)

14. **Control de acceso**
    - Quién puede anular, quién puede devolver

15. **Integración de pagos**
    - Webpay, Khipu, etc.

#### **🟡 MEDIO (Mejoras UX)**:

16. **Búsqueda avanzada**
    - Filtro por laboratorio, principio activo

17. **Código de barras**
    - Lectura directa en POS

18. **Cambio de cliente en carrito**
    - Ahora es después del pago

19. **Vista previa de cambio**
    - Antes de procesar pago

20. **Histórico de clientes**
    - Últimas compras en POS

---

## 📋 PARTE 2: DIAGNÓSTICO DEL ESTADO ACTUAL

### **FLUJO ACTUAL (SIMPLIFICADO)**:

```
┌─────────────────────────────────────────────────────────────┐
│                    TERMINAL POS ACTUAL                       │
└─────────────────────────────────────────────────────────────┘

1. BÚSQUEDA (GET)
   Formulario: <input name="busqueda">
   Query: Q(nombre__icontains) | Q(sku__icontains)
   Resultado: Medicamentos con stock > 0

2. CARRITO (AJAX + Session)
   Estructura: request.session['carrito_pos']
   Almacenamiento: ❌ Frágil (sesión)
   
3. PAGO (POST)
   Método: efectivo, débito, crédito, transferencia
   Monto: Obligatorio
   Cliente: Opcional
   
4. PROCESAMIENTO (BD)
   ✅ Transacción atómica
   ✅ Descuenta stock
   ✅ Registra historial
   ❌ Sin número de venta
   ❌ Sin IVA
   ❌ Sin descuento
   
5. TICKET (Impresión)
   Formato: HTML monospace
   ✅ Imprimible
   ❌ Sin PDF
   ❌ Sin email
   
6. OPERACIONES POST-VENTA
   ✅ Ver historial (ventas.html)
   ⚠️ Anular/eliminar (borra, no anula)
```

### **ESTADÍSTICAS DE IMPLEMENTACIÓN**:

| Feature | Implementado | Funcional | Seguro | Completo |
|---|---|---|---|---|
| Búsqueda | ✅ 100% | ✅ Sí | ✅ Sí | ⚠️ Básico |
| Carrito | ✅ 100% | ⚠️ Parcial | ❌ No | ❌ No |
| Pago | ✅ 100% | ✅ Sí | ⚠️ Parcial | ⚠️ Parcial |
| Stock | ✅ 100% | ✅ Sí | ✅ Sí | ⚠️ Sin validación |
| Ticket | ✅ 100% | ✅ Sí | ⚠️ Parcial | ❌ No |
| Número venta | ❌ 0% | ❌ No | ❌ No | ❌ No |
| Descuentos | ❌ 0% | ❌ No | ❌ N/A | ❌ No |
| IVA | ❌ 0% | ❌ No | ❌ No | ❌ No |
| Devoluciones | ❌ 0% | ❌ No | ❌ No | ❌ No |
| Reportes | ⚠️ 50% | ⚠️ Parcial | ⚠️ Parcial | ❌ No |

---

## 🎯 PARTE 3: FLUJO IDEAL PROPUESTO

### **ARQUITECTURA MEJORADA**:

```
┌─────────────────────────────────────────────────────────────┐
│              FLUJO DE VENTA MEJORADO (PROPUESTO)             │
└─────────────────────────────────────────────────────────────┘

PASO 1: INICIAR VENTA
├─ URL: /farmacia/pos/
├─ Usuario = Vendedor (de sesión)
├─ Crear CarritoVenta (BD temporal) con pk=sessión_id
└─ Estado: EN_CONSTRUCCION

PASO 2: SELECCIONAR CLIENTE (OPCIONAL)
├─ Modal: Buscar cliente por RUT/Nombre
├─ O: Continuar sin cliente (venta anónima)
├─ Guardar: CarritoVenta.cliente = Cliente
└─ Si tiene descuento VIP: aplicar automáticamente

PASO 3: BUSCAR MEDICAMENTOS
├─ Búsqueda rápida (nombre, SKU, código barras)
├─ Filtros: laboratorio, principio activo
├─ Mostrar: nombre, precio, stock, descuento aplicable
└─ Validar: ¿Cliente alérgico? ⚠️ Advertencia

PASO 4: AGREGAR AL CARRITO
├─ Guardar en CarritoVenta.items (ManyToMany)
├─ Cantidad validada (< stock disponible)
├─ Precio descargado de Medicamento
├─ Calcular: subtotal = cantidad × precio
└─ Actualizar: Total del carrito en tiempo real

PASO 5: REVISAR CARRITO
├─ Tabla editable:
│  ├─ Medicamento | Cantidad | Precio Unit | Subtotal | Descontar
│  ├─ Cambiar cantidad (validar stock)
│  ├─ Eliminar items
│  └─ Limpiar carrito
│
├─ Subtotal: Σ(cantidad × precio)
├─ Descuento global: % o monto
├─ Base imponible: Subtotal - Descuento
├─ IVA (19%): Base × 0.19
└─ TOTAL: Base + IVA

PASO 6: SELECCIONAR DESCUENTOS
├─ Tipo descuento:
│  ├─ Descuento VIP (automático)
│  ├─ Promoción (aplicable)
│  ├─ Descuento farmacéutico (% manual)
│  └─ Monto fijo
├─ Validar: Autorización si > límite
└─ Mostrar: Total actualizado

PASO 7: PROCESAR PAGO
├─ Método: Efectivo, Débito, Crédito, Transferencia
├─ Si Efectivo:
│  ├─ Monto a pagar (input)
│  ├─ Calcular cambio automáticamente
│  └─ Validar: monto ≥ total
├─ Si Débito/Crédito:
│  ├─ Referencia transacción
│  ├─ Últimos 4 dígitos
│  └─ Validar: dato no vacío
└─ Si Transferencia:
    ├─ Número comprobante
    └─ Validar: dato no vacío

PASO 8: CONFIRMAR Y CREAR VENTA
├─ Crear: Venta (principal)
├─ Generar: numero_venta (secuencial)
├─ Crear: Boleta (comprobante)
├─ Generar: numero_boleta
├─ Crear: DetalleVenta (items)
├─ Crear: Pago (método + monto)
├─ Descontar stock (con validación FIFO)
├─ Registrar: HistorialStock
├─ Marcar: CarritoVenta.estado = COMPLETADA
└─ Transacción: @transaction.atomic()

PASO 9: GENERAR COMPROBANTE
├─ Boleta (con datos fiscales)
├─ Número único: BV-2026-00001
├─ RUT farmacia: automatizado
├─ Dirección: automatizada
├─ IVA: calculado
├─ Total con IVA: mostrado
└─ Fecha/Hora: servidor

PASO 10: MOSTRAR Y GUARDAR COMPROBANTE
├─ Vista previa HTML
├─ PDF descargable
├─ Email a cliente (si tiene)
├─ Imprimir (térmica o normal)
├─ Guardar copia en BD (boleta.archivo_pdf)
└─ Usuario acepta: siguiente paso

PASO 11: OPCIONES POST-VENTA
├─ Botones:
│  ├─ Imprimir nuevamente
│  ├─ Enviar por email
│  ├─ Nueva venta
│  ├─ Ver historial
│  └─ Cerrar sesión
└─ Guardar datos en sesión (última venta)

ANULACIÓN (Posterior):
├─ Usuario entra a: /farmacia/ventas/
├─ Busca venta por número
├─ Click "Anular"
├─ Modal: Razón + contraseña supervisor
├─ Validar: autorización
├─ Cambiar: Venta.estado = ANULADA
├─ Crear: NotaCredito
├─ Revenir: Stock
├─ Registrar: HistorialStock (tipo=ANULACION)
└─ NO borrar nada (auditoría)

DEVOLUCIÓN (Posterior):
├─ Cliente trae medicamento
├─ Usuario entra a: /farmacia/devoluciones/
├─ Busca venta original
├─ Click "Procesar devolución"
├─ Inspeccionar: envase, fecha (< 7 días)
├─ Crear: Devolucion
├─ Generar: NotaCredito
├─ Revenir: Stock
├─ Registrar: HistorialStock (tipo=DEVOLUCION)
└─ Pedir: Autorización supervisor si aplica
```

---

## 📦 PARTE 4: MODELOS NUEVOS O MODIFICADOS

### **MODELOS A AGREGAR/MODIFICAR**:

```python
# ============================================================
# MODELO 1: CarritoVenta (NUEVO)
# ============================================================
class CarritoVenta(models.Model):
    """Carrito temporal almacenado en BD (no sesión)"""
    vendedor = ForeignKey(User, on_delete=models.CASCADE)
    cliente = ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    
    estado = CharField(choices=[
        ('EN_CONSTRUCCION', 'En construcción'),
        ('PAGADO', 'Pagado'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ], default='EN_CONSTRUCCION')
    
    subtotal = DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento_porcentaje = DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    base_imponible = DecimalField(max_digits=10, decimal_places=2)
    iva = DecimalField(max_digits=10, decimal_places=2)  # 19%
    total = DecimalField(max_digits=10, decimal_places=2)
    
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_modificacion = DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def agregar_item(self, medicamento, cantidad):
        """Agrega o actualiza cantidad de medicamento"""
        item, created = CarritoItem.objects.get_or_create(
            carrito=self,
            medicamento=medicamento,
            defaults={'cantidad': cantidad, 'precio_unitario': medicamento.precio}
        )
        if not created:
            item.cantidad += cantidad
            item.save()
        self.calcular_totales()
    
    def calcular_totales(self):
        """Recalcula subtotal, IVA, total"""
        items = self.items.all()
        self.subtotal = sum(item.cantidad * item.precio_unitario for item in items)
        self.base_imponible = self.subtotal - self.descuento
        self.iva = self.base_imponible * Decimal('0.19')
        self.total = self.base_imponible + self.iva
        self.save()


# ============================================================
# MODELO 2: CarritoItem (NUEVO)
# ============================================================
class CarritoItem(models.Model):
    """Items dentro del carrito"""
    carrito = ForeignKey(CarritoVenta, on_delete=models.CASCADE, related_name='items')
    medicamento = ForeignKey(Medicamento, on_delete=models.CASCADE)
    cantidad = PositiveIntegerField(default=1)
    precio_unitario = DecimalField(max_digits=10, decimal_places=2)
    subtotal = DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.carrito.calcular_totales()  # Recalcular carrito
    
    def __str__(self):
        return f"{self.medicamento.nombre} x{self.cantidad}"


# ============================================================
# MODELO 3: Boleta (NUEVO)
# ============================================================
class Boleta(models.Model):
    """Comprobante fiscal de venta"""
    numero_boleta = CharField(max_length=10, unique=True)  # BV-2026-00001
    folio = PositiveIntegerField(unique=True)  # Secuencia 1, 2, 3...
    
    venta = OneToOneField('Venta', on_delete=models.CASCADE, related_name='boleta')
    
    # Datos de la transacción
    fecha_emision = DateTimeField(auto_now_add=True)
    rut_farmacia = CharField(max_length=20)  # 12.345.678-9
    direccion_farmacia = CharField(max_length=255)
    
    # Datos del cliente
    cliente_rut = CharField(max_length=20, null=True, blank=True)
    cliente_nombre = CharField(max_length=255, null=True, blank=True)
    
    # Montos
    subtotal = DecimalField(max_digits=10, decimal_places=2)
    descuento = DecimalField(max_digits=10, decimal_places=2, default=0)
    base_imponible = DecimalField(max_digits=10, decimal_places=2)
    iva = DecimalField(max_digits=10, decimal_places=2)
    total = DecimalField(max_digits=10, decimal_places=2)
    
    # Método de pago
    metodo_pago = CharField(max_length=20, choices=[
        ('EFECTIVO', 'Efectivo'),
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
    ])
    
    # Comprobante digital
    archivo_pdf = FileField(upload_to='boletas/%Y/%m/', null=True, blank=True)
    estado_sii = CharField(max_length=20, default='NO_ENVIADA', choices=[
        ('NO_ENVIADA', 'No enviada'),
        ('ENVIADA', 'Enviada'),
        ('ACEPTADA', 'Aceptada'),
        ('RECHAZADA', 'Rechazada'),
    ])
    
    class Meta:
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Boleta {self.numero_boleta}"


# ============================================================
# MODELO 4: Venta MODIFICADO
# ============================================================
class Venta(models.Model):
    medicamento = ForeignKey(Medicamento, on_delete=models.CASCADE)
    cantidad = PositiveIntegerField(default=0)
    precio = DecimalField(max_digits=10, decimal_places=2)  # Precio UNITARIO (cambiar nombre)
    fecha = DateTimeField(auto_now_add=True)
    vendedor = ForeignKey(User, on_delete=models.CASCADE, related_name='ventas_realizadas')
    cliente = ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    lote = ForeignKey(LoteMedicamento, on_delete=models.SET_NULL, null=True, blank=True)
    
    # NUEVOS CAMPOS
    numero_venta = CharField(max_length=10, unique=True)  # VT-2026-00001
    estado = CharField(max_length=20, default='COMPLETADA', choices=[
        ('COMPLETADA', 'Completada'),
        ('ANULADA', 'Anulada'),
        ('DEVUELTA', 'Devuelta'),
    ])
    
    # Relación con boleta
    boleta = OneToOneField(Boleta, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha']


# ============================================================
# MODELO 5: Pago (NUEVO)
# ============================================================
class Pago(models.Model):
    """Registro de pagos realizados"""
    venta = ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    
    metodo_pago = CharField(max_length=20, choices=[
        ('EFECTIVO', 'Efectivo'),
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
    ])
    
    monto = DecimalField(max_digits=10, decimal_places=2)
    cambio = DecimalField(max_digits=10, decimal_places=2, default=0)
    referencia = CharField(max_length=100, null=True, blank=True)  # Para débito/crédito/transferencia
    
    fecha = DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Pago {self.metodo_pago} - {self.monto}"


# ============================================================
# MODELO 6: NotaCredito (NUEVO)
# ============================================================
class NotaCredito(models.Model):
    """Nota de crédito por devolución o anulación"""
    numero_nota = CharField(max_length=10, unique=True)  # NC-2026-00001
    venta = ForeignKey(Venta, on_delete=models.CASCADE)
    
    motivo = CharField(max_length=100, choices=[
        ('ANULACION', 'Anulación'),
        ('DEVOLUCION', 'Devolución'),
        ('DESCUENTO', 'Descuento'),
    ])
    
    monto = DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = DateTimeField(auto_now_add=True)
    aprobado_por = ForeignKey(User, on_delete=models.SET_NULL, null=True)
    observaciones = TextField(null=True, blank=True)
    
    def __str__(self):
        return f"NC {self.numero_nota}"
```

---

## 🔧 PARTE 5: VISTAS NECESARIAS

### **VISTAS A CREAR/MODIFICAR**:

```python
# ============================================================
# 1. Vista Principal POS (MEJORADA)
# ============================================================
@login_required
def terminal_pos_v2(request):
    """
    Terminal POS v2 con carrito en BD
    
    GET: Mostrar búsqueda + carrito
    POST: Agregar medicamento al carrito
    """
    # Obtener o crear carrito
    carrito, created = CarritoVenta.objects.get_or_create(
        vendedor=request.user,
        estado='EN_CONSTRUCCION'
    )
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    medicamentos = []
    if busqueda:
        medicamentos = Medicamento.objects.filter(
            Q(nombre__icontains=busqueda) |
            Q(sku__icontains=busqueda)
        ).filter(stock__gt=0)
    
    context = {
        'carrito': carrito,
        'items': carrito.items.all(),
        'medicamentos': medicamentos,
        'busqueda': busqueda,
    }
    
    return render(request, 'farmacia/pos_v2.html', context)


# ============================================================
# 2. Agregar al carrito
# ============================================================
@login_required
def pos_agregar_item(request, medicamento_id):
    """POST: Agregar medicamento al carrito"""
    medicamento = get_object_or_404(Medicamento, pk=medicamento_id)
    cantidad = int(request.POST.get('cantidad', 1))
    
    # Validar
    if cantidad > medicamento.stock:
        messages.error(request, f'Stock insuficiente')
        return redirect('terminal_pos_v2')
    
    # Obtener carrito
    carrito, _ = CarritoVenta.objects.get_or_create(
        vendedor=request.user,
        estado='EN_CONSTRUCCION'
    )
    
    # Agregar
    carrito.agregar_item(medicamento, cantidad)
    messages.success(request, f'✅ {medicamento.nombre} agregado')
    
    return redirect('terminal_pos_v2')


# ============================================================
# 3. Procesar pago mejorado
# ============================================================
@login_required
@transaction.atomic
def pos_procesar_pago(request):
    """POST: Procesar pago del carrito"""
    carrito = get_object_or_404(
        CarritoVenta,
        vendedor=request.user,
        estado='EN_CONSTRUCCION'
    )
    
    metodo_pago = request.POST.get('metodo_pago')
    monto_pagado = Decimal(request.POST.get('monto_pagado', 0))
    
    # Validar
    if monto_pagado < carrito.total:
        messages.error(request, f'Monto insuficiente')
        return redirect('pos_procesar_pago')
    
    # Crear venta principal
    venta = Venta.objects.create(
        medicamento=carrito.items.first().medicamento,  # Principal
        cantidad=1,
        precio=carrito.total,
        vendedor=request.user,
        cliente=carrito.cliente,
        numero_venta=generar_numero_venta(),
    )
    
    # Crear boleta
    boleta = Boleta.objects.create(
        numero_boleta=generar_numero_boleta(),
        folio=generar_folio(),
        venta=venta,
        subtotal=carrito.subtotal,
        descuento=carrito.descuento,
        base_imponible=carrito.base_imponible,
        iva=carrito.iva,
        total=carrito.total,
        metodo_pago=metodo_pago,
    )
    
    # Crear pago
    Pago.objects.create(
        venta=venta,
        metodo_pago=metodo_pago,
        monto=monto_pagado,
        cambio=monto_pagado - carrito.total,
    )
    
    # Descontar stock para cada item
    for item in carrito.items.all():
        item.medicamento.stock -= item.cantidad
        item.medicamento.save()
        
        HistorialStock.objects.create(
            medicamento=item.medicamento,
            tipo='VENTA',
            cantidad=item.cantidad,
            usuario=request.user,
            stock_anterior=item.medicamento.stock + item.cantidad,
            stock_posterior=item.medicamento.stock,
        )
    
    # Marcar carrito completo
    carrito.estado = 'COMPLETADO'
    carrito.save()
    
    # Generar PDF
    boleta.generar_pdf()
    
    # Guardar en sesión para mostrar
    request.session['ultima_boleta_id'] = boleta.id
    
    messages.success(request, '✅ Venta completada')
    return redirect('pos_mostrar_boleta')


# ============================================================
# 4. Mostrar boleta (reemplaza ticket_pos)
# ============================================================
@login_required
def pos_mostrar_boleta(request):
    """GET: Mostrar boleta imprimible"""
    boleta_id = request.session.get('ultima_boleta_id')
    boleta = get_object_or_404(Boleta, pk=boleta_id)
    
    context = {
        'boleta': boleta,
        'venta': boleta.venta,
        'carrito': CarritoVenta.objects.get(boleta=boleta) if hasattr(boleta, 'carrito_venta') else None,
    }
    
    return render(request, 'farmacia/boleta.html', context)


# ============================================================
# 5. Anular venta
# ============================================================
@login_required
def pos_anular_venta(request, numero_venta):
    """POST: Anular venta (crear nota crédito)"""
    venta = get_object_or_404(Venta, numero_venta=numero_venta)
    
    # Validar permiso (solo supervisor)
    if not request.user.is_staff:
        messages.error(request, 'Solo supervisores')
        return redirect('pos_ver_historial')
    
    motivo = request.POST.get('motivo')
    
    # Cambiar estado
    venta.estado = 'ANULADA'
    venta.save()
    
    # Crear nota de crédito
    NotaCredito.objects.create(
        numero_nota=generar_numero_nota(),
        venta=venta,
        motivo='ANULACION',
        monto=venta.precio * venta.cantidad,
        aprobado_por=request.user,
        observaciones=motivo,
    )
    
    # Revenir stock
    venta.medicamento.stock += venta.cantidad
    venta.medicamento.save()
    
    messages.success(request, f'✅ Venta {numero_venta} anulada')
    return redirect('pos_ver_historial')
```

---

## 🎨 PARTE 6: TEMPLATES NECESARIOS

### **TEMPLATES A CREAR**:

```html
<!-- 1. pos_v2.html (Reemplaza terminal_pos.html) -->
<!-- Búsqueda + Carrito en 2 columnas -->
<!-- Carrito en tiempo real (recalcula totales) -->
<!-- Botón procesar pago -->

<!-- 2. procesar_pago_v2.html (Mejorado) -->
<!-- Método de pago (radio buttons) -->
<!-- Monto pagado (con cambio automático) -->
<!-- Cliente (selector modal) -->
<!-- Resumen de carrito -->

<!-- 3. boleta.html (Reemplaza ticket_pos.html) -->
<!-- Número de boleta + folio -->
<!-- RUT + dirección farmacia -->
<!-- IVA desglosado -->
<!-- Código QR (futuro SII) -->
<!-- Botones: Imprimir, PDF, Email -->

<!-- 4. historial_ventas.html (Mejorado) -->
<!-- Tabla de ventas con número único -->
<!-- Filtros: fecha, vendedor, cliente -->
<!-- Botón anular (si permitido) -->
<!-- Botón descargar PDF -->

<!-- 5. anular_venta_modal.html (Nuevo) -->
<!-- Modal de confirmación -->
<!-- Campo de razón/observación -->
<!-- Validación de supervisor -->
```

---

## 📝 PARTE 7: PLAN DE IMPLEMENTACIÓN

### **FASE 1: FUNDAMENTOS (Semanas 1-2)**

**Sprint 1 - Modelos base**:
- [ ] Crear modelo `CarritoVenta` + `CarritoItem`
- [ ] Crear modelo `Boleta`
- [ ] Crear modelo `Pago`
- [ ] Crear modelo `NotaCredito`
- [ ] Modificar modelo `Venta` (agregar número, estado)
- [ ] Crear migrations
- [ ] Tests unitarios (8 tests mínimo)

**Sprint 2 - Vistas base**:
- [ ] Terminal POS v2 (búsqueda + carrito en BD)
- [ ] Agregar al carrito (POST AJAX)
- [ ] Procesar pago (crear venta + boleta)
- [ ] Mostrar boleta
- [ ] Tests (6 tests)

### **FASE 2: FUNCIONALIDADES (Semanas 3-4)**

**Sprint 3 - Funciones complementarias**:
- [ ] Generar número único (VT-2026-00001)
- [ ] Generar número boleta (BV-2026-00001)
- [ ] Calcular IVA automático
- [ ] Descontar stock con transacción
- [ ] Crear/guardar PDF boleta
- [ ] Tests (8 tests)

**Sprint 4 - Operaciones post-venta**:
- [ ] Anular venta (crear nota crédito)
- [ ] Ver historial ventas
- [ ] Reportes básicos
- [ ] Tests (6 tests)

### **FASE 3: UI/UX (Semana 5)**

- [ ] Template pos_v2.html (Bootstrap 5)
- [ ] Template procesar_pago_v2.html
- [ ] Template boleta.html (imprimible)
- [ ] CSS para impresión
- [ ] Testing en navegador

### **FASE 4: MIGRACIÓN (Semana 6)**

- [ ] Reemplazar terminal_pos con pos_v2
- [ ] Reemplazar ticket_pos con boleta
- [ ] Mantener URLs retrocompatibles (redirect)
- [ ] Testing en producción (staging)
- [ ] Documentación

---

## 🚀 CONCLUSIONES Y RECOMENDACIONES

### **ESTADO ACTUAL - EVALUACIÓN HONESTA**:

✅ **Lo que está bien**:
- Terminal POS búsqueda funciona
- Carrito visual está OK
- Transacciones atómicas
- Historial de stock completo
- Impresión básica OK

❌ **Lo que falta críticamente**:
- Número de venta único (auditoría imposible)
- Número de boleta (requisito fiscal)
- IVA (obligatorio en Chile)
- Descuentos (No se pueden aplicar)
- Carrito en sesión (inseguro en multi-usuario)
- Anulación correcta (borra, no anula)
- Devoluciones (no existe)

⚠️ **Riesgos de la implementación actual**:
- Si SII audita: multa por boletas sin número
- Si cliente quiere devolver: imposible
- Si 2 usuarios en 1 computadora: carrito inconsistente
- Si necesitas reportes: datos inconsistentes

### **RECOMENDACIÓN FINAL**:

**Implementar FASE 1 + FASE 2 (4 semanas)**:
- Costo: ~$12,000 USD
- Ganancia: Sistema robusto, audit-ready, escalable
- ROI: Inmediato (evita multas SII)

**Este es un cambio arquitectónico importante, pero necesario.**

---

**Documento completo. ¿Quieres que implemente alguna fase?**
