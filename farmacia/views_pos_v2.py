# farmacia/views_pos_v2.py
"""
Vistas para la Terminal POS v2 (mejora del sistema POS actual).
Incluye carrito en BD, boleta, pagos, anulaciones, devoluciones.

Autor: Arquitecto de Software
Fecha: Abril 2026
"""

from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import (
    Medicamento, CarritoVenta, CarritoItem, Boleta, Pago,
    NotaCredito, Venta, HistorialStock, Cliente, Receta
)
from .forms import (
    ProcesarPagoV2Form, AplicarDescuentoForm, SeleccionarClienteV2Form,
    AnularVentaForm, ProcesarDevolucionForm
)
from .utils import (
    generar_numero_venta, generar_numero_boleta, generar_folio_boleta,
    generar_numero_nota_credito, generar_folio_nota_credito,
    calcular_iva, calcular_total_con_iva, validar_stock_carrito,
    calcular_cambio, formato_moneda
)
from .email_utils import enviar_boleta_email
from .receta_control import (
    verificar_receta_antes_de_vender,
    validar_carrito_recetas,
    registrar_venta_con_receta,
)


# =====================================================================
# VISTAS PRINCIPALES DE TERMINAL POS v2
# =====================================================================

@login_required(login_url='inicio_sesion')
def terminal_pos_v2(request):
    """
    Terminal POS v2 - Vista principal.
    Muestra búsqueda de medicamentos y carrito actualizado.
    
    GET: Mostrar búsqueda + carrito
    POST: Buscar medicamento (vía AJAX)
    """
    # Obtener o crear carrito para el vendedor actual
    carrito, created = CarritoVenta.objects.get_or_create(
        vendedor=request.user,
        estado='EN_CONSTRUCCION'
    )
    
    # Recalcular totales siempre
    carrito.calcular_totales()
    
    # Búsqueda de medicamentos
    busqueda = request.GET.get('busqueda', '').strip()
    medicamentos = []
    
    if busqueda:
        medicamentos = Medicamento.objects.filter(
            Q(nombre__icontains=busqueda) |
            Q(sku__icontains=busqueda) |
            Q(laboratorio__icontains=busqueda)
        ).filter(stock__gt=0).order_by('nombre')
    
    context = {
        'carrito': carrito,
        'items': carrito.items.all(),
        'medicamentos': medicamentos,
        'busqueda': busqueda,
        'cantidad_items': carrito.items.count(),
        'total_carrito': carrito.total,
    }
    
    return render(request, 'farmacia/pos_v2/terminal_pos_v2.html', context)


