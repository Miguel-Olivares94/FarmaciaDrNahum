# farmacia/permissions.py
# Sistema de permisos y decoradores para roles

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from .models import RolPermiso, AuditoriaLog
from django.utils.timezone import now

# ============================================
# FUNCIONES AUXILIARES
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


# ============================================
# DECORADORES DE PERMISO
# ============================================

def requiere_rol(rol_requerido):
    """
    Decorador que valida que el usuario tenga un rol específico.
    Permite ADMIN siempre (acceso a todo).
    """
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
    """
    Decorador que permite VENDEDOR, GERENTE, CONTADOR y ADMIN.
    Bloquea otros roles.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")
        
        try:
            rol_permiso = RolPermiso.objects.get(user=request.user)
            if rol_permiso.rol not in ['VENDEDOR', 'ADMIN', 'GERENTE', 'CONTADOR']:
                registrar_auditoria(
                    usuario=request.user,
                    accion='ACCESODENEGADO',
                    objeto=view_func.__name__,
                    objeto_id=0,
                    detalles="Rol insuficiente para acceder a esta vista",
                    resultado=False,
                    ip=get_client_ip(request)
                )
                raise PermissionDenied("Acceso denegado")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def solo_admin(view_func):
    """
    Decorador que solo permite acceso a ADMIN.
    Bloquea todos los demás roles.
    """
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
                raise PermissionDenied("Solo administrador puede acceder aquí")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def puede_editar_venta(view_func):
    """
    Decorador que valida si usuario puede editar una venta específica.
    - ADMIN: puede editar cualquier venta
    - VENDEDOR: solo puede editar sus propias ventas dentro de 24h
    
    Espera que el view reciba venta_id como parámetro.
    """
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
        
        except Venta.DoesNotExist:
            raise PermissionDenied("Venta no encontrada")
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


def requiere_gerente_o_admin(view_func):
    """
    Decorador que solo permite GERENTE y ADMIN.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")
        
        try:
            rol_permiso = RolPermiso.objects.get(user=request.user)
            if rol_permiso.rol not in ['ADMIN', 'GERENTE']:
                registrar_auditoria(
                    usuario=request.user,
                    accion='ACCESODENEGADO',
                    objeto=view_func.__name__,
                    objeto_id=0,
                    detalles="Requiere rol GERENTE o ADMIN",
                    resultado=False,
                    ip=get_client_ip(request)
                )
                raise PermissionDenied("Requiere permisos de Gerente")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def requiere_contador_o_admin(view_func):
    """
    Decorador que solo permite CONTADOR y ADMIN para reportes financieros.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")
        
        try:
            rol_permiso = RolPermiso.objects.get(user=request.user)
            if rol_permiso.rol not in ['ADMIN', 'CONTADOR']:
                registrar_auditoria(
                    usuario=request.user,
                    accion='ACCESODENEGADO',
                    objeto=view_func.__name__,
                    objeto_id=0,
                    detalles="Requiere rol CONTADOR o ADMIN",
                    resultado=False,
                    ip=get_client_ip(request)
                )
                raise PermissionDenied("Requiere permisos de Contador")
        except RolPermiso.DoesNotExist:
            raise PermissionDenied("Usuario sin rol asignado")
        
        return view_func(request, *args, **kwargs)
    return wrapper
