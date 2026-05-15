# 🛠️ IMPLEMENTACIÓN PRÁCTICA - Roles y Permisos

**Archivo:** `permissions_implementation.py`  
**Descripción:** Código listo para copiar y pegar en tu proyecto Django

---

## 📦 PASO 1: ACTUALIZAR MODELS.PY

```python
# farmacia/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Sum, Avg
from decimal import Decimal

# ============================================
# MODELO DE ROLES Y PERMISOS
# ============================================

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
            
            tiempo_transcurrido = now() - venta.fecha
            return tiempo_transcurrido.total_seconds() < 86400  # 24 horas
        
        return False

# ============================================
# MODELO DE VENTA ACTUALIZADO
# ============================================

class Venta(models.Model):
    """Modelo de venta con campos de seguridad"""
    
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('CERRADA', 'Cerrada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
    ]
    
    id = models.AutoField(primary_key=True)
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ventas_realizadas')
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # SECRETO - Solo para ADMIN
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    margen_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVA')
    metodo_pago = models.CharField(max_length=20, choices=PAGO_CHOICES)
    notas = models.TextField(blank=True)
    descuento_aplicado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-fecha']
        permissions = [
            ('ver_ventas_globales', 'Puede ver ventas globales'),
            ('editar_venta_ajena', 'Puede editar venta de otro vendedor'),
            ('eliminar_venta', 'Puede eliminar ventas'),
        ]
    
    def __str__(self):
        return f"Venta #{self.id} - {self.vendedor.first_name} ({self.fecha.date()})"
    
    def es_editable(self, usuario):
        """Valida si usuario puede editar"""
        rol = RolPermiso.objects.get(user=usuario)
        return rol.puede_editar_venta(self)
    
    def obtener_datos_vendedor(self):
        """Retorna solo datos permitidos para vendedor"""
        return {
            'id': self.id,
            'fecha': self.fecha.strftime('%d/%m/%Y %H:%M'),
            'vendedor': self.vendedor.get_full_name() or self.vendedor.username,
            'cliente': self.cliente.nombre if self.cliente else 'Sin cliente',
            'total': f"${self.total:,.2f}",
            'estado': self.get_estado_display(),
            'metodo_pago': self.get_metodo_pago_display(),
            'notas': self.notas,
            # NO INCLUIR: costo_total, margen_porcentaje
        }
    
    def obtener_datos_admin(self):
        """Retorna datos completos para admin"""
        ganancia = self.total - self.costo_total
        return {
            'id': self.id,
            'fecha': self.fecha.strftime('%d/%m/%Y %H:%M'),
            'vendedor': self.vendedor.get_full_name() or self.vendedor.username,
            'cliente': self.cliente.nombre if self.cliente else 'Sin cliente',
            'total': f"${self.total:,.2f}",
            'costo_total': f"${self.costo_total:,.2f}",
            'ganancia': f"${ganancia:,.2f}",
            'margen_porcentaje': f"{self.margen_porcentaje:.1f}%",
            'estado': self.get_estado_display(),
            'metodo_pago': self.get_metodo_pago_display(),
            'notas': self.notas,
        }

# ============================================
# MODELO DE CLIENTE ACTUALIZADO
# ============================================

class Cliente(models.Model):
    """Modelo de cliente con datos sensibles protegidos"""
    
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12)  # SECRETO
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    
    # Relación con vendedor
    vendedor_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clientes_asignados')
    
    # Datos sensibles
    datos_alergias = models.TextField(blank=True)  # SECRETO
    restricciones_medicas = models.TextField(blank=True)  # SECRETO
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.rut})"
    
    def obtener_datos_vendedor(self):
        """Retorna solo datos permitidos para vendedor"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'ciudad': self.ciudad,
            # NO INCLUIR: RUT, alergias, restricciones
        }
    
    def obtener_datos_admin(self):
        """Retorna datos completos para admin"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'rut': self.rut,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'ciudad': self.ciudad,
            'datos_alergias': self.datos_alergias,
            'restricciones_medicas': self.restricciones_medicas,
            'vendedor_asignado': self.vendedor_asignado.username if self.vendedor_asignado else 'N/A',
        }

# ============================================
# MODELO DE AUDITORÍA
# ============================================

class AuditoriaLog(models.Model):
    """Registra todas las acciones importantes"""
    
    ACCIONES_CHOICES = [
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
        ('VER', 'Ver'),
        ('EXPORTAR', 'Exportar'),
        ('INTENTOFALLIDO', 'Intento fallido de acceso'),
        ('ACCESODENEGADO', 'Acceso denegado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=20, choices=ACCIONES_CHOICES)
    objeto = models.CharField(max_length=50)  # 'Venta', 'Cliente', etc
    objeto_id = models.IntegerField()
    detalles = models.TextField()
    resultado = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['accion', 'timestamp']),
            models.Index(fields=['objeto', 'objeto_id']),
        ]
    
    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.objeto}"
```

