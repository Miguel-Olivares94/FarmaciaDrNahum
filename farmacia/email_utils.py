"""
Utilidades para envío de emails de boletas y notificaciones
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def enviar_boleta_email(boleta, destinatario_email=None):
    """
    Envía la boleta por email al cliente.
    
    Args:
        boleta (Boleta): Instancia de la boleta a enviar
        destinatario_email (str): Email del destinatario (opcional, usa cliente.email)
    
    Returns:
        dict: {success: bool, message: str}
    """
    try:
        # Obtener email
        if not destinatario_email:
            if boleta.cliente_nombre and boleta.carrito.cliente:
                destinatario_email = boleta.carrito.cliente.email
        
        # Si no hay email, retornar sin error
        if not destinatario_email:
            return {
                'success': False,
                'message': 'Cliente no tiene email registrado'
            }
        
        # Preparar contexto para template
        context = {
            'boleta': boleta,
            'carrito': boleta.carrito,
            'items': boleta.carrito.items.all(),
            'pago': boleta.pago,
            'farmacia_nombre': 'Farmacia Dr. Nahum',
            'farmacia_telefono': '+56 9 1234 5678',
            'farmacia_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Renderizar template HTML
        html_message = render_to_string('farmacia/emails/boleta_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Crear email con alternativa HTML
        email = EmailMultiAlternatives(
            subject=f'Boleta #{boleta.numero_boleta} - Farmacia Dr. Nahum',
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario_email],
        )
        email.attach_alternative(html_message, 'text/html')
        
        # Enviar
        email.send(fail_silently=False)
        
        logger.info(f'Boleta #{boleta.numero_boleta} enviada a {destinatario_email}')
        return {
            'success': True,
            'message': f'Boleta enviada a {destinatario_email}'
        }
    
    except Exception as e:
        logger.error(f'Error al enviar boleta #{boleta.numero_boleta}: {str(e)}')
        return {
            'success': False,
            'message': f'Error al enviar email: {str(e)}'
        }


def enviar_confirmacion_venta(venta, email_cliente):
    """
    Envía confirmación de venta al cliente
    
    Args:
        venta (Venta): Instancia de la venta
        email_cliente (str): Email del cliente
    
    Returns:
        dict: {success: bool, message: str}
    """
    try:
        context = {
            'venta': venta,
            'medicamento': venta.medicamento,
            'cantidad': venta.cantidad,
            'precio': venta.precio,
            'farmacia_nombre': 'Farmacia Dr. Nahum',
        }
        
        html_message = render_to_string('farmacia/emails/confirmacion_venta.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=f'Confirmación de Compra - {venta.numero_venta}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_cliente],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f'Confirmación de venta {venta.numero_venta} enviada a {email_cliente}')
        return {
            'success': True,
            'message': f'Confirmación enviada a {email_cliente}'
        }
    
    except Exception as e:
        logger.error(f'Error al enviar confirmación de venta: {str(e)}')
        return {
            'success': False,
            'message': f'Error al enviar email: {str(e)}'
        }


def enviar_alerta_stock_bajo(medicamento, email_farmacista):
    """
    Envía alerta de stock bajo al farmacista
    
    Args:
        medicamento (Medicamento): Medicamento con stock bajo
        email_farmacista (str): Email del farmacista
    
    Returns:
        dict: {success: bool, message: str}
    """
    try:
        context = {
            'medicamento': medicamento,
            'stock_actual': medicamento.stock,
            'farmacia': 'Farmacia Dr. Nahum',
        }
        
        subject = f'⚠️ ALERTA: Stock bajo de {medicamento.nombre}'
        message = (
            f'El medicamento {medicamento.nombre} tiene stock bajo.\n'
            f'Stock actual: {medicamento.stock} unidades\n'
            f'Se recomienda hacer un pedido al proveedor.'
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_farmacista],
            fail_silently=False,
        )
        
        logger.warning(f'Alerta de stock bajo enviada para {medicamento.nombre}')
        return {
            'success': True,
            'message': f'Alerta enviada a {email_farmacista}'
        }
    
    except Exception as e:
        logger.error(f'Error al enviar alerta de stock: {str(e)}')
        return {
            'success': False,
            'message': f'Error al enviar email: {str(e)}'
        }
