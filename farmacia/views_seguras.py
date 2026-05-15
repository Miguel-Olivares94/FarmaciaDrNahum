# farmacia/views_seguras.py
# Vistas con validación de roles y permisos

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Avg, Count
from .models import Venta, Cliente, Medicamento, RolPermiso, AuditoriaLog
from .permissions import (
    requiere_vendedor_o_admin, 
    solo_admin,
    puede_editar_venta,
    requiere_gerente_o_admin,
    requiere_contador_o_admin,
    registrar_auditoria,
    get_client_ip
)


# ============================================
# VISTAS DE VENTAS CON SEGURIDAD
# ============================================

@requiere_vendedor_o_admin
def listar_ventas(request):
    """
    Listar ventas - Filtrado por rol.
    - VENDEDOR: solo sus propias ventas
    - ADMIN/GERENTE/CONTADOR: todas las ventas
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR ve solo sus ventas
    if rol_permiso.rol == 'VENDEDOR':
        ventas = Venta.objects.filter(vendedor=request.user).order_by('-fecha')
        ventas_data = []
        for v in ventas:
            ventas_data.append({
                'id': v.id,
                'numero_venta': v.numero_venta,
                'fecha': v.fecha.strftime('%d/%m/%Y %H:%M'),
                'medicamento': v.medicamento.nombre,
                'cantidad': v.cantidad,
                'total': f"${v.precio:,.2f}",
                'cliente': v.cliente.nombre if v.cliente else 'Sin cliente',
                'estado': v.get_estado_display(),
            })
    else:  # ADMIN/GERENTE/CONTADOR ve todo
        ventas = Venta.objects.all().order_by('-fecha')
        ventas_data = []
        for v in ventas:
            ventas_data.append({
                'id': v.id,
                'numero_venta': v.numero_venta,
                'fecha': v.fecha.strftime('%d/%m/%Y %H:%M'),
                'medicamento': v.medicamento.nombre,
                'cantidad': v.cantidad,
                'total': f"${v.precio:,.2f}",
                'cliente': v.cliente.nombre if v.cliente else 'Sin cliente',
                'vendedor': v.vendedor.get_full_name() or v.vendedor.username,
                'estado': v.get_estado_display(),
            })
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ListaVentas',
        objeto_id=0,
        detalles=f"Accedió a listado de ventas (rol: {rol_permiso.rol})",
        ip=get_client_ip(request)
    )
    
    return render(request, 'farmacia/ventas_list.html', {
        'ventas': ventas_data,
        'rol': rol_permiso.rol
    })


@requiere_vendedor_o_admin
def detalle_venta(request, venta_id):
    """
    Ver detalle de venta - Con validación de acceso.
    VENDEDOR solo ve sus propias ventas.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
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
    venta_data = {
        'id': venta.id,
        'numero_venta': venta.numero_venta,
        'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
        'medicamento': venta.medicamento.nombre,
        'cantidad': venta.cantidad,
        'precio_unitario': f"${venta.medicamento.precio:,.2f}",
        'total': f"${venta.precio:,.2f}",
        'cliente': venta.cliente.nombre if venta.cliente else 'Sin cliente',
        'vendedor': venta.vendedor.get_full_name() or venta.vendedor.username,
        'estado': venta.get_estado_display(),
        'puede_editar': rol_permiso.puede_editar_venta(venta),
        'puede_eliminar': rol_permiso.puede_eliminar_venta(),
    }
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='Venta',
        objeto_id=venta_id,
        detalles="Ver detalle de venta",
        ip=get_client_ip(request)
    )
    
    return render(request, 'farmacia/venta_detail.html', {
        'venta': venta_data,
        'rol': rol_permiso.rol
    })