---

## 🔐 PASO 2: CREAR PERMISSIONS.PY

```python
# farmacia/permissions.py

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from .models import RolPermiso, AuditoriaLog
from django.utils.timezone import now

# ============================================
# DECORADORES DE PERMISO
# ============================================

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

def get_client_ip(request):
    """Obtiene IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def requiere_rol(rol_requerido):
    """Decorador que valida el rol del usuario"""
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Usuario no autenticado")
            
            try:
                rol_permiso = RolPermiso.objects.get(user=request.user)
                
                # ADMIN ve todo
                if rol_permiso.rol == 'ADMIN':
                    return view_func(request, *args, **kwargs)
                
                # Validar rol específico
                if rol_permiso.rol != rol_requerido:
                    registrar_auditoria(
                        usuario=request.user,
                        accion='ACCESODENEGADO',
                        objeto=view_func.__name__,
                        objeto_id=0,
                        detalles=f"Intento de acceso a vista que requiere {rol_requerido}",
                        resultado=False,
                        ip=get_client_ip(request)
                    )
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
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")
        
        try:
            rol_permiso = RolPermiso.objects.get(user=request.user)
            if rol_permiso.rol not in ['VENDEDOR', 'ADMIN', 'GERENTE']:
                registrar_auditoria(
                    usuario=request.user,
                    accion='ACCESODENEGADO',
                    objeto=view_func.__name__,
                    objeto_id=0,
                    detalles="Rol insuficiente",
                    resultado=False,
                    ip=get_client_ip(request)
                )
                raise PermissionDenied("Acceso denegado")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def solo_admin(view_func):
    """Solo ADMIN puede acceder"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")
        
        try:
            rol_permiso = RolPermiso.objects.get(user=request.user)
            if rol_permiso.rol != 'ADMIN':
                registrar_auditoria(
                    usuario=request.user,
                    accion='ACCESODENEGADO',
                    objeto=view_func.__name__,
                    objeto_id=0,
                    detalles="Solo acceso para ADMIN",
                    resultado=False,
                    ip=get_client_ip(request)
                )
                raise PermissionDenied("Solo administrador")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def puede_editar_venta(view_func):
    """Valida si usuario puede editar venta"""
    @wraps(view_func)
    def wrapper(request, venta_id, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")
        
        from .models import Venta
        
        try:
            venta = Venta.objects.get(id=venta_id)
            rol_permiso = RolPermiso.objects.get(user=request.user)
            
            # ADMIN puede editar todo
            if rol_permiso.rol == 'ADMIN':
                return view_func(request, venta_id, *args, **kwargs)
            
            # VENDEDOR solo puede editar sus propias ventas dentro de 24h
            if rol_permiso.rol == 'VENDEDOR':
                if venta.vendedor != request.user:
                    registrar_auditoria(
                        usuario=request.user,
                        accion='ACCESODENEGADO',
                        objeto='Venta',
                        objeto_id=venta_id,
                        detalles="Intento de editar venta de otro vendedor",
                        resultado=False,
                        ip=get_client_ip(request)
                    )
                    raise PermissionDenied("No puedes editar venta de otro vendedor")
                
                # Verificar 24 horas
                tiempo_transcurrido = now() - venta.fecha
                if tiempo_transcurrido.total_seconds() > 86400:
                    registrar_auditoria(
                        usuario=request.user,
                        accion='ACCESODENEGADO',
                        objeto='Venta',
                        objeto_id=venta_id,
                        detalles="Intento de editar venta fuera de 24 horas",
                        resultado=False,
                        ip=get_client_ip(request)
                    )
                    raise PermissionDenied("Solo puedes editar dentro de 24 horas")
        
        except Exception as e:
            registrar_auditoria(
                usuario=request.user,
                accion='INTENTOFALLIDO',
                objeto='Venta',
                objeto_id=venta_id,
                detalles=str(e),
                resultado=False,
                ip=get_client_ip(request)
            )
            raise
        
        return view_func(request, venta_id, *args, **kwargs)
    return wrapper
```