@login_required(login_url='inicio_sesion')
@require_http_methods(["POST"])
def pos_agregar_item(request, medicamento_id):
    """
    AJAX: Agrega medicamento al carrito.
    
    POST params:
        - cantidad: int
    
    Returns:
        JSON con estado de la operación
    """
    try:
        medicamento = get_object_or_404(Medicamento, pk=medicamento_id)
        cantidad = int(request.POST.get('cantidad', 1))
        
        # Validar cantidad
        if cantidad <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Cantidad debe ser mayor a 0'
            }, status=400)
        
        if cantidad > medicamento.stock:
            return JsonResponse({
                'success': False,
                'error': f'Stock insuficiente. Disponible: {medicamento.stock}'
            }, status=400)

        # --- Validación backend OBLIGATORIA de receta ---
        receta = None
        if medicamento.requiere_receta():
            receta_id = request.POST.get('receta_id')
            if not receta_id:
                from .receta_control import registrar_venta_bloqueada
                registrar_venta_bloqueada(medicamento, request.user, request)
                return JsonResponse({
                    'success': False,
                    'requiere_receta': True,
                    'tipo_receta': medicamento.tipo_venta,
                    'error': (
                        f'"{medicamento.nombre}" requiere receta médica '
                        f'({medicamento.get_tipo_venta_display()}). '
                        f'Registre la receta antes de agregar el producto.'
                    )
                }, status=400)
            try:
                receta = Receta.objects.get(pk=receta_id)
                verificar_receta_antes_de_vender(medicamento, receta, request.user, request)
            except Receta.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Receta no encontrada.'}, status=400)
            except Exception as exc:
                return JsonResponse({'success': False, 'error': str(exc)}, status=400)

        # Obtener carrito
        carrito, _ = CarritoVenta.objects.get_or_create(
            vendedor=request.user,
            estado='EN_CONSTRUCCION'
        )

        # Agregar item con receta si corresponde
        item, created = CarritoItem.objects.get_or_create(
            carrito=carrito,
            medicamento=medicamento,
            defaults={
                'cantidad': cantidad,
                'precio_unitario': medicamento.precio,
                'receta': receta,
            }
        )
        if not created:
            item.cantidad += cantidad
            if receta:
                item.receta = receta
            item.save()
        carrito.calcular_totales()

        return JsonResponse({
            'success': True,
            'message': f'✅ {medicamento.nombre} agregado al carrito',
            'carrito_items': carrito.items.count(),
            'carrito_total': str(carrito.total),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url='inicio_sesion')
@require_http_methods(["POST"])
def pos_agregar_por_codigo_barras(request):
    """
    AJAX: Busca medicamento por código de barras (SKU) y lo agrega al carrito.
    Usado para lector de código de barras/escáner.
    
    POST params:
        - codigo_barras: str (SKU del medicamento)
        - cantidad: int (default: 1)
    
    Returns:
        JSON con estado de la operación
    """
    try:
        codigo = request.POST.get('codigo_barras', '').strip()
        cantidad = int(request.POST.get('cantidad', 1))
        
        if not codigo:
            return JsonResponse({
                'success': False,
                'error': 'Código de barras requerido'
            }, status=400)
        
        # Buscar medicamento por SKU o código
        medicamento = Medicamento.objects.filter(
            Q(sku=codigo) | Q(nombre__icontains=codigo)
        ).filter(stock__gt=0).first()
        
        if not medicamento:
            return JsonResponse({
                'success': False,
                'error': f'❌ Medicamento con código "{codigo}" no encontrado o sin stock'
            }, status=404)
        
        if cantidad <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Cantidad debe ser mayor a 0'
            }, status=400)
        
        if cantidad > medicamento.stock:
            return JsonResponse({
                'success': False,
                'error': f'Stock insuficiente. Disponible: {medicamento.stock}'
            }, status=400)

        # --- Validación backend de receta ---
        receta = None
        if medicamento.requiere_receta():
            receta_id = request.POST.get('receta_id')
            if not receta_id:
                from .receta_control import registrar_venta_bloqueada
                registrar_venta_bloqueada(medicamento, request.user, request)
                return JsonResponse({
                    'success': False,
                    'requiere_receta': True,
                    'tipo_receta': medicamento.tipo_venta,
                    'error': (
                        f'"{medicamento.nombre}" requiere receta médica '
                        f'({medicamento.get_tipo_venta_display()}). '
                        f'Registre la receta primero.'
                    )
                }, status=400)
            try:
                receta = Receta.objects.get(pk=receta_id)
                verificar_receta_antes_de_vender(medicamento, receta, request.user, request)
            except Receta.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Receta no encontrada.'}, status=400)
            except Exception as exc:
                return JsonResponse({'success': False, 'error': str(exc)}, status=400)

        # Obtener carrito
        carrito, _ = CarritoVenta.objects.get_or_create(
            vendedor=request.user,
            estado='EN_CONSTRUCCION'
        )

        # Agregar item con receta si corresponde
        item, created = CarritoItem.objects.get_or_create(
            carrito=carrito,
            medicamento=medicamento,
            defaults={
                'cantidad': cantidad,
                'precio_unitario': medicamento.precio,
                'receta': receta,
            }
        )
        if not created:
            item.cantidad += cantidad
            if receta:
                item.receta = receta
            item.save()
        carrito.calcular_totales()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ {medicamento.nombre} x{cantidad} agregado',
            'producto': {
                'nombre': medicamento.nombre,
                'cantidad': cantidad,
                'precio': str(medicamento.precio),
                'stock_restante': medicamento.stock - cantidad,
            },
            'carrito_items': carrito.items.count(),
            'carrito_total': str(carrito.total),
        })
    
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Cantidad debe ser un número'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required(login_url='inicio_sesion')
@require_http_methods(["POST"])
def pos_eliminar_item(request, medicamento_id):
    """
    AJAX: Elimina medicamento del carrito.
    
    Returns:
        JSON con estado actualizado del carrito
    """
    try:
        carrito = CarritoVenta.objects.get(
            vendedor=request.user,
            estado='EN_CONSTRUCCION'
        )
        
        carrito.eliminar_item(medicamento_id)
        
        return JsonResponse({
            'success': True,
            'carrito_items': carrito.items.count(),
            'carrito_total': str(carrito.total),
        })
    
    except CarritoVenta.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Carrito no encontrado'
        }, status=404)


