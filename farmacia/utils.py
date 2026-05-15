# farmacia/utils.py
"""
Utilidades para el sistema POS v2 de Farmacia Collico.
Incluye generadores de números, cálculos, etc.
"""

from decimal import Decimal
from datetime import datetime
from django.db.models import Max
from .models import Venta, Boleta, NotaCredito


def generar_numero_venta():
    """
    Genera número único de venta con formato: VT-YYYY-NNNNN
    Ejemplo: VT-2026-00001
    """
    año = datetime.now().year
    
    # Obtener último número de venta del año actual
    ultima_venta = Venta.objects.filter(
        numero_venta__startswith=f'VT-{año}-'
    ).order_by('-numero_venta').first()
    
    if ultima_venta:
        # Extraer número secuencial del último número
        secuencia = int(ultima_venta.numero_venta.split('-')[-1])
        siguiente = secuencia + 1
    else:
        siguiente = 1
    
    # Formatear con 5 dígitos (00001)
    numero = f'VT-{año}-{siguiente:05d}'
    return numero


def generar_numero_boleta():
    """
    Genera número único de boleta con formato: BV-YYYY-NNNNN
    Ejemplo: BV-2026-00001
    """
    año = datetime.now().year
    
    # Obtener última boleta del año actual
    ultima_boleta = Boleta.objects.filter(
        numero_boleta__startswith=f'BV-{año}-'
    ).order_by('-numero_boleta').first()
    
    if ultima_boleta:
        secuencia = int(ultima_boleta.numero_boleta.split('-')[-1])
        siguiente = secuencia + 1
    else:
        siguiente = 1
    
    numero = f'BV-{año}-{siguiente:05d}'
    return numero


def generar_folio_boleta():
    """
    Genera folio secuencial único para boleta.
    Es un número secuencial simple: 1, 2, 3... (requerido por SII)
    """
    # Obtener último folio
    ultima_boleta = Boleta.objects.all().order_by('-folio').first()
    
    if ultima_boleta:
        return ultima_boleta.folio + 1
    else:
        return 1


def generar_numero_nota_credito():
    """
    Genera número único de nota de crédito: NC-YYYY-NNNNN
    Ejemplo: NC-2026-00001
    """
    año = datetime.now().year
    
    # Obtener última nota del año actual
    ultima_nota = NotaCredito.objects.filter(
        numero_nota__startswith=f'NC-{año}-'
    ).order_by('-numero_nota').first()
    
    if ultima_nota:
        secuencia = int(ultima_nota.numero_nota.split('-')[-1])
        siguiente = secuencia + 1
    else:
        siguiente = 1
    
    numero = f'NC-{año}-{siguiente:05d}'
    return numero


def generar_folio_nota_credito():
    """Genera folio secuencial único para nota de crédito"""
    ultima_nota = NotaCredito.objects.all().order_by('-folio').first()
    
    if ultima_nota:
        return ultima_nota.folio + 1
    else:
        return 1


def calcular_iva(monto, porcentaje=19):
    """
    Calcula IVA sobre un monto.
    
    Args:
        monto: Monto base para calcular IVA
        porcentaje: Porcentaje de IVA (default 19% para Chile)
    
    Returns:
        Decimal: Monto de IVA
    """
    return Decimal(monto) * Decimal(porcentaje) / Decimal(100)


def calcular_total_con_iva(monto, porcentaje=19):
    """
    Calcula monto total incluyendo IVA.
    
    Args:
        monto: Monto base
        porcentaje: Porcentaje de IVA (default 19%)
    
    Returns:
        tuple: (base_imponible, iva, total)
    """
    base = Decimal(monto)
    iva = calcular_iva(base, porcentaje)
    total = base + iva
    
    return (base, iva, total)


def aplicar_descuento(monto, descuento_porcentaje=0, descuento_monto=0):
    """
    Aplica descuento a un monto.
    Se puede aplicar porcentaje o monto fijo (no ambos).
    
    Args:
        monto: Monto original
        descuento_porcentaje: Descuento en porcentaje (0-100)
        descuento_monto: Descuento en monto fijo
    
    Returns:
        tuple: (monto_original, descuento_aplicado, monto_final)
    """
    monto = Decimal(monto)
    
    if descuento_porcentaje > 0:
        descuento = monto * Decimal(descuento_porcentaje) / Decimal(100)
    elif descuento_monto > 0:
        descuento = Decimal(descuento_monto)
    else:
        descuento = Decimal(0)
    
    # Validar que descuento no sea mayor al monto
    if descuento > monto:
        descuento = monto
    
    monto_final = monto - descuento
    
    return (monto, descuento, monto_final)


def calcular_cambio(total_venta, monto_pagado):
    """
    Calcula cambio en una venta de efectivo.
    
    Args:
        total_venta: Total a pagar
        monto_pagado: Monto entregado por cliente
    
    Returns:
        Decimal: Cambio (puede ser negativo si monto insuficiente)
    """
    return Decimal(monto_pagado) - Decimal(total_venta)


def validar_stock_carrito(carrito):
    """
    Valida si hay stock disponible para todos los items del carrito.
    
    Args:
        carrito: Instancia de CarritoVenta
    
    Returns:
        tuple: (es_valido, mensajes)
    """
    mensajes = []
    
    for item in carrito.items.all():
        if item.cantidad > item.medicamento.stock:
            mensajes.append(
                f"Stock insuficiente de {item.medicamento.nombre}. "
                f"Disponible: {item.medicamento.stock}, Solicitado: {item.cantidad}"
            )
    
    return (len(mensajes) == 0, mensajes)


def redondear_moneda(monto, decimales=0):
    """
    Redondea un monto a moneda chilena (sin decimales).
    
    Args:
        monto: Monto a redondear
        decimales: Decimales (default 0 para CLP)
    
    Returns:
        Decimal: Monto redondeado
    """
    if decimales == 0:
        # Redondear a 10 más cercano (standard CLP)
        monto = Decimal(monto)
        return (monto / 10).quantize(Decimal('1')) * 10
    else:
        return Decimal(monto).quantize(Decimal(10) ** -decimales)


def formato_moneda(monto):
    """
    Formatea monto como moneda chilena.
    Ejemplo: 1500000 → "$1.500.000"
    
    Args:
        monto: Monto a formatear
    
    Returns:
        str: Monto formateado
    """
    monto = int(monto)
    return f"${monto:,}".replace(",", ".")


def generar_resumen_carrito(carrito):
    """
    Genera resumen legible de un carrito.
    Usado para mostrar en boleta o email.
    
    Args:
        carrito: Instancia de CarritoVenta
    
    Returns:
        dict: Datos formateados
    """
    return {
        'numero_items': carrito.items.count(),
        'subtotal': formato_moneda(carrito.subtotal),
        'descuento': formato_moneda(carrito.descuento_monto),
        'base_imponible': formato_moneda(carrito.base_imponible),
        'iva': formato_moneda(carrito.iva),
        'total': formato_moneda(carrito.total),
        'items': [
            {
                'nombre': item.medicamento.nombre,
                'cantidad': item.cantidad,
                'precio_unitario': formato_moneda(item.precio_unitario),
                'subtotal': formato_moneda(item.subtotal),
            }
            for item in carrito.items.all()
        ]
    }
