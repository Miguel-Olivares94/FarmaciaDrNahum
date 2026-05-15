# farmacia/email_sender.py
"""
Módulo para enviar emails con boletas a clientes.
"""

from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from .pdf_generator import generar_pdf_boleta


def enviar_boleta_email(boleta, email_destinatario):
    """
    Envía boleta por email a cliente.
    
    Args:
        boleta: Instancia de Boleta
        email_destinatario: Email del cliente
    
    Returns:
        bool: True si se envió correctamente
    """
    try:
        # Generar PDF
        pdf_buffer = generar_pdf_boleta(boleta)
        
        # Contexto para template
        contexto = {
            'numero_boleta': boleta.numero_boleta,
            'cliente_nombre': boleta.cliente_nombre or 'Consumidor Final',
            'total': f"${int(boleta.total):,}".replace(',', '.'),
            'fecha': boleta.fecha_emision.strftime('%d/%m/%Y %H:%M'),
            'farmacia': 'FARMACIA DR. NAHUM',
        }
        
        # Renderizar HTML del email
        html_message = render_to_string('farmacia/email/boleta_email.html', contexto)
        
        # Crear email
        email = EmailMessage(
            subject=f'Boleta {boleta.numero_boleta} - Farmacia Dr. Nahum',
            body=f'Adjunto encontrará su boleta #{boleta.numero_boleta}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destinatario],
            html_message=html_message,
        )
        
        # Adjuntar PDF
        email.attach(
            f'boleta_{boleta.numero_boleta}.pdf',
            pdf_buffer.getvalue(),
            'application/pdf'
        )
        
        # Enviar
        email.send(fail_silently=False)
        
        # Registrar en modelo
        boleta.email_enviado = True
        boleta.email_destinatario = email_destinatario
        boleta.save(update_fields=['email_enviado', 'email_destinatario'])
        
        return True
        
    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False


def enviar_boleta_reenvio(numero_boleta, email_destinatario):
    """
    Reenvía boleta existente por email.
    
    Args:
        numero_boleta: Número de boleta (ej: BV-2026-00001)
        email_destinatario: Email destino
    
    Returns:
        bool: Éxito
    """
    from .models import Boleta
    
    try:
        boleta = Boleta.objects.get(numero_boleta=numero_boleta)
        return enviar_boleta_email(boleta, email_destinatario)
    except Boleta.DoesNotExist:
        return False


def enviar_boleta_descarga(boleta, usuario_email):
    """
    Notifica a usuario sobre su boleta generada.
    
    Args:
        boleta: Instancia de Boleta
        usuario_email: Email del usuario
    
    Returns:
        bool: Éxito
    """
    try:
        email = EmailMessage(
            subject=f'Su Boleta {boleta.numero_boleta} está lista',
            body=f'La boleta {boleta.numero_boleta} se ha generado correctamente en el sistema.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[usuario_email],
        )
        
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        print(f"Error en notificación: {str(e)}")
        return False


def test_email_connection():
    """
    Prueba la conexión de email.
    Útil para debugging.
    
    Returns:
        bool: True si funciona
    """
    try:
        from django.core.mail import get_connection
        connection = get_connection()
        connection.open()
        connection.close()
        return True
    except Exception as e:
        print(f"Error en conexión email: {str(e)}")
        return False
