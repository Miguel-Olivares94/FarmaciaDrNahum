# 🔐 Arquitectura de Roles y Permisos - Farmacia Dr Nahúm

**Versión:** 1.0  
**Fecha:** 2026-04-27  
**Objetivo:** Definir permisos granulares para VENDEDOR vs ADMINISTRADOR con validación backend

---

## 📋 TABLA DE CONTENIDOS
1. [Matriz de Permisos General](#matriz-de-permisos-general)
2. [Permisos por Módulo](#permisos-por-módulo)
3. [Campos Visibles/Ocultos](#campos-visiblesoculos)
4. [Vistas Permitidas y Bloqueadas](#vistas-permitidas-y-bloqueadas)
5. [Implementación Django](#implementación-django)
6. [Validaciones Backend](#validaciones-backend)
7. [Auditoría y Seguridad](#auditoría-y-seguridad)
8. [Recomendaciones](#recomendaciones)

---

## 🔑 MATRIZ DE PERMISOS GENERAL

```
ACCIÓN                          VENDEDOR    ADMIN/DUEÑO
─────────────────────────────────────────────────────────
Ver Dashboard Completo            ❌          ✅
Ver Dashboard Personal            ✅          ✅
Ver Ventas Propias                ✅          ✅
Ver Todas las Ventas              ❌          ✅
Crear Venta                       ✅          ✅
Editar Venta Propia               ✅ (24h)    ✅
Editar Venta Ajena                ❌          ✅
Eliminar Venta                    ❌          ✅
Ver Clientes Propios              ✅          ✅
Ver Todos los Clientes            ❌          ✅
Crear Cliente                     ✅          ✅
Editar Cliente Propio             ✅          ✅
Editar Cliente Ajeno              ❌          ✅
Eliminar Cliente                  ❌          ✅
Ver Productos                     ✅          ✅
Editar Producto                   ❌          ✅
Ver Costo Producto                ❌          ✅
Ver Margen Ganancia               ❌          ✅
Ver Reporte Propio                ✅          ✅
Ver Reporte Global                ❌          ✅
Ver Finanzas/Costos               ❌          ✅
Configurar Sistema                ❌          ✅
Gestionar Usuarios                ❌          ✅
Ver Auditoría                     ❌          ✅
```

---

## 📊 PERMISOS POR MÓDULO

### 1. DASHBOARD

#### ✅ VENDEDOR PUEDE VER:
- **Mi Panel Personal:**
  - Ventas del día
  - Número de clientes atendidos hoy
  - Meta del día (si existe)
  - Progreso vs meta diaria
  - Últimas 5 ventas propias
  - Clientes frecuentes (propios)

- **Métricas Permitidas:**
  - Cantidad de transacciones: Sí
  - Unidades vendidas (propias): Sí
  - Monto total (propias): Sí
  - Promedio por venta (propia): Sí
  - Tendencia últimos 7 días (propia): Sí

#### ❌ VENDEDOR NO PUEDE VER:
- Dashboard global de la farmacia
- Ventas de otros vendedores
- Comparativas entre vendedores
- Utilidades reales (Total - Costo)
- Margen de ganancia
- Análisis de rentabilidad
- Costos de operación
- Flujo de caja
- Ranking de vendedores (salvo que esté explícitamente autorizado)
- Gráficos financieros
- KPIs de negocio

#### 🔒 FILTRADO BACKEND:
```python
# Vista Dashboard para Vendedor
if user.role == 'VENDEDOR':
    ventas = Venta.objects.filter(vendedor=user)  # Solo propias
    clientes = Cliente.objects.filter(vendedor_asignado=user)  # Solo propios
    # No incluir costo_unitario, margen, costo_total
```

---

### 2. VENTAS

#### ✅ VENDEDOR PUEDE:
- **Registrar nueva venta:**
  - Seleccionar cliente
  - Agregar productos al carrito
  - Aplicar descuento autorizado (máximo 10%)
  - Procesar pago
  - Imprimir comprobante
  - Seleccionar método de pago

- **Ver propias ventas:**
  - Ver detalles de sus transacciones
  - Ver historial completo
  - Filtrar por fecha, cliente, estado
  - Ver número de boleta/factura
  - Ver estado del pago

- **Editar venta propia (SOLO dentro de 24 horas y NO cerrada):**
  - Modificar descuento aplicado
  - Cambiar método de pago
  - Agregar nota/referencia

- **Imprimir/Descargar:**
  - Comprobante de su venta
  - Boleta de compra

#### ❌ VENDEDOR NO PUEDE:
- Ver ventas de otros vendedores
- Ver resumen global de ventas
- Eliminar venta registrada
- Editar venta ajena
- Ver costo total de la venta
- Ver margen de ganancia en la venta
- Cambiar vendedor asignado
- Forzar cierre de boleta
- Acceder a anulaciones (solo ADMIN)
- Ver devoluciones totales
- Ver reportes de ventas por vendedor

#### 🔒 FILTRADO BACKEND:

```python
# Listar ventas - Solo propias
def ventas_view(request):
    if request.user.role == 'VENDEDOR':
        ventas = Venta.objects.filter(vendedor=request.user)
    else:  # ADMIN
        ventas = Venta.objects.all()
    
    return render(request, 'ventas.html', {'ventas': ventas})

# Editar venta - Validar propiedad y tiempo
def editar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Validaciones de seguridad
    if request.user.role == 'VENDEDOR':
        # 1. Debe ser propietario
        if venta.vendedor != request.user:
            raise PermissionDenied("No puedes editar venta de otro vendedor")
        
        # 2. Debe estar dentro de 24 horas
        tiempo_transcurrido = now() - venta.fecha
        if tiempo_transcurrido > timedelta(hours=24):
            raise PermissionDenied("Solo puedes editar dentro de 24 horas")
        
        # 3. No debe estar cerrada
        if venta.estado == 'CERRADA':
            raise PermissionDenied("No puedes editar venta cerrada")
    
    # ... resto del código

# Eliminar venta - Solo ADMIN
def eliminar_venta(request, venta_id):
    if request.user.role != 'ADMIN':
        raise PermissionDenied("Solo administrador puede eliminar ventas")
    
    venta = get_object_or_404(Venta, id=venta_id)
    venta.delete()
```

#### 📊 CAMPOS VISIBLES EN VENTA:
```
CAMPO                   VENDEDOR    ADMIN
─────────────────────────────────────────
ID Venta                  ✅         ✅
Fecha                     ✅         ✅
Vendedor                  ✅         ✅
Cliente                   ✅         ✅
Productos                 ✅         ✅
Cantidad                  ✅         ✅
Precio Unitario (venta)   ✅         ✅
Subtotal                  ✅         ✅
Descuento Aplicado        ✅         ✅
IVA                       ✅         ✅
TOTAL                     ✅         ✅
─────────────────────────────────────────
Costo Unitario            ❌         ✅
Costo Total               ❌         ✅
Margen %                  ❌         ✅
Ganancia Neta             ❌         ✅
─────────────────────────────────────────
Método Pago               ✅         ✅
Estado Pago               ✅         ✅
Estado Venta              ✅         ✅
```

---

### 3. CLIENTES

#### ✅ VENDEDOR PUEDE:
- Ver listado de clientes asignados a él
- Ver detalles básicos del cliente (nombre, teléfono, dirección)
- Ver historial de compras del cliente (solo de él)
- Registrar nuevo cliente
- Editar datos básicos autorizados:
  - Teléfono
  - Email
  - Dirección
  - Datos de contacto
- Registrar gestiones (notas, seguimiento)
- Ver saldo del cliente (si existe crédito)

#### ❌ VENDEDOR NO PUEDE:
- Ver clientes asignados a otros vendedores
- Ver todos los clientes de la farmacia
- Reasignar clientes (cambiar vendedor asignado)
- Eliminar cliente
- Ver datos tributarios (RUT, razón social si es empresa)
- Ver datos sensibles (alergias, restricciones médicas - salvo información básica)
- Cambiar clasificación del cliente
- Exportar base de clientes completa
- Ver cliente data de otros vendedores
- Ver análisis de rentabilidad del cliente

#### 🔒 FILTRADO BACKEND:

```python
# Vista Cliente - Solo clientes propios
def cliente_list_view(request):
    if request.user.role == 'VENDEDOR':
        clientes = Cliente.objects.filter(vendedor_asignado=request.user)
    else:  # ADMIN
        clientes = Cliente.objects.all()
    
    return render(request, 'clientes.html', {'clientes': clientes})

# Detalle Cliente - Validar acceso
def cliente_detail_view(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.user.role == 'VENDEDOR':
        if cliente.vendedor_asignado != request.user:
            raise PermissionDenied("No tienes acceso a este cliente")
    
    return render(request, 'cliente_detail.html', {'cliente': cliente})

# Editar Cliente
def cliente_edit_view(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.user.role == 'VENDEDOR':
        # Validar propiedad
        if cliente.vendedor_asignado != request.user:
            raise PermissionDenied("No puedes editar cliente ajeno")
        
        # Validar campos editables
        campos_permitidos = ['telefono', 'email', 'direccion', 'ciudad']
        for field in request.POST:
            if field not in campos_permitidos:
                raise PermissionDenied(f"No puedes editar {field}")
    
    # ... resto del código
```

#### 📊 CAMPOS VISIBLES POR CLIENTE:

```
CAMPO                      VENDEDOR    ADMIN
──────────────────────────────────────────────
Nombre                       ✅         ✅
Teléfono                     ✅         ✅
Email                        ✅         ✅
Dirección                    ✅         ✅
Ciudad                       ✅         ✅
Historial de Compras         ✅ (propias) ✅
Saldo (si hay crédito)       ✅         ✅
Notas de Seguimiento         ✅         ✅
──────────────────────────────────────────────
RUT/ID Tributario            ❌         ✅
Razón Social (empresa)       ❌         ✅
Datos Alergias/Restricciones ❌         ✅
Rentabilidad del Cliente      ❌         ✅
Margen Promedio              ❌         ✅
Vendedor Asignado (editable) ❌         ✅
Clasificación (VIP, etc)     ❌ (ver)   ✅ (editar)
Datos Sensibles              ❌         ✅
```

---

### 4. PRODUCTOS Y STOCK

#### ✅ VENDEDOR PUEDE:
- Ver catálogo de productos
- Ver nombre del producto
- Ver descripción
- Ver precio de venta autorizado
- Ver disponibilidad de stock (Sí/No, cantidad aproximada)
- Buscar productos
- Ver laboratorio (información pública)
- Ver dosis/presentación
- Ver foto/imagen del producto

#### ❌ VENDEDOR NO PUEDE:
- Editar producto
- Cambiar precio de venta
- Ver costo de compra
- Ver margen de ganancia del producto
- Ver proveedor (comprador interno)
- Modificar stock manualmente
- Ver historial de precios
- Ver fecha de vencimiento (solo para venta FIFO)
- Editar datos técnicos
- Ver rentabilidad del producto

#### 🔒 FILTRADO BACKEND:

```python
# Vista Producto - Sin campos sensibles
def producto_list_view(request):
    productos = Producto.objects.all()
    
    # Serializar solo campos permitidos
    if request.user.role == 'VENDEDOR':
        data = []
        for prod in productos:
            data.append({
                'id': prod.id,
                'nombre': prod.nombre,
                'descripcion': prod.descripcion,
                'precio_venta': prod.precio_venta,
                'stock_disponible': prod.stock > 0,
                'cantidad_aproximada': 'Alto' if prod.stock > 20 else 'Bajo',
                'laboratorio': prod.laboratorio,
                'dosis': prod.dosis,
                'imagen': prod.imagen.url if prod.imagen else None,
                # NO incluir:
                # - costo_unitario
                # - margen_porcentaje
                # - proveedor
                # - fecha_vencimiento
            })
        return JsonResponse(data, safe=False)
    
    # ADMIN ve todo
    return JsonResponse(list(productos.values()), safe=False)

# Endpoint para editar producto - Solo ADMIN
def editar_producto(request, producto_id):
    if request.user.role != 'ADMIN':
        raise PermissionDenied("Solo admin puede editar productos")
    
    # ... resto del código
```

#### 📊 CAMPOS VISIBLES POR PRODUCTO:

```
CAMPO                    VENDEDOR    ADMIN
──────────────────────────────────────────
ID Producto                ✅         ✅
Nombre                     ✅         ✅
Descripción                ✅         ✅
Laboratorio                ✅         ✅
Dosis/Presentación         ✅         ✅
Imagen                     ✅         ✅
Precio Venta Autorizado    ✅         ✅
Stock Disponible (Sí/No)   ✅         ✅
Cantidad Aproximada        ✅         ✅
──────────────────────────────────────────
Costo Unitario             ❌         ✅
Precio Costo               ❌         ✅
Margen %                   ❌         ✅
Margen $                   ❌         ✅
Rentabilidad               ❌         ✅
Proveedor                  ❌         ✅
Fecha Vencimiento          ❌         ✅
Última Compra              ❌         ✅
Cantidad Stock (exacta)    ✅         ✅
```

---

### 5. REPORTES

#### ✅ VENDEDOR PUEDE:
- Ver reporte de propias ventas
- Filtrar por fecha rango
- Ver cantidad de transacciones propias
- Ver total vendido (propias)
- Ver ticket promedio (propio)
- Ver productos más vendidos por él
- Ver clientes más atendidos
- Ver metas personales (si existen)
- Imprimir reporte propio
- Exportar reporte personal (PDF/Excel)

#### ❌ VENDEDOR NO PUEDE:
- Ver reportes globales de la farmacia
- Ver ventas de otros vendedores
- Ver comparativa entre vendedores
- Ver ranking de vendedores
- Ver ganancias/costos
- Ver margen de ganancia
- Ver análisis de rentabilidad
- Ver flujo de caja
- Ver análisis de stock
- Ver proveedores
- Ver reportes tributarios/impuestos

#### 🔒 FILTRADO BACKEND:

```python
# Reporte Vendedor
def reporte_vendedor_view(request):
    if request.user.role == 'VENDEDOR':
        # Solo datos propios
        ventas = Venta.objects.filter(
            vendedor=request.user,
            fecha__range=[fecha_inicio, fecha_fin]
        )
        
        datos = {
            'total_transacciones': ventas.count(),
            'monto_total_vendido': ventas.aggregate(Sum('total'))['total__sum'],
            'ticket_promedio': ventas.aggregate(Avg('total'))['total__avg'],
            'productos_top': get_productos_top_vendedor(request.user),
            'clientes_top': get_clientes_top(request.user),
            # NO incluir margen, costo, ganancia
        }
    else:  # ADMIN
        # Ver todo
        pass
    
    return render(request, 'reporte_vendedor.html', datos)

# Reporte Global - Solo ADMIN
def reporte_global_view(request):
    if request.user.role != 'ADMIN':
        raise PermissionDenied("Solo admin puede ver reportes globales")
    
    # Datos completos incluido costo, margen, ganancia
    pass
```

---

### 6. CONFIGURACIÓN

#### ✅ VENDEDOR PUEDE:
- Cambiar contraseña propia
- Ver datos de perfil
- Actualizar teléfono de contacto personal
- Ver información de comisión (si aplica)

#### ❌ VENDEDOR ABSOLUTAMENTE NO PUEDE:
- Acceder a configuración del sistema
- Crear/editar usuarios
- Modificar roles
- Ver logs de auditoría
- Configurar integraciones
- Ver parámetros tributarios
- Cambiar configuración de precios globales
- Ver datos de proveedores internos
- Modificar datos bancarios
- Ver información de impuestos
- Cambiar configuración de descuentos máximos

#### 🔒 PROTECCIÓN:

```python
# Middleware para bloquear acceso a configuración
def security_middleware(request):
    admin_routes = [
        '/admin/',
        '/configuracion/',
        '/usuarios/',
        '/roles/',
        '/integraciones/',
        '/parametros-tributarios/',
        '/auditoria/',
    ]
    
    if request.path in admin_routes:
        if request.user.role != 'ADMIN':
            raise PermissionDenied("Acceso denegado")
```

---

### 7. SEGURIDAD

#### ❌ VENDEDOR NO PUEDE HACER:
- Acceder a API interna
- Ver base de datos
- Modificar registros de auditoría
- Forzar anulación de ventas
- Cambiar estados de pago
- Importar/exportar datos
- Ejecutar consultas SQL
- Acceder a logs del sistema

---

## 📋 VISTAS PERMITIDAS Y BLOQUEADAS

```
VISTA/URL                           VENDEDOR    ADMIN
─────────────────────────────────────────────────────────
/farmacia/dashboard/                PERMITIDA   PERMITIDA
/farmacia/dashboard/personal/        PERMITIDA   PERMITIDA
/farmacia/dashboard/global/          BLOQUEADA   PERMITIDA
/farmacia/pos/                       PERMITIDA   PERMITIDA
/farmacia/ventas/                    PERMITIDA   PERMITIDA
  (solo propias)
/farmacia/ventas/[ID]/               PERMITIDA   PERMITIDA
  (validar propiedad)
/farmacia/ventas/editar/[ID]/        PERMITIDA   PERMITIDA
  (24 horas, validar)
/farmacia/ventas/eliminar/[ID]/      BLOQUEADA   PERMITIDA
/farmacia/clientes/                  PERMITIDA   PERMITIDA
  (solo propios)
/farmacia/clientes/[ID]/             PERMITIDA   PERMITIDA
  (validar propiedad)
/farmacia/clientes/crear/            PERMITIDA   PERMITIDA
/farmacia/clientes/editar/[ID]/      PERMITIDA   PERMITIDA
  (solo campos permitidos)
/farmacia/medicamentos/              PERMITIDA   PERMITIDA
  (sin costo/margen)
/farmacia/medicamentos/editar/       BLOQUEADA   PERMITIDA
/farmacia/reportes/personal/         PERMITIDA   PERMITIDA
/farmacia/reportes/global/           BLOQUEADA   PERMITIDA
/farmacia/reportes/vendedores/       BLOQUEADA   PERMITIDA
/farmacia/reportes/finanzas/         BLOQUEADA   PERMITIDA
/farmacia/admin/                     BLOQUEADA   PERMITIDA
/farmacia/configuracion/             BLOQUEADA   PERMITIDA
/farmacia/usuarios/                  BLOQUEADA   PERMITIDA
/farmacia/auditoria/                 BLOQUEADA   PERMITIDA
```

---

## 🛠️ IMPLEMENTACIÓN DJANGO

### 1. MODELO DE ROLES

```python
# models.py
from django.contrib.auth.models import User
from django.db import models

class RolPermiso(models.Model):
    ROLES = [
        ('ADMIN', 'Administrador/Dueño'),
        ('VENDEDOR', 'Vendedor'),
        ('GERENTE', 'Gerente de Tienda'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='VENDEDOR')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado_activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.rol}"

class Venta(models.Model):
    id = models.AutoField(primary_key=True)
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventas')
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)  # SECRETO - Solo ADMIN
    estado = models.CharField(max_length=20, default='ACTIVA')
    
    def obtener_datos_vendedor(self):
        """Retorna solo datos permitidos para vendedor"""
        return {
            'id': self.id,
            'fecha': self.fecha,
            'vendedor': self.vendedor.username,
            'cliente': self.cliente.nombre if self.cliente else 'Sin cliente',
            'total': self.total,
            'estado': self.estado,
            # NO incluir costo_total, margen, ganancia
        }

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12)  # SECRETO - Solo ADMIN
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    vendedor_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def obtener_datos_vendedor(self):
        """Retorna solo datos permitidos para vendedor"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            # NO incluir RUT
        }

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # SECRETO
    laboratorio = models.CharField(max_length=100)
    
    def obtener_datos_vendedor(self):
        """Retorna solo datos permitidos para vendedor"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'precio_venta': self.precio_venta,
            'laboratorio': self.laboratorio,
            # NO incluir costo_unitario, margen
        }
```

### 2. DECORADOR DE PERMISOS

```python
# permissions.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from .models import RolPermiso

def requiere_rol(rol_requerido):
    """Decorador que valida el rol del usuario"""
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                rol_permiso = RolPermiso.objects.get(user=request.user)
                if rol_permiso.rol != rol_requerido and rol_permiso.rol != 'ADMIN':
                    raise PermissionDenied(f"Requiere rol {rol_requerido}")
            except RolPermiso.DoesNotExist:
                raise PermissionDenied("Usuario sin rol asignado")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorador

def requiere_vendedor_o_admin(view_func):
    """Permite VENDEDOR y ADMIN"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            rol_permiso = RolPermiso.objects.get(user=request.user)
            if rol_permiso.rol not in ['VENDEDOR', 'ADMIN']:
                raise PermissionDenied("Acceso denegado")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def solo_admin(view_func):
    """Solo ADMIN puede acceder"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            rol_permiso = RolPermiso.objects.get(user=request.user)
            if rol_permiso.rol != 'ADMIN':
                raise PermissionDenied("Solo administrador")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper
```

### 3. VISTAS CON VALIDACIÓN

```python
# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from datetime import timedelta
from .models import Venta, Cliente, Producto, RolPermiso
from .permissions import requiere_vendedor_o_admin, solo_admin

@requiere_vendedor_o_admin
def listar_ventas(request):
    """Listar ventas - Filtrado por rol"""
    
    try:
        rol_permiso = RolPermiso.objects.get(user=request.user)
    except RolPermiso.DoesNotExist:
        raise PermissionDenied("Usuario sin rol")
    
    # VENDEDOR ve solo sus ventas
    if rol_permiso.rol == 'VENDEDOR':
        ventas = Venta.objects.filter(vendedor=request.user).order_by('-fecha')
        # Serializar solo campos permitidos
        ventas_data = [v.obtener_datos_vendedor() for v in ventas]
    else:  # ADMIN ve todo
        ventas = Venta.objects.all().order_by('-fecha')
        ventas_data = list(ventas.values())
    
    return render(request, 'ventas_list.html', {'ventas': ventas_data})

@requiere_vendedor_o_admin
def detalle_venta(request, venta_id):
    """Ver detalle de venta"""
    
    venta = get_object_or_404(Venta, id=venta_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve sus propias ventas
    if rol_permiso.rol == 'VENDEDOR' and venta.vendedor != request.user:
        raise PermissionDenied("No puedes ver venta de otro vendedor")
    
    # Preparar datos según rol
    if rol_permiso.rol == 'VENDEDOR':
        venta_data = venta.obtener_datos_vendedor()
    else:  # ADMIN
        venta_data = {
            'id': venta.id,
            'total': venta.total,
            'costo_total': venta.costo_total,
            'ganancia': venta.total - venta.costo_total,
            'margen': ((venta.total - venta.costo_total) / venta.total * 100) if venta.total > 0 else 0,
        }
    
    return render(request, 'venta_detail.html', {'venta': venta_data})

@require_http_methods(["POST"])
@requiere_vendedor_o_admin
def editar_venta(request, venta_id):
    """Editar venta - Validaciones estrictas"""
    
    venta = get_object_or_404(Venta, id=venta_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VALIDACIÓN 1: Debe ser propietario (si es vendedor)
    if rol_permiso.rol == 'VENDEDOR' and venta.vendedor != request.user:
        raise PermissionDenied("No puedes editar venta de otro vendedor")
    
    # VALIDACIÓN 2: Debe estar dentro de 24 horas
    if rol_permiso.rol == 'VENDEDOR':
        tiempo_transcurrido = now() - venta.fecha
        if tiempo_transcurrido > timedelta(hours=24):
            raise PermissionDenied("Solo puedes editar dentro de 24 horas")
    
    # VALIDACIÓN 3: No debe estar cerrada
    if venta.estado == 'CERRADA' and rol_permiso.rol == 'VENDEDOR':
        raise PermissionDenied("No puedes editar venta cerrada")
    
    # VALIDACIÓN 4: Campos editables
    campos_editables_vendedor = ['metodo_pago', 'descuento', 'notas']
    
    if rol_permiso.rol == 'VENDEDOR':
        for key in request.POST:
            if key not in campos_editables_vendedor:
                raise PermissionDenied(f"No puedes editar {key}")
    
    # Aplicar cambios
    for key, value in request.POST.items():
        if hasattr(venta, key):
            setattr(venta, key, value)
    
    venta.save()
    
    # Registrar en auditoría
    registrar_auditoria(
        usuario=request.user,
        accion='EDITAR_VENTA',
        objeto='Venta',
        objeto_id=venta.id,
        detalles=f"Campos editados: {', '.join(request.POST.keys())}"
    )
    
    return JsonResponse({'success': True, 'message': 'Venta actualizada'})

@solo_admin
def eliminar_venta(request, venta_id):
    """Eliminar venta - Solo ADMIN"""
    
    venta = get_object_or_404(Venta, id=venta_id)
    venta_id_ref = venta.id
    venta.delete()
    
    # Registrar en auditoría
    registrar_auditoria(
        usuario=request.user,
        accion='ELIMINAR_VENTA',
        objeto='Venta',
        objeto_id=venta_id_ref,
        detalles='Venta eliminada por administrador'
    )
    
    return JsonResponse({'success': True, 'message': 'Venta eliminada'})

@requiere_vendedor_o_admin
def listar_clientes(request):
    """Listar clientes - Filtrado por rol"""
    
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR ve solo sus clientes
    if rol_permiso.rol == 'VENDEDOR':
        clientes = Cliente.objects.filter(vendedor_asignado=request.user)
        clientes_data = [c.obtener_datos_vendedor() for c in clientes]
    else:  # ADMIN
        clientes = Cliente.objects.all()
        clientes_data = list(clientes.values())
    
    return render(request, 'clientes_list.html', {'clientes': clientes_data})

@requiere_vendedor_o_admin
def detalle_cliente(request, cliente_id):
    """Ver detalle de cliente"""
    
    cliente = get_object_or_404(Cliente, id=cliente_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve sus propios clientes
    if rol_permiso.rol == 'VENDEDOR' and cliente.vendedor_asignado != request.user:
        raise PermissionDenied("No tienes acceso a este cliente")
    
    # Preparar datos según rol
    if rol_permiso.rol == 'VENDEDOR':
        cliente_data = cliente.obtener_datos_vendedor()
    else:
        cliente_data = {
            'id': cliente.id,
            'nombre': cliente.nombre,
            'rut': cliente.rut,
            'email': cliente.email,
            'telefono': cliente.telefono,
            'direccion': cliente.direccion,
            'rentabilidad': calcular_rentabilidad_cliente(cliente),
        }
    
    return render(request, 'cliente_detail.html', {'cliente': cliente_data})

@requiere_vendedor_o_admin
def editar_cliente(request, cliente_id):
    """Editar cliente - Solo campos permitidos"""
    
    cliente = get_object_or_404(Cliente, id=cliente_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo edita sus propios clientes
    if rol_permiso.rol == 'VENDEDOR' and cliente.vendedor_asignado != request.user:
        raise PermissionDenied("No puedes editar cliente de otro vendedor")
    
    # Campos que VENDEDOR puede editar
    campos_editables_vendedor = ['telefono', 'email', 'direccion', 'ciudad']
    
    # Validar campos
    if rol_permiso.rol == 'VENDEDOR':
        for key in request.POST:
            if key not in campos_editables_vendedor:
                raise PermissionDenied(f"No puedes editar {key}")
    
    # Aplicar cambios
    for key, value in request.POST.items():
        if hasattr(cliente, key):
            setattr(cliente, key, value)
    
    cliente.save()
    
    # Registrar en auditoría
    registrar_auditoria(
        usuario=request.user,
        accion='EDITAR_CLIENTE',
        objeto='Cliente',
        objeto_id=cliente.id,
        detalles=f"Campos editados: {', '.join(request.POST.keys())}"
    )
    
    return JsonResponse({'success': True, 'message': 'Cliente actualizado'})

@requiere_vendedor_o_admin
def reporte_personal(request):
    """Reporte personal del vendedor"""
    
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve su reporte
    if rol_permiso.rol == 'VENDEDOR':
        usuario_filtro = request.user
    else:  # ADMIN puede filtrar por vendedor
        usuario_filtro = request.GET.get('vendedor', request.user)
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    ventas = Venta.objects.filter(vendedor=usuario_filtro)
    
    if fecha_inicio and fecha_fin:
        ventas = ventas.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    datos = {
        'total_transacciones': ventas.count(),
        'monto_total': ventas.aggregate(Sum('total'))['total__sum'] or 0,
        'ticket_promedio': ventas.aggregate(Avg('total'))['total__avg'] or 0,
        'productos_top': get_productos_top(usuario_filtro),
        'clientes_top': get_clientes_top(usuario_filtro),
    }
    
    # ADMIN ve también ganancia
    if rol_permiso.rol == 'ADMIN':
        datos['ganancia_total'] = sum(v.total - v.costo_total for v in ventas)
        datos['margen_promedio'] = calcular_margen_promedio(ventas)
    
    return render(request, 'reporte_personal.html', datos)

@solo_admin
def reporte_global(request):
    """Reporte global - Solo ADMIN"""
    
    ventas = Venta.objects.all()
    
    datos = {
        'total_ventas': ventas.count(),
        'monto_total': ventas.aggregate(Sum('total'))['total__sum'],
        'costo_total': ventas.aggregate(Sum('costo_total'))['costo_total__sum'],
        'ganancia_total': sum(v.total - v.costo_total for v in ventas),
        'ventas_por_vendedor': get_ventas_por_vendedor(),
        'rentabilidad': calcular_rentabilidad_global(),
    }
    
    return render(request, 'reporte_global.html', datos)

@requiere_vendedor_o_admin
def listar_productos(request):
    """Listar productos - Sin datos sensibles para vendedor"""
    
    productos = Producto.objects.all()
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve campos públicos
    if rol_permiso.rol == 'VENDEDOR':
        productos_data = [p.obtener_datos_vendedor() for p in productos]
    else:
        productos_data = list(productos.values())
    
    return render(request, 'productos_list.html', {'productos': productos_data})
```

### 4. MIDDLEWARE DE SEGURIDAD

```python
# middleware.py
from django.core.exceptions import PermissionDenied
from .models import RolPermiso

class VerificacionRolMiddleware:
    """Middleware que verifica rol en accesos a vistas protegidas"""
    
    RUTAS_ADMIN = [
        '/farmacia/admin/',
        '/farmacia/configuracion/',
        '/farmacia/usuarios/',
        '/farmacia/roles/',
        '/farmacia/auditoria/',
        '/farmacia/reportes/global/',
        '/farmacia/reportes/finanzas/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Validar acceso a rutas protegidas
        if any(request.path.startswith(ruta) for ruta in self.RUTAS_ADMIN):
            if request.user.is_authenticated:
                try:
                    rol_permiso = RolPermiso.objects.get(user=request.user)
                    if rol_permiso.rol != 'ADMIN':
                        raise PermissionDenied("Acceso denegado")
                except RolPermiso.DoesNotExist:
                    raise PermissionDenied("Usuario sin rol asignado")
        
        response = self.get_response(request)
        return response
```

---

## 🔍 VALIDACIONES BACKEND

### 1. AUDITORÍA Y REGISTRO

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class AuditoriaLog(models.Model):
    ACCIONES = [
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
        ('VER', 'Ver'),
        ('EXPORTAR', 'Exportar'),
        ('FALLIDO', 'Intento fallido'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    objeto = models.CharField(max_length=50)  # 'Venta', 'Cliente', etc
    objeto_id = models.IntegerField()
    detalles = models.TextField()
    resultado = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.objeto}"
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['accion', 'timestamp']),
        ]

# utils.py
def registrar_auditoria(usuario, accion, objeto, objeto_id, detalles, resultado=True, ip=None):
    """Registra acción en auditoría"""
    AuditoriaLog.objects.create(
        usuario=usuario,
        accion=accion,
        objeto=objeto,
        objeto_id=objeto_id,
        detalles=detalles,
        resultado=resultado,
        ip_address=ip,
    )

def registrar_intento_fallido(usuario, accion, objeto, razon, ip=None):
    """Registra intentos fallidos de acceso"""
    AuditoriaLog.objects.create(
        usuario=usuario,
        accion='FALLIDO',
        objeto=objeto,
        objeto_id=0,
        detalles=f"{accion}: {razon}",
        resultado=False,
        ip_address=ip,
    )
```

### 2. VALIDACIONES EN QUERYSET

```python
# managers.py
from django.db import models
from django.core.exceptions import PermissionDenied

class VentaQuerySet(models.QuerySet):
    def del_vendedor(self, usuario):
        """Filtra ventas del vendedor"""
        return self.filter(vendedor=usuario)
    
    def con_datos_vendedor(self):
        """Excluye datos sensibles"""
        return self.values(
            'id', 'fecha', 'vendedor__username', 'cliente__nombre',
            'total', 'estado'
        ).exclude_fields('costo_total', 'margen')

class VentaManager(models.Manager):
    def get_queryset(self):
        return VentaQuerySet(self.model, using=self._db)
    
    def para_vendedor(self, usuario):
        """Obtiene ventas permitidas para vendedor"""
        return self.get_queryset().del_vendedor(usuario)
```

### 3. SERIALIZERS CON FILTRADO

```python
# serializers.py
from rest_framework import serializers
from .models import Venta, Cliente, Producto

class VentaSerializerVendedor(serializers.ModelSerializer):
    """Serializer reducido para vendedor"""
    class Meta:
        model = Venta
        fields = [
            'id', 'fecha', 'vendedor', 'cliente', 'total', 'estado'
        ]

class VentaSerializerAdmin(serializers.ModelSerializer):
    """Serializer completo para admin"""
    ganancia = serializers.SerializerMethodField()
    margen = serializers.SerializerMethodField()
    
    class Meta:
        model = Venta
        fields = '__all__'
    
    def get_ganancia(self, obj):
        return obj.total - obj.costo_total
    
    def get_margen(self, obj):
        if obj.total > 0:
            return ((obj.total - obj.costo_total) / obj.total) * 100
        return 0

class ClienteSerializerVendedor(serializers.ModelSerializer):
    """Serializer reducido para vendedor"""
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'email', 'telefono', 'direccion']

class ClienteSerializerAdmin(serializers.ModelSerializer):
    """Serializer completo para admin"""
    class Meta:
        model = Cliente
        fields = '__all__'

class ProductoSerializerVendedor(serializers.ModelSerializer):
    """Serializer reducido para vendedor"""
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio_venta', 'laboratorio', 'stock']

class ProductoSerializerAdmin(serializers.ModelSerializer):
    """Serializer completo para admin"""
    class Meta:
        model = Producto
        fields = '__all__'
```

---

## 📊 TABLA RESUMEN: CAMPOS VISIBLES POR ROL

```
┌─────────────────────────┬──────────┬─────────┐
│ CAMPO/DATOS             │ VENDEDOR │ ADMIN   │
├─────────────────────────┼──────────┼─────────┤
│ VENTA                   │          │         │
│ - ID                    │ ✅       │ ✅      │
│ - Fecha                 │ ✅       │ ✅      │
│ - Total                 │ ✅       │ ✅      │
│ - Costo Total           │ ❌       │ ✅      │
│ - Margen %              │ ❌       │ ✅      │
│ - Ganancia $            │ ❌       │ ✅      │
├─────────────────────────┼──────────┼─────────┤
│ CLIENTE                 │          │         │
│ - Nombre                │ ✅       │ ✅      │
│ - Teléfono              │ ✅       │ ✅      │
│ - RUT                   │ ❌       │ ✅      │
│ - Email                 │ ✅       │ ✅      │
│ - Rentabilidad          │ ❌       │ ✅      │
├─────────────────────────┼──────────┼─────────┤
│ PRODUCTO                │          │         │
│ - Nombre                │ ✅       │ ✅      │
│ - Precio Venta          │ ✅       │ ✅      │
│ - Costo                 │ ❌       │ ✅      │
│ - Margen %              │ ❌       │ ✅      │
│ - Proveedor             │ ❌       │ ✅      │
├─────────────────────────┼──────────┼─────────┤
│ REPORTES                │          │         │
│ - Propio                │ ✅       │ ✅      │
│ - Global                │ ❌       │ ✅      │
│ - Finanzas              │ ❌       │ ✅      │
│ - Otros Vendedores      │ ❌       │ ✅      │
└─────────────────────────┴──────────┴─────────┘
```

---

## 🔒 CHECKLIST DE SEGURIDAD

- [ ] Validar rol en cada vista (decoradores)
- [ ] Filtrar queryset por usuario en backend
- [ ] No confiar en parámetros GET/POST para filtrar
- [ ] Usar ORM de Django (no SQL raw)
- [ ] Encriptar campos sensibles en BD
- [ ] Registrar todas las acciones en auditoría
- [ ] Validar tiempo de edición (24 horas)
- [ ] Bloquear acceso a URLs directas
- [ ] Usar middleware para seguridad adicional
- [ ] No serializar campos sensibles
- [ ] Validar permisos en API endpoints
- [ ] Usar HTTPS en producción
- [ ] Implementar rate limiting
- [ ] Logs de intentos fallidos
- [ ] Revisar auditoría regularmente
- [ ] Encriptar datos en tránsito
- [ ] Usar CSRF tokens
- [ ] Sanitizar inputs

---

## 📝 RECOMENDACIONES FINALES

### 1. NO hacer esto (INCORRECTO):
```python
# ❌ MALO - Confiar en frontend
if request.GET.get('vendedor_id'):
    ventas = Venta.objects.filter(vendedor_id=request.GET.get('vendedor_id'))

# ❌ MALO - Mostrar dato y ocultarlo con CSS
<div style="display:none">{{ venta.costo_total }}</div>

# ❌ MALO - Validar solo en serializer
def mi_vista(request):
    return JsonResponse(Venta.objects.all().values())  # Todo expuesto

# ❌ MALO - API sin autenticación
@api_view(['GET'])
def productos_api(request):
    return JsonResponse(Producto.objects.all().values())
```

### 2. Hacer esto (CORRECTO):
```python
# ✅ BUENO - Validar en backend
if request.user.role == 'VENDEDOR':
    ventas = Venta.objects.filter(vendedor=request.user)

# ✅ BUENO - No incluir dato en serializer
class VentaSerializer(serializers.ModelSerializer):
    fields = ['id', 'fecha', 'total']  # Excluye costo_total

# ✅ BUENO - Usar decorador de permisos
@requiere_vendedor_o_admin
def mi_vista(request):
    # Ya validado por decorador
    pass

# ✅ BUENO - API con autenticación y filtrado
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def productos_api(request):
    productos = Producto.objects.all()
    serializer = ProductoSerializerVendedor(productos, many=True)
    return Response(serializer.data)
```

### 3. Implementar en SETTINGS.py:

```python
# settings.py

# Middleware de seguridad
MIDDLEWARE = [
    # ... otros middleware
    'farmacia.middleware.VerificacionRolMiddleware',
]

# Autenticación
AUTHENTICATION_BACKENDS = [
    'farmacia.backends.CustomAuthBackend',
]

# Permisos por defecto
DEFAULT_PERMISSION_CLASSES = [
    'rest_framework.permissions.IsAuthenticated',
]

# Logging de auditoría
LOGGING = {
    'version': 1,
    'handlers': {
        'auditoria_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/auditoria.log',
        },
    },
    'loggers': {
        'auditoria': {
            'handlers': ['auditoria_file'],
            'level': 'INFO',
        },
    },
}
```

---

## 🎯 PRÓXIMOS PASOS

1. **Implementar modelos** de roles y auditoría
2. **Crear decoradores** de validación
3. **Refactorizar vistas** con filtrado
4. **Configurar middleware** de seguridad
5. **Crear fixtures** para pruebas
6. **Documentar cambios** en wiki interna
7. **Capacitar al equipo** sobre seguridad
8. **Realizar auditoría** de seguridad externa
9. **Monitorear logs** de acceso
10. **Revisar permisos** periódicamente

---

**Documento elaborado:** 2026-04-27  
**Versión:** 1.0  
**Clasificación:** Confidencial
