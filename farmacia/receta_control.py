"""
farmacia/receta_control.py
==========================
Lógica de negocio para el control de medicamentos con receta.

Responsabilidades:
  - Validar si un carrito/ítem puede venderse sin receta
  - Obtener la IP real del request (para auditoría)
  - Registrar eventos en AuditoriaReceta
  - Verificar vigencia y archivos requeridos
"""
from datetime import date
from django.core.exceptions import ValidationError
from django.utils import timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request):
    """Extrae la IP real del cliente, considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _registrar_auditoria(evento, usuario, request=None, receta=None, medicamento=None, detalle=''):
    """Crea un registro en AuditoriaReceta de forma segura (no lanza excepciones)."""
    from .models import AuditoriaReceta
    try:
        AuditoriaReceta.objects.create(
            evento=evento,
            usuario=usuario,
            receta=receta,
            medicamento=medicamento,
            detalle=detalle,
            ip_address=_get_client_ip(request) if request else None,
        )
    except Exception:
        pass  # La auditoría nunca debe romper el flujo principal


# ---------------------------------------------------------------------------
# Validación de ítems individuales
# ---------------------------------------------------------------------------

def validar_item_requiere_receta(medicamento, receta=None):
    """
    Valida si un medicamento puede agregarse al carrito.

    Reglas:
      - libre            → siempre OK
      - receta_simple    → necesita receta vigente
      - receta_retenida  → necesita receta vigente + archivo (recomendado)
      - controlado       → necesita receta vigente + archivo obligatorio

    Lanza ValidationError si hay algún problema.
    Retorna True si todo está bien.
    """
    from .models import Medicamento

    if not medicamento.requiere_receta():
        return True

    if receta is None:
        raise ValidationError(
            f'"{medicamento.nombre}" requiere receta médica. '
            f'Tipo: {medicamento.get_tipo_venta_display()}.'
        )

    # Verificar vigencia
    if not receta.esta_vigente():
        raise ValidationError(
            f'La receta presentada está vencida '
            f'(emitida: {receta.fecha_emision.strftime("%d/%m/%Y")}).'
        )

    # Para controlados: archivo obligatorio
    if medicamento.tipo_venta == Medicamento.TIPO_VENTA_CONTROLADO:
        if not receta.archivo_receta:
            raise ValidationError(
                f'Los medicamentos controlados requieren digitalización '
                f'(imagen/PDF) de la receta.'
            )

    return True


# ---------------------------------------------------------------------------
# Validación completa del carrito antes de confirmar venta
# ---------------------------------------------------------------------------

def validar_carrito_recetas(carrito):
    """
    Recorre todos los ítems del carrito y verifica que cada medicamento
    que requiere receta tenga una receta válida adjunta.

    Retorna lista de errores. Lista vacía = todo OK.
    """
    errores = []
    for item in carrito.items.select_related('medicamento', 'receta').all():
        med = item.medicamento
        if not med.requiere_receta():
            continue
        try:
            validar_item_requiere_receta(med, item.receta)
        except ValidationError as e:
            errores.append(f'{med.nombre}: {e.message}')
    return errores


# ---------------------------------------------------------------------------
# Registro de evento al intentar vender sin receta (bloqueo)
# ---------------------------------------------------------------------------

def registrar_venta_bloqueada(medicamento, usuario, request=None):
    """
    Registra en auditoría el intento fallido de vender sin receta.
    Llamar cuando se rechaza agregar un ítem al carrito.
    """
    from .models import AuditoriaReceta
    _registrar_auditoria(
        evento=AuditoriaReceta.EVENTO_VENTA_BLOQUEADA,
        usuario=usuario,
        request=request,
        medicamento=medicamento,
        detalle=f'Intento de venta de "{medicamento.nombre}" sin receta válida.',
    )


# ---------------------------------------------------------------------------
# Registro de venta completada con receta
# ---------------------------------------------------------------------------

def registrar_venta_con_receta(venta, receta, usuario, request=None):
    """
    Registra que una venta fue completada con receta.
    Si la receta debe retenerse, también registra ese evento.
    """
    from .models import AuditoriaReceta
    _registrar_auditoria(
        evento=AuditoriaReceta.EVENTO_VENTA_CON_RECETA,
        usuario=usuario,
        request=request,
        receta=receta,
        medicamento=venta.medicamento,
        detalle=f'Venta #{venta.numero_venta} autorizada con receta #{receta.id}.',
    )
    if receta.debe_retenerse():
        _registrar_auditoria(
            evento=AuditoriaReceta.EVENTO_RECETA_RETENIDA,
            usuario=usuario,
            request=request,
            receta=receta,
            medicamento=venta.medicamento,
            detalle=f'Receta #{receta.id} ({receta.get_tipo_display()}) retenida físicamente.',
        )


# ---------------------------------------------------------------------------
# Registro de receta verificada / rechazada
# ---------------------------------------------------------------------------

def registrar_verificacion_receta(receta, usuario, aprobada: bool, motivo='', request=None):
    """
    Registra la verificación o rechazo de una receta por parte de un farmacéutico.
    También actualiza el estado de la receta.
    """
    from .models import AuditoriaReceta, Receta
    if aprobada:
        receta.estado = Receta.ESTADO_VERIFICADA
        receta.verificada_por = usuario
        receta.fecha_verificacion = timezone.now()
        receta.save(update_fields=['estado', 'verificada_por', 'fecha_verificacion'])
        _registrar_auditoria(
            evento=AuditoriaReceta.EVENTO_RECETA_VERIFICADA,
            usuario=usuario,
            request=request,
            receta=receta,
            detalle=f'Receta #{receta.id} verificada y aprobada.',
        )
    else:
        receta.estado = Receta.ESTADO_RECHAZADA
        receta.motivo_rechazo = motivo
        receta.verificada_por = usuario
        receta.fecha_verificacion = timezone.now()
        receta.save(update_fields=['estado', 'motivo_rechazo', 'verificada_por', 'fecha_verificacion'])
        _registrar_auditoria(
            evento=AuditoriaReceta.EVENTO_RECETA_RECHAZADA,
            usuario=usuario,
            request=request,
            receta=receta,
            detalle=f'Receta #{receta.id} rechazada. Motivo: {motivo}',
        )


# ---------------------------------------------------------------------------
# Verificación de seguridad en backend (usar en TODAS las vistas de venta)
# ---------------------------------------------------------------------------

def verificar_receta_antes_de_vender(medicamento, receta, usuario, request=None):
    """
    Punto único de validación backend obligatoria.
    Llamar siempre antes de procesar una venta.

    - Si el medicamento no requiere receta → pasa sin problema.
    - Si requiere receta y no hay una válida → registra bloqueo y lanza ValidationError.

    Nunca confiar sólo en el frontend.
    """
    if not medicamento.requiere_receta():
        return True

    try:
        validar_item_requiere_receta(medicamento, receta)
    except ValidationError:
        registrar_venta_bloqueada(medicamento, usuario, request)
        raise

    return True