---

## 🔍 PASO 3: CREAR VIEWS_SEGURAS.PY

```python
# farmacia/views_seguras.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Avg, Count
from .models import Venta, Cliente, Producto, RolPermiso, AuditoriaLog
from .permissions import (
    requiere_vendedor_o_admin, 
    solo_admin,
    puede_editar_venta,
    registrar_auditoria,
    get_client_ip
)

# ============================================
# VISTAS DE VENTAS
# ============================================

@requiere_vendedor_o_admin
def listar_ventas(request):
    """Listar ventas - Filtrado por rol"""
    
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR ve solo sus ventas
    if rol_permiso.rol == 'VENDEDOR':
        ventas = Venta.objects.filter(vendedor=request.user).order_by('-fecha')
        ventas_serializado = [v.obtener_datos_vendedor() for v in ventas]
    else:  # ADMIN/GERENTE/CONTADOR ve todo
        ventas = Venta.objects.all().order_by('-fecha')
        ventas_serializado = [v.obtener_datos_admin() for v in ventas]
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ListaVentas',
        objeto_id=0,
        detalles=f"Accedió a listado de ventas",
        ip=get_client_ip(request)
    )
    
    return render(request, 'ventas_list.html', {'ventas': ventas_serializado})

@requiere_vendedor_o_admin
def detalle_venta(request, venta_id):
    """Ver detalle de venta - Con validación de acceso"""
    
    venta = get_object_or_404(Venta, id=venta_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve sus propias ventas
    if rol_permiso.rol == 'VENDEDOR' and venta.vendedor != request.user:
        registrar_auditoria(
            usuario=request.user,
            accion='ACCESODENEGADO',
            objeto='Venta',
            objeto_id=venta_id,
            detalles="Intento de ver venta de otro vendedor",
            resultado=False,
            ip=get_client_ip(request)
        )
        raise PermissionDenied("No tienes acceso a esta venta")
    
    # Preparar datos según rol
    if rol_permiso.rol == 'VENDEDOR':
        venta_data = venta.obtener_datos_vendedor()
    else:
        venta_data = venta.obtener_datos_admin()
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='Venta',
        objeto_id=venta_id,
        detalles="Ver detalle de venta",
        ip=get_client_ip(request)
    )
    
    return render(request, 'venta_detail.html', {'venta': venta_data})

@require_http_methods(["POST"])
@puede_editar_venta
def editar_venta(request, venta_id):
    """Editar venta - Con validaciones estrictas"""
    
    venta = get_object_or_404(Venta, id=venta_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # Campos que VENDEDOR puede editar
    campos_permitidos_vendedor = ['metodo_pago', 'descuento_aplicado', 'notas']
    
    # Validar campos
    if rol_permiso.rol == 'VENDEDOR':
        for key in request.POST.keys():
            if key not in campos_permitidos_vendedor:
                registrar_auditoria(
                    usuario=request.user,
                    accion='ACCESODENEGADO',
                    objeto='Venta',
                    objeto_id=venta_id,
                    detalles=f"Intento de editar campo no permitido: {key}",
                    resultado=False,
                    ip=get_client_ip(request)
                )
                raise PermissionDenied(f"No puedes editar {key}")
    
    # Aplicar cambios
    for key, value in request.POST.items():
        if hasattr(venta, key):
            setattr(venta, key, value)
    
    venta.save()
    
    # Registrar en auditoría
    registrar_auditoria(
        usuario=request.user,
        accion='EDITAR',
        objeto='Venta',
        objeto_id=venta_id,
        detalles=f"Editó campos: {', '.join(request.POST.keys())}",
        ip=get_client_ip(request)
    )
    
    return JsonResponse({'success': True, 'message': 'Venta actualizada'})

@require_http_methods(["POST"])
@solo_admin
def eliminar_venta(request, venta_id):
    """Eliminar venta - Solo ADMIN"""
    
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Registrar antes de eliminar
    registrar_auditoria(
        usuario=request.user,
        accion='ELIMINAR',
        objeto='Venta',
        objeto_id=venta_id,
        detalles=f"Eliminó venta de {venta.vendedor.username}",
        ip=get_client_ip(request)
    )
    
    venta.delete()
    
    return JsonResponse({'success': True, 'message': 'Venta eliminada'})

# ============================================
# VISTAS DE CLIENTES
# ============================================

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
        clientes_data = [c.obtener_datos_admin() for c in clientes]
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ListaClientes',
        objeto_id=0,
        detalles="Accedió a listado de clientes",
        ip=get_client_ip(request)
    )
    
    return render(request, 'clientes_list.html', {'clientes': clientes_data})

@requiere_vendedor_o_admin
def detalle_cliente(request, cliente_id):
    """Ver detalle de cliente"""
    
    cliente = get_object_or_404(Cliente, id=cliente_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve sus propios clientes
    if rol_permiso.rol == 'VENDEDOR' and cliente.vendedor_asignado != request.user:
        registrar_auditoria(
            usuario=request.user,
            accion='ACCESODENEGADO',
            objeto='Cliente',
            objeto_id=cliente_id,
            detalles="Intento de ver cliente de otro vendedor",
            resultado=False,
            ip=get_client_ip(request)
        )
        raise PermissionDenied("No tienes acceso a este cliente")
    
    # Preparar datos según rol
    if rol_permiso.rol == 'VENDEDOR':
        cliente_data = cliente.obtener_datos_vendedor()
    else:
        cliente_data = cliente.obtener_datos_admin()
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='Cliente',
        objeto_id=cliente_id,
        detalles="Ver detalle de cliente",
        ip=get_client_ip(request)
    )
    
    return render(request, 'cliente_detail.html', {'cliente': cliente_data})

# ============================================
# VISTAS DE REPORTES
# ============================================

@requiere_vendedor_o_admin
def reporte_personal(request):
    """Reporte personal del vendedor"""
    
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve su reporte
    if rol_permiso.rol == 'VENDEDOR':
        usuario_filtro = request.user
    else:  # ADMIN/GERENTE puede filtrar
        usuario_filtro = request.GET.get('vendedor_id', request.user)
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    ventas = Venta.objects.filter(vendedor=usuario_filtro)
    
    if fecha_inicio and fecha_fin:
        ventas = ventas.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    # Calcular métricas permitidas para vendedor
    datos = {
        'total_transacciones': ventas.count(),
        'monto_total': ventas.aggregate(Sum('total'))['total__sum'] or 0,
        'ticket_promedio': ventas.aggregate(Avg('total'))['total__avg'] or 0,
        'numero_clientes': ventas.values('cliente').distinct().count(),
    }
    
    # ADMIN ve también ganancia
    if rol_permiso.rol == 'ADMIN':
        datos['costo_total'] = ventas.aggregate(Sum('costo_total'))['costo_total__sum'] or 0
        datos['ganancia_total'] = datos['monto_total'] - datos['costo_total']
        datos['margen_promedio'] = ventas.aggregate(Avg('margen_porcentaje'))['margen_porcentaje__avg'] or 0
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ReportePersonal',
        objeto_id=0,
        detalles="Accedió a reporte personal",
        ip=get_client_ip(request)
    )
    
    return render(request, 'reporte_personal.html', datos)

@solo_admin
def reporte_global(request):
    """Reporte global - Solo ADMIN"""
    
    ventas = Venta.objects.all()
    
    datos = {
        'total_ventas': ventas.count(),
        'monto_total': ventas.aggregate(Sum('total'))['total__sum'] or 0,
        'costo_total': ventas.aggregate(Sum('costo_total'))['costo_total__sum'] or 0,
        'ganancia_total': 0,  # Será calculado arriba
        'margen_promedio': ventas.aggregate(Avg('margen_porcentaje'))['margen_porcentaje__avg'] or 0,
    }
    
    datos['ganancia_total'] = datos['monto_total'] - datos['costo_total']
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ReporteGlobal',
        objeto_id=0,
        detalles="Accedió a reporte global",
        ip=get_client_ip(request)
    )
    
    return render(request, 'reporte_global.html', datos)

@solo_admin
def ver_auditoria(request):
    """Ver logs de auditoría - Solo ADMIN"""
    
    logs = AuditoriaLog.objects.all().order_by('-timestamp')[:1000]
    
    return render(request, 'auditoria.html', {'logs': logs})
```