@login_required(login_url='inicio_sesion')
@require_http_methods(["POST"])
def pos_vaciar_carrito(request):
    """AJAX: Limpia el carrito completo"""
    try:
        carrito = CarritoVenta.objects.get(
            vendedor=request.user,
            estado='EN_CONSTRUCCION'
        )
        
        carrito.vaciar_carrito()
        
        return JsonResponse({
            'success': True,
            'carrito_items': 0,
            'carrito_total': '0',
        })
    
    except CarritoVenta.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Carrito no encontrado'
        }, status=404)


# =====================================================================
# VISTAS DE DESCUENTOS
# =====================================================================

@login_required(login_url='inicio_sesion')
def pos_aplicar_descuento(request):
    """
    Aplica descuento al carrito.
    
    GET: Mostrar formulario
    POST: Aplicar descuento
    """
    carrito = get_object_or_404(
        CarritoVenta,
        vendedor=request.user,
        estado='EN_CONSTRUCCION'
    )
    
    if request.method == 'POST':
        form = AplicarDescuentoForm(request.POST)
        
        if form.is_valid():
            tipo = form.cleaned_data['tipo_descuento']
            valor = form.cleaned_data['valor']
            
            if tipo == 'PORCENTAJE':
                carrito.aplicar_descuento(porcentaje=valor)
            else:  # MONTO
                carrito.aplicar_descuento(monto=valor)
            
            messages.success(request, '✅ Descuento aplicado')
            return redirect('pos_procesar_pago')
    else:
        form = AplicarDescuentoForm()
    
    context = {
        'form': form,
        'carrito': carrito,
    }
    
    return render(request, 'farmacia/pos_v2/aplicar_descuento.html', context)


# =====================================================================
# VISTAS DE CLIENTE
# =====================================================================

@login_required(login_url='inicio_sesion')
def pos_seleccionar_cliente(request):
    """
    Selecciona cliente para la venta (opcional).
    
    GET: Mostrar formulario
    POST: Guardar cliente
    """
    carrito = get_object_or_404(
        CarritoVenta,
        vendedor=request.user,
        estado='EN_CONSTRUCCION'
    )
    
    if request.method == 'POST':
        form = SeleccionarClienteV2Form(request.POST)
        
        if form.is_valid():
            cliente = form.cleaned_data.get('cliente')
            
            if cliente:
                carrito.cliente = cliente
                carrito.save()
                messages.success(request, f'✅ Cliente {cliente.nombre} seleccionado')
            else:
                carrito.cliente = None
                carrito.save()
                messages.info(request, 'Venta sin cliente')
            
            return redirect('pos_procesar_pago')
    else:
        form = SeleccionarClienteV2Form()
    
    context = {
        'form': form,
        'carrito': carrito,
    }
    
    return render(request, 'farmacia/pos_v2/seleccionar_cliente_v2.html', context)