@require_http_methods(["GET", "POST"])
@puede_editar_venta
def editar_venta(request, venta_id):
    """
    Editar venta - Con validaciones estrictas.
    VENDEDOR solo puede editar campos específicos dentro de 24h.
    GET: muestra formulario. POST: aplica cambios.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    # GET: redirigir a detalle (la edición se hace desde el detalle)
    if request.method == 'GET':
        return redirect('venta_detalle_segura', venta_id=venta_id)
    
    venta = get_object_or_404(Venta, id=venta_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # Campos que VENDEDOR puede editar
    campos_permitidos_vendedor = ['numero_venta', 'estado']
    
    # Validar campos
    cambios = []
    if rol_permiso.rol == 'VENDEDOR':
        for key in request.POST.keys():
            if key not in campos_permitidos_vendedor and key != 'csrfmiddlewaretoken':
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
        if key != 'csrfmiddlewaretoken' and hasattr(venta, key):
            old_value = getattr(venta, key)
            if old_value != value:
                setattr(venta, key, value)
                cambios.append(f"{key}: {old_value} → {value}")
    
    if cambios:
        venta.save()
        
        # Registrar en auditoría
        registrar_auditoria(
            usuario=request.user,
            accion='EDITAR',
            objeto='Venta',
            objeto_id=venta_id,
            detalles=f"Editó: {', '.join(cambios)}",
            ip=get_client_ip(request)
        )
    
    return JsonResponse({
        'success': True,
        'message': 'Venta actualizada correctamente',
        'cambios': cambios
    })


@require_http_methods(["POST"])
@solo_admin
def eliminar_venta(request, venta_id):
    """
    Eliminar venta - Solo ADMIN puede hacerlo.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    venta = get_object_or_404(Venta, id=venta_id)
    numero_venta = venta.numero_venta
    
    # Registrar antes de eliminar
    registrar_auditoria(
        usuario=request.user,
        accion='ELIMINAR',
        objeto='Venta',
        objeto_id=venta_id,
        detalles=f"Eliminó venta {numero_venta} de {venta.vendedor.username}",
        ip=get_client_ip(request)
    )
    
    venta.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Venta {numero_venta} eliminada correctamente'
    })


# ============================================
# VISTAS DE CLIENTES CON SEGURIDAD
# ============================================

@requiere_vendedor_o_admin
def listar_clientes(request):
    """
    Listar clientes - Filtrado por rol.
    VENDEDOR ve solo sus clientes (si están asignados).
    ADMIN ve todos.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR ve solo sus clientes (si tiene asignados)
    if rol_permiso.rol == 'VENDEDOR':
        # Por ahora, todos los clientes (en futuro, usar vendedor_asignado)
        clientes = Cliente.objects.all()
    else:  # ADMIN
        clientes = Cliente.objects.all()
    
    clientes_data = []
    for c in clientes:
        clientes_data.append({
            'id': c.id,
            'nombre': c.nombre,
            'email': c.email if rol_permiso.rol == 'ADMIN' else '***',
            'telefono': c.telefono,
            'total_compras': f"${c.compras_totales():,.2f}",
            'cantidad_compras': c.cantidad_compras(),
            'estado': 'Activo' if c.activo else 'Inactivo',
        })
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ListaClientes',
        objeto_id=0,
        detalles="Accedió a listado de clientes",
        ip=get_client_ip(request)
    )
    
    return render(request, 'farmacia/clientes_list.html', {
        'clientes': clientes_data,
        'rol': rol_permiso.rol
    })


@requiere_vendedor_o_admin
def detalle_cliente(request, cliente_id):
    """
    Ver detalle de cliente.
    VENDEDOR ve solo datos básicos.
    ADMIN ve todo incluido datos sensibles.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    cliente = get_object_or_404(Cliente, id=cliente_id)
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # Preparar datos según rol
    cliente_data = {
        'id': cliente.id,
        'nombre': cliente.nombre,
        'telefono': cliente.telefono,
        'total_compras': f"${cliente.compras_totales():,.2f}",
        'cantidad_compras': cliente.cantidad_compras(),
        'estado': 'Activo' if cliente.activo else 'Inactivo',
    }
    
    # Solo ADMIN ve datos sensibles
    if rol_permiso.rol == 'ADMIN':
        cliente_data.update({
            'rut_dni': cliente.rut_dni,
            'email': cliente.email,
            'fecha_nacimiento': cliente.fecha_nacimiento,
            'alergias': cliente.alergias,
            'medicamentos_contraindicados': cliente.medicamentos_contraindicados,
        })
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='Cliente',
        objeto_id=cliente_id,
        detalles="Ver detalle de cliente",
        ip=get_client_ip(request)
    )
    
    return render(request, 'farmacia/cliente_detail.html', {
        'cliente': cliente_data,
        'rol': rol_permiso.rol
    })


# ============================================
# VISTAS DE REPORTES CON SEGURIDAD
# ============================================