---

## 📋 PASO 4: ACTUALIZAR URLS.PY

```python
# farmacia/urls.py - Agregar estas líneas

from .views_seguras import (
    listar_ventas,
    detalle_venta,
    editar_venta,
    eliminar_venta,
    listar_clientes,
    detalle_cliente,
    reporte_personal,
    reporte_global,
    ver_auditoria,
)

urlpatterns = [
    # ... URLs existentes
    
    # URLs de Ventas con seguridad
    path('ventas/', listar_ventas, name='ventas_seguras'),
    path('ventas/<int:venta_id>/', detalle_venta, name='venta_detalle'),
    path('ventas/<int:venta_id>/editar/', editar_venta, name='venta_editar'),
    path('ventas/<int:venta_id>/eliminar/', eliminar_venta, name='venta_eliminar'),
    
    # URLs de Clientes con seguridad
    path('clientes/', listar_clientes, name='clientes_seguras'),
    path('clientes/<int:cliente_id>/', detalle_cliente, name='cliente_detalle'),
    
    # URLs de Reportes con seguridad
    path('reportes/personal/', reporte_personal, name='reporte_personal'),
    path('reportes/global/', reporte_global, name='reporte_global'),
    path('auditoria/', ver_auditoria, name='ver_auditoria'),
]
```