# =====================================================================
# VISTAS DE PAGO Y COMPLETACIÓN
# =====================================================================

@login_required(login_url='inicio_sesion')
def pos_procesar_pago(request):
    """
    Procesa el pago de la venta.
    
    GET: Mostrar formulario de pago
    POST: Procesar pago y crear venta
    """
    carrito = get_object_or_404(
        CarritoVenta,
        vendedor=request.user,
        estado='EN_CONSTRUCCION'
    )
    
    # Validar que hay items
    if not carrito.items.exists():
        messages.error(request, 'El carrito está vacío')
        return redirect('terminal_pos_v2')
    
    # Validar stock
    es_valido, mensajes_error = validar_stock_carrito(carrito)
    if not es_valido:
        for msg in mensajes_error:
            messages.error(request, msg)
        return redirect('terminal_pos_v2')

    # --- Validación backend obligatoria de recetas ---
    errores_receta = validar_carrito_recetas(carrito)
    if errores_receta:
        for err in errores_receta:
            messages.error(request, f'Receta requerida: {err}')
        return redirect('terminal_pos_v2')
    
    if request.method == 'POST':
        form = ProcesarPagoV2Form(request.POST)
        
        if form.is_valid():
            # Procesar venta en transacción atómica
            try:
                with transaction.atomic():
                    # 1. Generar números
                    numero_venta = generar_numero_venta()
                    numero_boleta = generar_numero_boleta()
                    folio = generar_folio_boleta()
                    
                    # 2. Crear boleta
                    boleta = Boleta.objects.create(
                        numero_boleta=numero_boleta,
                        folio=folio,
                        carrito=carrito,
                        rut_farmacia='12.345.678-9',  # TODO: Configurar
                        nombre_farmacia='FARMACIA COLLICO',
                        direccion_farmacia='Collico, Región del Biobío',
                        cliente_rut=carrito.cliente.rut_dni if carrito.cliente else None,
                        cliente_nombre=f"{carrito.cliente.nombre} {carrito.cliente.apellido}" if carrito.cliente else None,
                        subtotal=carrito.subtotal,
                        descuento=carrito.descuento_monto,
                        base_imponible=carrito.base_imponible,
                        iva=carrito.iva,
                        total=carrito.total,
                        metodo_pago=form.cleaned_data['metodo_pago'],
                        referencia_pago=form.cleaned_data.get('referencia_pago', ''),
                        vendedor=request.user,
                    )
                    
                    # 3. Crear pago
                    pago = Pago.objects.create(
                        boleta=boleta,
                        carrito=carrito,
                        metodo_pago=form.cleaned_data['metodo_pago'],
                        monto=form.cleaned_data['monto_pagado'],
                        cambio=calcular_cambio(carrito.total, form.cleaned_data['monto_pagado']),
                        referencia=form.cleaned_data.get('referencia_pago', ''),
                    )
                    
                    # 4. Crear venta principal (primera línea del carrito)
                    primer_item = carrito.items.select_related('receta').first()
                    venta_principal = Venta.objects.create(
                        medicamento=primer_item.medicamento,
                        cantidad=primer_item.cantidad,
                        precio=carrito.total,  # Total de la venta
                        vendedor=request.user,
                        cliente=carrito.cliente,
                        numero_venta=numero_venta,
                        estado='COMPLETADA',
                        boleta=boleta,
                        receta_venta=primer_item.receta,
                    )

                    # 4b. Auditoría de recetas por cada ítem que la requiera
                    for item in carrito.items.select_related('medicamento', 'receta').all():
                        if item.receta:
                            registrar_venta_con_receta(
                                venta_principal, item.receta,
                                request.user, request
                            )
                    
                    # 5. Descontar stock y registrar historial
                    for item in carrito.items.all():
                        med = item.medicamento
                        med.stock -= item.cantidad
                        med.save()
                        
                        HistorialStock.objects.create(
                            medicamento=med,
                            tipo='VENTA',
                            cantidad=item.cantidad,
                            usuario=request.user,
                            stock_anterior=med.stock + item.cantidad,
                            stock_posterior=med.stock,
                            venta=venta_principal,
                            motivo=f'Venta POS v2 - {form.cleaned_data["metodo_pago"]}'
                        )
                    
                    # 6. Marcar carrito como completado
                    carrito.estado = 'COMPLETADO'
                    carrito.fecha_completacion = timezone.now()
                    carrito.save()
                    
                    # 7. Guardar en sesión para mostrar
                    request.session['ultima_boleta_id'] = boleta.id
                    request.session['ultima_venta_id'] = venta_principal.id
                    
                    # 8. Enviar boleta por email si el cliente tiene email
                    if carrito.cliente and carrito.cliente.email:
                        resultado_email = enviar_boleta_email(boleta, carrito.cliente.email)
                        if resultado_email['success']:
                            messages.info(request, f"📧 {resultado_email['message']}")
                        else:
                            messages.warning(request, f"⚠️ {resultado_email['message']}")
                    
                    messages.success(request, f'✅ Venta completada: {numero_venta}')
                    return redirect('pos_mostrar_boleta')
            
            except Exception as e:
                messages.error(request, f'❌ Error al procesar venta: {str(e)}')
                return redirect('pos_procesar_pago')
    else:
        form = ProcesarPagoV2Form(initial={
            'metodo_pago': 'EFECTIVO',
            'monto_pagado': carrito.total
        })
    
    context = {
        'form': form,
        'carrito': carrito,
        'total_a_pagar': carrito.total,
    }
    
    return render(request, 'farmacia/pos_v2/procesar_pago_v2.html', context)