@requiere_vendedor_o_admin
def reporte_personal(request):
    """
    Reporte personal del vendedor.
    VENDEDOR solo ve su reporte.
    GERENTE/CONTADOR pueden filtrar vendedor.
    ADMIN ve todos.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    rol_permiso = RolPermiso.objects.get(user=request.user)
    
    # VENDEDOR solo ve su reporte
    if rol_permiso.rol == 'VENDEDOR':
        usuario_filtro = request.user
    else:  # ADMIN/GERENTE puede filtrar
        usuario_filtro = request.user
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    ventas = Venta.objects.filter(vendedor=usuario_filtro)
    
    if fecha_inicio and fecha_fin:
        ventas = ventas.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    # Calcular métricas permitidas para vendedor
    datos = {
        'vendedor': usuario_filtro.get_full_name() or usuario_filtro.username,
        'total_transacciones': ventas.count(),
        'monto_total': ventas.aggregate(Sum('precio'))['precio__sum'] or 0,
        'ticket_promedio': ventas.aggregate(Avg('precio'))['precio__avg'] or 0,
        'numero_clientes': ventas.values('cliente').distinct().count(),
    }
    
    # ADMIN ve también ganancia (cuando esté implementado)
    if rol_permiso.rol == 'ADMIN':
        datos['rol'] = 'ADMIN'
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ReportePersonal',
        objeto_id=0,
        detalles="Accedió a reporte personal",
        ip=get_client_ip(request)
    )
    
    return render(request, 'farmacia/reporte_personal.html', datos)


@requiere_gerente_o_admin
def reporte_global(request):
    """
    Reporte global - Solo GERENTE y ADMIN.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    ventas = Venta.objects.all()
    
    datos = {
        'total_ventas': ventas.count(),
        'monto_total': ventas.aggregate(Sum('precio'))['precio__sum'] or 0,
        'ticket_promedio': ventas.aggregate(Avg('precio'))['precio__avg'] or 0,
        'numero_clientes': ventas.values('cliente').distinct().count(),
    }
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ReporteGlobal',
        objeto_id=0,
        detalles="Accedió a reporte global",
        ip=get_client_ip(request)
    )
    
    return render(request, 'farmacia/reporte_global.html', datos)


@requiere_contador_o_admin
def reporte_finanzas(request):
    """
    Reporte financiero con márgenes y costos.
    Solo CONTADOR y ADMIN.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    ventas = Venta.objects.all()
    
    datos = {
        'total_ventas': ventas.count(),
        'monto_total': ventas.aggregate(Sum('precio'))['precio__sum'] or 0,
    }
    
    # Registrar acceso
    registrar_auditoria(
        usuario=request.user,
        accion='VER',
        objeto='ReporteFinanzas',
        objeto_id=0,
        detalles="Accedió a reporte financiero",
        ip=get_client_ip(request)
    )
    
    return render(request, 'farmacia/reporte_finanzas.html', datos)


# ============================================
# VISTAS DE AUDITORÍA (SOLO ADMIN)
# ============================================

@solo_admin
def ver_auditoria(request):
    """
    Ver logs de auditoría - Solo ADMIN.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    logs = AuditoriaLog.objects.all().order_by('-timestamp')[:1000]
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'usuario': log.usuario.username if log.usuario else 'Sistema',
            'accion': log.get_accion_display(),
            'objeto': log.objeto,
            'objeto_id': log.objeto_id,
            'detalles': log.detalles,
            'resultado': '✅ Exitoso' if log.resultado else '❌ Fallido',
            'ip': log.ip_address or 'N/A',
            'timestamp': log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        })
    
    return render(request, 'farmacia/auditoria.html', {'logs': logs_data})


@solo_admin
def ver_auditoria_usuario(request, usuario_id):
    """
    Ver logs de auditoría de un usuario específico - Solo ADMIN.
    """
    
    if not request.user.is_authenticated:
        return redirect('inicio_sesion')
    
    from django.contrib.auth.models import User
    
    usuario = get_object_or_404(User, id=usuario_id)
    logs = AuditoriaLog.objects.filter(usuario=usuario).order_by('-timestamp')[:500]
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'accion': log.get_accion_display(),
            'objeto': log.objeto,
            'objeto_id': log.objeto_id,
            'detalles': log.detalles,
            'resultado': '✅ Exitoso' if log.resultado else '❌ Fallido',
            'ip': log.ip_address or 'N/A',
            'timestamp': log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        })
    
    return render(request, 'farmacia/auditoria_usuario.html', {
        'usuario': usuario.username,
        'logs': logs_data
    })
