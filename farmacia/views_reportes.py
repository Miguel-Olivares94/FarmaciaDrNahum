# farmacia/views_reportes.py
"""
Vistas para Dashboard y Reportes de Ventas.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from .models import Venta, Medicamento, Boleta, CarritoVenta
from .pdf_generator import generar_pdf_reporte_ventas


def es_supervisor(user):
    """Verifica si usuario es supervisor/admin"""
    return user.is_staff or user.is_superuser


@login_required
def dashboard_reportes(request):
    """
    Dashboard principal con métricas de ventas.
    
    GET /pos/v2/reportes/
    """
    # Verificar permisos
    if not es_supervisor(request.user):
        return render(request, 'farmacia/error_permiso.html', status=403)
    
    # Período seleccionado
    periodo = request.GET.get('periodo', '30')  # días
    try:
        dias = int(periodo)
    except:
        dias = 30
    
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    # Filtrar ventas del período
    ventas = Venta.objects.filter(
        fecha__gte=fecha_inicio,
        estado='COMPLETADA'
    )
    
    # === MÉTRICAS PRINCIPALES ===
    total_ventas = ventas.aggregate(Sum('precio'))['precio__sum'] or Decimal('0.00')
    cantidad_ventas = ventas.count()
    promedio_venta = (total_ventas / cantidad_ventas) if cantidad_ventas > 0 else Decimal('0.00')
    
    # Medicamentos más vendidos
    top_productos = Medicamento.objects.filter(
        venta__in=ventas
    ).annotate(
        cantidad_vendida=Count('venta')
    ).order_by('-cantidad_vendida')[:10]
    
    # Vendedores top
    vendedores_top = ventas.values('vendedor__first_name', 'vendedor__last_name').annotate(
        total=Sum('precio'),
        cantidad=Count('id')
    ).order_by('-total')[:5]
    
    # Información para gráficos
    ventas_por_dia = ventas.extra(
        select={'fecha_dia': 'DATE(fecha)'}
    ).values('fecha_dia').annotate(
        total=Sum('precio'),
        cantidad=Count('id')
    ).order_by('fecha_dia')
    
    # Convertir a JSON para charts
    dias_labels = [v['fecha_dia'].strftime('%d/%m') for v in ventas_por_dia]
    dias_data = [int(v['total']) for v in ventas_por_dia]
    
    context = {
        'total_ventas': f"${int(total_ventas):,}".replace(',', '.'),
        'cantidad_ventas': cantidad_ventas,
        'promedio_venta': f"${int(promedio_venta):,}".replace(',', '.'),
        'top_productos': top_productos,
        'vendedores_top': vendedores_top,
        'periodo': dias,
        'fecha_inicio': fecha_inicio.date(),
        'fecha_fin': timezone.now().date(),
        'dias_labels': json.dumps(dias_labels),
        'dias_data': json.dumps(dias_data),
    }
    
    return render(request, 'farmacia/dashboard_reportes.html', context)


@login_required
def reporte_ventas_diarias(request):
    """
    API JSON con datos de ventas diarias.
    
    GET /pos/v2/reportes/ventas-diarias/?dias=30
    """
    if not es_supervisor(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    ventas = Venta.objects.filter(
        fecha__gte=fecha_inicio,
        estado='COMPLETADA'
    ).extra(
        select={'fecha_dia': 'DATE(fecha)'}
    ).values('fecha_dia').annotate(
        total=Sum('precio'),
        cantidad=Count('id')
    ).order_by('fecha_dia')
    
    datos = []
    for v in ventas:
        datos.append({
            'fecha': v['fecha_dia'].strftime('%Y-%m-%d'),
            'total': str(v['total']),
            'cantidad': v['cantidad'],
        })
    
    return JsonResponse({'datos': datos})


@login_required
def reporte_top_productos(request):
    """
    API JSON con productos más vendidos.
    
    GET /pos/v2/reportes/top-productos/?limite=10&dias=30
    """
    if not es_supervisor(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    limite = int(request.GET.get('limite', 10))
    dias = int(request.GET.get('dias', 30))
    
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    top = Medicamento.objects.filter(
        venta__fecha__gte=fecha_inicio,
        venta__estado='COMPLETADA'
    ).annotate(
        cantidad_vendida=Sum('venta__cantidad'),
        ingresos=Sum('venta__precio')
    ).order_by('-cantidad_vendida')[:limite]
    
    datos = []
    for med in top:
        datos.append({
            'nombre': med.nombre,
            'cantidad': med.cantidad_vendida or 0,
            'ingresos': str(med.ingresos or 0),
            'stock_actual': med.stock,
        })
    
    return JsonResponse({'productos': datos})


@login_required
def reporte_vendedores(request):
    """
    Reporte de desempeño por vendedor.
    
    GET /pos/v2/reportes/vendedores/?dias=30
    """
    if not es_supervisor(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    vendedores = Venta.objects.filter(
        fecha__gte=fecha_inicio,
        estado='COMPLETADA'
    ).values(
        'vendedor__id',
        'vendedor__first_name',
        'vendedor__last_name',
        'vendedor__username'
    ).annotate(
        total_vendido=Sum('precio'),
        cantidad_transacciones=Count('id'),
        promedio_transaccion=Sum('precio') / Count('id')
    ).order_by('-total_vendido')
    
    datos = []
    for v in vendedores:
        datos.append({
            'vendedor': f"{v['vendedor__first_name']} {v['vendedor__last_name']}",
            'username': v['vendedor__username'],
            'total_vendido': str(v['total_vendido']),
            'transacciones': v['cantidad_transacciones'],
            'promedio': str(v['promedio_transaccion'] or 0),
        })
    
    return JsonResponse({'vendedores': datos})


@login_required
def reporte_ingresos(request):
    """
    Análisis de ingresos y tendencias.
    
    GET /pos/v2/reportes/ingresos/?mes=actual
    """
    if not es_supervisor(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    hoy = timezone.now().date()
    
    # Ingresos de hoy
    ingresos_hoy = Venta.objects.filter(
        fecha__date=hoy,
        estado='COMPLETADA'
    ).aggregate(Sum('precio'))['precio__sum'] or Decimal('0.00')
    
    # Ingresos de esta semana
    hace_7_dias = hoy - timedelta(days=7)
    ingresos_semana = Venta.objects.filter(
        fecha__date__gte=hace_7_dias,
        estado='COMPLETADA'
    ).aggregate(Sum('precio'))['precio__sum'] or Decimal('0.00')
    
    # Ingresos del mes
    hace_30_dias = hoy - timedelta(days=30)
    ingresos_mes = Venta.objects.filter(
        fecha__date__gte=hace_30_dias,
        estado='COMPLETADA'
    ).aggregate(Sum('precio'))['precio__sum'] or Decimal('0.00')
    
    # IVA recaudado
    iva_mes = ingresos_mes * Decimal('0.19') if ingresos_mes > 0 else Decimal('0.00')
    
    return JsonResponse({
        'ingresos_hoy': str(ingresos_hoy),
        'ingresos_semana': str(ingresos_semana),
        'ingresos_mes': str(ingresos_mes),
        'iva_mes': str(iva_mes),
    })


@login_required
def descargar_reporte_pdf(request):
    """
    Descarga reporte de ventas en PDF.
    
    GET /pos/v2/reportes/descargar-pdf/?dias=30
    """
    if not es_supervisor(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    ventas = Venta.objects.filter(
        fecha__gte=fecha_inicio,
        estado='COMPLETADA'
    ).order_by('-fecha')
    
    pdf_buffer = generar_pdf_reporte_ventas(ventas, f"Reporte de Ventas - Últimos {dias} días")
    
    from django.http import FileResponse
    response = FileResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{dias}dias.pdf"'
    
    return response


@login_required
def anular_venta_desde_reporte(request, numero_venta):
    """
    Anular venta desde reporte (solo supervisores).
    
    POST /pos/v2/reportes/anular/{numero_venta}/
    """
    if not es_supervisor(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        venta = Venta.objects.get(numero_venta=numero_venta)
        
        if request.method == 'POST':
            motivo = request.POST.get('motivo', 'Anulación desde reportes')
            
            # Revertir stock
            if venta.medicamento and venta.estado == 'COMPLETADA':
                venta.medicamento.stock += venta.cantidad
                venta.medicamento.save()
            
            # Cambiar estado
            venta.estado = 'ANULADA'
            venta.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Venta {numero_venta} anulada correctamente'
            })
        
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    except Venta.DoesNotExist:
        return JsonResponse({'error': 'Venta no encontrada'}, status=404)