@login_required(login_url='inicio_sesion')
def pos_mostrar_boleta(request, boleta_id=None):
    """
    Muestra la boleta de la última venta.
    Puede recibir boleta_id como parámetro de URL o desde sesión.
    Permite imprimir, descargar PDF, email, nueva venta.
    """
    # Si no hay boleta_id, intentar obtenerla de la sesión
    if not boleta_id:
        boleta_id = request.session.get('ultima_boleta_id')
    
    if not boleta_id:
        messages.warning(request, 'No hay boleta para mostrar')
        return redirect('terminal_pos_v2')
    
    boleta = get_object_or_404(Boleta, pk=boleta_id)
    carrito = boleta.carrito
    
    context = {
        'boleta': boleta,
        'carrito': carrito,
        'items': carrito.items.all(),
        'pago': boleta.pago,
    }
    
    return render(request, 'farmacia/pos_v2/boleta.html', context)


# =====================================================================
# VISTAS DE ANULACIÓN Y DEVOLUCIONES
# =====================================================================

@login_required(login_url='inicio_sesion')
def pos_anular_venta(request, numero_venta):
    """
    Anula una venta completada.
    Solo usuarios con permiso pueden hacer esto.
    
    POST: Procesar anulación
    """
    venta = get_object_or_404(Venta, numero_venta=numero_venta)
    
    # Validar permisos (solo staff)
    if not request.user.is_staff:
        messages.error(request, '❌ Solo supervisores pueden anular ventas')
        return redirect('pos_historial_ventas')
    
    if request.method == 'POST':
        form = AnularVentaForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Cambiar estado de venta
                    venta.estado = 'ANULADA'
                    venta.save()
                    
                    # 2. Crear nota de crédito
                    numero_nota = generar_numero_nota_credito()
                    folio = generar_folio_nota_credito()
                    
                    nota = NotaCredito.objects.create(
                        numero_nota=numero_nota,
                        folio=folio,
                        boleta_original=venta.boleta,
                        motivo='ANULACION',
                        observaciones=form.cleaned_data['observaciones'],
                        monto=venta.precio,
                        usuario_registra=request.user,
                        usuario_aprueba=request.user,
                        aprobada=True,
                    )
                    
                    # 3. Revertir stock
                    venta.medicamento.stock += venta.cantidad
                    venta.medicamento.save()
                    
                    # 4. Registrar en historial
                    HistorialStock.objects.create(
                        medicamento=venta.medicamento,
                        tipo='ANULACION',
                        cantidad=-venta.cantidad,  # Negativo para indicar reversión
                        usuario=request.user,
                        stock_anterior=venta.medicamento.stock - venta.cantidad,
                        stock_posterior=venta.medicamento.stock,
                        venta=venta,
                        motivo=f'Anulación {numero_venta} - {form.cleaned_data["motivo"]}'
                    )
                    
                    messages.success(request, f'✅ Venta {numero_venta} anulada. Nota: {numero_nota}')
                    return redirect('pos_historial_ventas')
            
            except Exception as e:
                messages.error(request, f'❌ Error al anular: {str(e)}')
                return redirect('pos_anular_venta', numero_venta=numero_venta)
    else:
        form = AnularVentaForm()
    
    context = {
        'form': form,
        'venta': venta,
    }
    
    return render(request, 'farmacia/pos_v2/anular_venta.html', context)


