# farmacia/pdf_generator.py
"""
Generador de PDF para boletas y reportes.
Utiliza reportlab para crear PDFs profesionales.
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
from decimal import Decimal


def generar_pdf_boleta(boleta):
    """
    Genera PDF de boleta/factura.
    
    Args:
        boleta: Instancia de Boleta
    
    Returns:
        BytesIO: Buffer con contenido PDF
    """
    buffer = BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(3*inch, 8*inch),  # 80mm x 200mm (tamaño boleta térmica)
        rightMargin=0.2*inch,
        leftMargin=0.2*inch,
        topMargin=0.2*inch,
        bottomMargin=0.2*inch,
    )
    
    # Story de elementos
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Heading1'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=2,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
        spaceAfter=1,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.black,
        spaceAfter=1,
        fontName='Helvetica'
    )
    
    # === HEADER ===
    story.append(Paragraph("FARMACIA COLLICO", titulo_style))
    story.append(Paragraph(f"RUT: {boleta.rut_farmacia}", header_style))
    story.append(Paragraph(boleta.direccion_farmacia, header_style))
    story.append(Spacer(1, 0.1*inch))
    
    # === NÚMERO BOLETA ===
    boleta_header_data = [
        ['BOLETA'],
        [boleta.numero_boleta],
        [f'FOLIO: {boleta.folio}']
    ]
    boleta_table = Table(boleta_header_data, colWidths=[2.6*inch])
    boleta_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 10),
        ('FONTSIZE', (0, 1), (0, 1), 12),
        ('FONTSIZE', (0, 2), (0, 2), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(boleta_table)
    story.append(Spacer(1, 0.05*inch))
    
    # === INFORMACIÓN GENERAL ===
    info_data = [
        ['Fecha:', datetime.now().strftime('%d/%m/%Y %H:%M')],
    ]
    
    if boleta.cliente_nombre:
        info_data.append(['Cliente:', boleta.cliente_nombre])
        if boleta.cliente_rut:
            info_data.append(['RUT:', boleta.cliente_rut])
    else:
        info_data.append(['Cliente:', 'CONSUMIDOR FINAL'])
    
    info_data.append(['Vendedor:', f"{boleta.vendedor.first_name} {boleta.vendedor.last_name}"])
    
    info_table = Table(info_data, colWidths=[0.8*inch, 1.8*inch])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.1*inch))
    
    # === DETALLE DE ITEMS ===
    items_data = [['DESCRIP', 'QTY', 'PRECIO']]
    
    for item in boleta.carrito.items.all():
        items_data.append([
            item.medicamento.nombre[:25],  # Truncar nombre largo
            str(item.cantidad),
            f"${int(item.subtotal):,}".replace(',', '.'),
        ])
    
    items_table = Table(items_data, colWidths=[1.4*inch, 0.6*inch, 0.6*inch])
    items_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.05*inch))
    
    # === TOTALES ===
    totales_data = [
        ['SUBTOTAL:', f"${int(boleta.subtotal):,}".replace(',', '.')],
    ]
    
    if boleta.descuento > 0:
        totales_data.append([f'DESCUENTO:', f"-${int(boleta.descuento):,}".replace(',', '.')])
    
    totales_data.extend([
        ['BASE IMP:', f"${int(boleta.base_imponible):,}".replace(',', '.')],
        ['IVA 19%:', f"${int(boleta.iva):,}".replace(',', '.')],
    ])
    
    totales_table = Table(totales_data, colWidths=[1.3*inch, 1.3*inch])
    totales_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ]))
    story.append(totales_table)
    story.append(Spacer(1, 0.05*inch))
    
    # === TOTAL FINAL ===
    total_data = [
        ['TOTAL', f"${int(boleta.total):,}".replace(',', '.')],
    ]
    total_table = Table(total_data, colWidths=[1.3*inch, 1.3*inch])
    total_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.05*inch))
    
    # === MÉTODO DE PAGO ===
    pago_data = [
        [f'PAGO: {boleta.metodo_pago}'],
    ]
    if boleta.referencia_pago:
        pago_data.append([f'REF: {boleta.referencia_pago}'])
    
    pago_table = Table(pago_data, colWidths=[2.6*inch])
    pago_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(pago_table)
    story.append(Spacer(1, 0.1*inch))
    
    # === FOOTER ===
    story.append(Paragraph("GRACIAS POR SU COMPRA", header_style))
    story.append(Paragraph("Validación SII: www.sii.cl", header_style))
    story.append(Paragraph("Documento emitido con sistema certificado", header_style))
    
    # Construir PDF
    doc.build(story)
    
    # Retornar buffer
    buffer.seek(0)
    return buffer


def generar_pdf_reporte_ventas(ventas, titulo="Reporte de Ventas"):
    """
    Genera PDF con reporte de ventas.
    
    Args:
        ventas: QuerySet de Ventas
        titulo: Título del reporte
    
    Returns:
        BytesIO: Buffer con PDF
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'TituloReport',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    
    # Título
    story.append(Paragraph(titulo, titulo_style))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Tabla de ventas
    data = [['Número', 'Medicamento', 'Cantidad', 'Precio', 'Fecha', 'Estado']]
    
    total_ventas = Decimal('0.00')
    for venta in ventas:
        data.append([
            venta.numero_venta,
            venta.medicamento.nombre[:30],
            str(venta.cantidad),
            f"${int(venta.precio):,}".replace(',', '.'),
            venta.fecha.strftime('%d/%m/%Y'),
            venta.estado,
        ])
        total_ventas += venta.precio
    
    table = Table(data, colWidths=[1.2*inch, 2*inch, 1*inch, 1.2*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Total
    story.append(Paragraph(
        f"<b>Total de Ventas: ${int(total_ventas):,}</b>".replace(',', '.'),
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def guardar_pdf_boleta(boleta):
    """
    Guarda PDF de boleta en campo archivo_pdf.
    
    Args:
        boleta: Instancia de Boleta
    """
    from django.core.files.base import ContentFile
    
    pdf_buffer = generar_pdf_boleta(boleta)
    
    # Guardar en campo
    boleta.archivo_pdf.save(
        f"boleta_{boleta.numero_boleta}.pdf",
        ContentFile(pdf_buffer.getvalue()),
        save=True
    )
