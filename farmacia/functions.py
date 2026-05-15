from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseServerError
from datetime import date, timedelta

def LogIn(request, username, password):
    try:
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_active:
            login(request, user)
            # Redirige al usuario a la página deseada después del inicio de sesión
            return redirect('farmacia_main')
        else:
            # Si la autenticación falla o el usuario no está activo, muestra un mensaje de error
            messages.error(request, 'Credenciales incorrectas o usuario inactivo.')
            # Puedes redirigir a la página de inicio de sesión o cualquier otra página
            return render(request, 'inicio_sesion.html')
    except Exception as e:
        # Maneja cualquier otra excepción que pueda ocurrir durante el proceso de inicio de sesión
        return HttpResponseServerError(f"Error durante el inicio de sesión: {str(e)}")


# =====================================================================
# WEEK 3: FUNCIONES PARA STOCK TRANSACCIONAL CON FIFO
# =====================================================================

def obtener_lotes_fifo(medicamento):
    """
    Obtiene lotes de medicamento ordenados por FIFO (vencimiento más cercano primero).
    Retorna solo lotes vigentes y con stock disponible.
    """
    from .models import LoteMedicamento
    
    hoy = date.today()
    lotes = LoteMedicamento.objects.filter(
        medicamento=medicamento,
        cantidad_disponible__gt=0,
        fecha_vencimiento__gte=hoy  # Solo lotes no vencidos
    ).order_by('fecha_vencimiento')  # FIFO: primero vencen, primero salen
    
    return lotes


def obtener_lote_para_venta(medicamento, cantidad):
    """
    Obtiene el lote FIFO que puede suplir la cantidad requerida.
    Si el lote más antiguo no tiene suficiente stock, usa múltiples lotes.
    Retorna lista de tuplas (lote, cantidad_a_usar).
    """
    from .models import LoteMedicamento
    
    lotes_info = []
    cantidad_pendiente = cantidad
    
    for lote in obtener_lotes_fifo(medicamento):
        if cantidad_pendiente <= 0:
            break
        
        cantidad_a_usar = min(lote.cantidad_disponible, cantidad_pendiente)
        lotes_info.append((lote, cantidad_a_usar))
        cantidad_pendiente -= cantidad_a_usar
    
    # Si quedan cantidades pendientes, no hay suficiente stock FIFO
    if cantidad_pendiente > 0:
        return None
    
    return lotes_info


def validar_vencimiento_medicamento(medicamento, dias_minimo=7):
    """
    Valida si el medicamento tiene algún lote próximo a vencer.
    Retorna (es_apto, dias_minimos_en_lote_mas_nuevo).
    
    dias_minimo: días mínimos requeridos para que sea apto para venta
    """
    from .models import LoteMedicamento
    
    lotes = obtener_lotes_fifo(medicamento)
    
    if not lotes.exists():
        return False, 0  # No hay lotes vigentes
    
    # El lote más antiguo (FIFO)
    lote_mas_antiguo = lotes.first()
    dias_faltantes = lote_mas_antiguo.dias_para_vencer()
    
    es_apto = dias_faltantes >= dias_minimo
    return es_apto, dias_faltantes


def obtener_medicamentos_con_alerta():
    """
    Obtiene medicamentos que tienen lotes próximos a vencer (<7 días).
    Useful para dashboard de alertas.
    """
    from .models import Medicamento, LoteMedicamento
    
    hoy = date.today()
    fecha_alerta = hoy + timedelta(days=7)
    
    medicamentos_alerta = Medicamento.objects.filter(
        lotes__fecha_vencimiento__lte=fecha_alerta,
        lotes__fecha_vencimiento__gte=hoy,
        lotes__cantidad_disponible__gt=0
    ).distinct()
    
    return medicamentos_alerta


def obtener_lotes_vencidos():
    """
    Obtiene lotes que ya pasaron su fecha de vencimiento.
    Useful para reportes de descarte.
    """
    from .models import LoteMedicamento
    
    hoy = date.today()
    lotes_vencidos = LoteMedicamento.objects.filter(
        fecha_vencimiento__lt=hoy,
        cantidad_disponible__gt=0
    )
    
    return lotes_vencidos


def procesar_venta_con_fifo(medicamento, cantidad, vendedor, cliente=None):
    """
    Procesa una venta usando el sistema FIFO.
    Actualiza lotes y crea registros de historial.
    
    Retorna:
        (exito, mensaje, venta_ids)
    """
    from .models import Venta, HistorialStock
    from django.db import transaction
    
    lotes_a_usar = obtener_lote_para_venta(medicamento, cantidad)
    
    if not lotes_a_usar:
        return False, "Stock insuficiente con lotes vigentes", []
    
    # Validar vencimiento - generar advertencia pero permitir venta
    es_apto, dias = validar_vencimiento_medicamento(medicamento)
    advertencia = ""
    if not es_apto:
        advertencia = f" ADVERTENCIA: Medicamento próximo a vencer en {dias} días."
    
    venta_ids = []
    
    with transaction.atomic():
        for lote, cantidad_lote in lotes_a_usar:
            # Crear venta
            venta = Venta.objects.create(
                medicamento=medicamento,
                cantidad=cantidad_lote,
                precio=medicamento.precio * cantidad_lote,
                vendedor=vendedor,
                cliente=cliente,
                lote=lote
            )
            venta_ids.append(venta.id)
            
            # Actualizar lote
            lote.cantidad_disponible -= cantidad_lote
            lote.save()
            
            # Actualizar stock medicamento
            medicamento.stock -= cantidad_lote
            medicamento.save()
            
            # Registrar en historial
            HistorialStock.objects.create(
                medicamento=medicamento,
                tipo='VENTA',
                cantidad=cantidad_lote,
                usuario=vendedor,
                stock_anterior=medicamento.stock + cantidad_lote,
                stock_posterior=medicamento.stock,
                motivo=f'Venta FIFO - Lote {lote.numero_lote}'
            )
    
    return True, "Venta procesada exitosamente." + advertencia, venta_ids