@login_required(login_url='inicio_sesion')
def pos_procesar_devolucion(request, numero_venta):
    """
    Procesa devolución de medicamento.
    Crea nota de crédito y revierte stock.
    """
    venta = get_object_or_404(Venta, numero_venta=numero_venta)
    
    if request.method == 'POST':
        form = ProcesarDevolucionForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear nota de crédito
                    numero_nota = generar_numero_nota_credito()
                    folio = generar_folio_nota_credito()
                    cantidad = form.cleaned_data['cantidad']
                    
                    nota = NotaCredito.objects.create(
                        numero_nota=numero_nota,
                        folio=folio,
                        boleta_original=venta.boleta,
                        motivo='DEVOLUCION',
                        observaciones=form.cleaned_data['observaciones'],
                        monto=venta.medicamento.precio * cantidad,
                        usuario_registra=request.user,
                        requiere_aprobacion=cantidad > (venta.cantidad // 2),
                    )
                    
                    # 2. Revertir stock
                    venta.medicamento.stock += cantidad
                    venta.medicamento.save()
                    
                    # 3. Registrar en historial
                    HistorialStock.objects.create(
                        medicamento=venta.medicamento,
                        tipo='DEVOLUCION',
                        cantidad=-cantidad,
                        usuario=request.user,
                        stock_anterior=venta.medicamento.stock - cantidad,
                        stock_posterior=venta.medicamento.stock,
                        venta=venta,
                        motivo=f'Devolución {numero_venta} - {form.cleaned_data["motivo"]}'
                    )
                    
                    messages.success(request, f'✅ Devolución procesada. Nota: {numero_nota}')
                    return redirect('pos_historial_ventas')
            
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    else:
        form = ProcesarDevolucionForm()
    
    context = {
        'form': form,
        'venta': venta,
    }
    
    return render(request, 'farmacia/pos_v2/procesar_devolucion.html', context)


# =====================================================================
# VISTAS DE REPORTES Y HISTORIAL
# =====================================================================

@login_required(login_url='inicio_sesion')
def pos_historial_ventas(request):
    """
    Muestra historial de ventas con opciones para anular/devolver.
    """
    # Obtener ventas del usuario actual (o todas si es staff)
    if request.user.is_staff:
        ventas = Venta.objects.all()
    else:
        ventas = Venta.objects.filter(vendedor=request.user)
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        ventas = ventas.filter(estado=estado)
    
    fechadesde = request.GET.get('fecha_desde')
    if fechadesde:
        from django.utils.dateparse import parse_date
        ventas = ventas.filter(fecha__date__gte=parse_date(fechadesde))
    
    ventaspor_pagina = 20
    page = request.GET.get('page', 1)
    
    context = {
        'ventas': ventas.order_by('-fecha'),
        'filtro_estado': estado,
        'filtro_fecha_desde': fechadesde,
    }
    
    return render(request, 'farmacia/pos_v2/historial_ventas.html', context)