---

## 🛡️ PASO 5: MIDDLEWARE DE SEGURIDAD

```python
# farmacia/middleware.py

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from .models import RolPermiso, AuditoriaLog
import logging

logger = logging.getLogger('auditoria')

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
        if self.es_ruta_admin(request.path):
            if request.user.is_authenticated:
                try:
                    rol_permiso = RolPermiso.objects.get(user=request.user)
                    if rol_permiso.rol != 'ADMIN':
                        self.registrar_acceso_denegado(request)
                        return HttpResponse('Acceso denegado', status=403)
                except RolPermiso.DoesNotExist:
                    return HttpResponse('Usuario sin rol', status=403)
            else:
                return HttpResponse('No autenticado', status=401)
        
        response = self.get_response(request)
        return response
    
    def es_ruta_admin(self, path):
        return any(path.startswith(ruta) for ruta in self.RUTAS_ADMIN)
    
    def registrar_acceso_denegado(self, request):
        """Registra intentos de acceso denegado"""
        AuditoriaLog.objects.create(
            usuario=request.user,
            accion='ACCESODENEGADO',
            objeto=request.path,
            objeto_id=0,
            detalles=f"Intento de acceder a ruta protegida: {request.path}",
            resultado=False,
            ip_address=self.get_client_ip(request),
        )
        logger.warning(f"Acceso denegado: {request.user} - {request.path}")
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

---

## ⚙️ PASO 6: CONFIGURAR SETTINGS.PY

```python
# settings.py

MIDDLEWARE = [
    # ... otros middlewares
    'farmacia.middleware.VerificacionRolMiddleware',
]

# Logging de auditoría
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'auditoria_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/auditoria.log',
            'formatter': 'verbose',
        },
        'seguridad_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/seguridad.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'auditoria': {
            'handlers': ['auditoria_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'seguridad': {
            'handlers': ['seguridad_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

---

## 🚀 COMANDO PARA CREAR USUARIOS CON ROLES

```python
# Crear archivo: farmacia/management/commands/crear_usuarios_roles.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from farmacia.models import RolPermiso

class Command(BaseCommand):
    help = 'Crea usuarios de prueba con diferentes roles'

    def handle(self, *args, **kwargs):
        # Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Administrador',
                'email': 'admin@farmacia.com'
            }
        )
        admin.set_password('Admin2026!')
        admin.save()
        
        rol_admin, _ = RolPermiso.objects.get_or_create(
            user=admin,
            defaults={'rol': 'ADMIN'}
        )
        
        self.stdout.write(f"✅ Admin creado: admin / Admin2026!")
        
        # Vendedor 1
        vendedor1, created = User.objects.get_or_create(
            username='vendedor1',
            defaults={
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'email': 'juan@farmacia.com'
            }
        )
        vendedor1.set_password('Vendedor123!')
        vendedor1.save()
        
        rol_v1, _ = RolPermiso.objects.get_or_create(
            user=vendedor1,
            defaults={'rol': 'VENDEDOR'}
        )
        
        self.stdout.write(f"✅ Vendedor creado: vendedor1 / Vendedor123!")

# Ejecutar con:
# python manage.py crear_usuarios_roles
```

---

**Versión:** 1.0  
**Fecha:** 2026-04-27  
**Clasificación:** Confidencial
