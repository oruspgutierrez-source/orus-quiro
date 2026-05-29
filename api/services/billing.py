import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from api.services.wa_client import wa_client

def draw_invoice_background(canvas, doc):
    """
    Dibuja el color de fondo pergamino y el marco ornamental sutil interno
    del diseño V3 aprobado por el usuario en el canvas del PDF.
    """
    canvas.saveState()
    # Color de fondo de la página (Simula el degradado fdfbf7 a f5f0e6 en plano)
    canvas.setFillColor(colors.HexColor('#fcfaf7'))
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    
    # Marco ornamental sutil interno (20px de margen = 20 puntos)
    canvas.setStrokeColor(colors.HexColor('#e1d6c5'))
    canvas.setLineWidth(1)
    canvas.setStrokeAlpha(0.6)
    canvas.rect(20, 20, doc.pagesize[0] - 40, doc.pagesize[1] - 40, stroke=True, fill=False)
    canvas.restoreState()

def generate_invoice_pdf(
    transaction_id: str, 
    client_name: str, 
    client_email: str, 
    amount: float, 
    currency: str
) -> str:
    """
    Renderiza una factura simplificada premium en formato PDF con los datos de la transacción
    utilizando el diseño exacto V3 aprobado por el usuario:
    - Colores Terracota (#cf664e) y tonos cálidos topo/arena.
    - Marco ornamental interno y fondo suave.
    - Monograma "OQ" y jerarquía tipográfica clásica.
    
    Retorna:
    - str: Ruta absoluta del archivo PDF generado.
    """
    # 1. Asegurar la existencia de la carpeta de destino
    output_dir = os.path.abspath("resources/media/invoices")
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, f"factura_{transaction_id}.pdf")
    
    # 2. Definir colores corporativos V3
    terracota_orus = colors.HexColor('#cf664e')
    terracota_cabecera = colors.HexColor('#e26a54')
    carbon_texto = colors.HexColor('#3a3530')
    gris_label = colors.HexColor('#7a746e')
    gris_subtitle = colors.HexColor('#66615c')
    fondo_celdas = colors.HexColor('#f5f0e6')
    gris_borde = colors.HexColor('#e6dfd3')
    blanco = colors.HexColor('#FFFFFF')

    # 3. Inicializar el documento (tamaño carta con márgenes proporcionales al marco)
    doc = SimpleDocTemplate(
        file_path, 
        pagesize=letter, 
        rightMargin=45, 
        leftMargin=45, 
        topMargin=45, 
        bottomMargin=45
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # 4. Crear estilos de texto personalizados basados en la tipografía Georgia (Times en PDF por portabilidad)
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Times-Roman',
        fontSize=24,
        textColor=terracota_orus,
        spaceAfter=6,
        letterSpacing=1
    )
    
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=10,
        textColor=gris_subtitle,
        leading=13
    )
    
    contact_style = ParagraphStyle(
        'InvoiceContact',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        textColor=gris_label,
        leading=14
    )

    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Times-Roman',
        fontSize=11.5,
        textColor=terracota_orus,
        spaceBefore=15,
        spaceAfter=8,
        letterSpacing=1
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        textColor=carbon_texto,
        leading=14
    )

    body_regular = ParagraphStyle(
        'BodyRegular',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        textColor=carbon_texto,
        leading=14
    )

    body_label = ParagraphStyle(
        'BodyLabel',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=10,
        textColor=gris_label,
        leading=14
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9,
        textColor=blanco,
        alignment=TA_LEFT,
        letterSpacing=0.5
    )
    
    table_header_right = ParagraphStyle(
        'TableHeaderRight',
        parent=table_header,
        alignment=TA_RIGHT
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        textColor=carbon_texto,
        leading=14,
        alignment=TA_LEFT
    )
    
    table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=table_cell,
        alignment=TA_RIGHT
    )

    quote_style = ParagraphStyle(
        'QuoteText',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=11,
        textColor=terracota_orus,
        alignment=TA_CENTER,
        leading=15,
        spaceBefore=25,
        spaceAfter=15
    )

    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        textColor=gris_label,
        alignment=TA_LEFT,
        leading=13
    )

    # 5. Encabezado de Factura V3
    fecha_emision = datetime.now().strftime("%d/%m/%Y")
    
    header_left = [
        Spacer(1, 15),
        Paragraph("Orus Quiroterapia", title_style),
        Paragraph("Lecturas de Quiromancia Védica & Astrología Biométrica", subtitle_style),
        Spacer(1, 4),
        Paragraph("Contacto: contacto@orusquiroterapia.online", contact_style),
        Paragraph("Website: https://orusquiroterapia.online", contact_style),
    ]
    
    header_right = [
        Spacer(1, 15),
        Paragraph("Doc. de Confirmación", ParagraphStyle('DocType', parent=title_style, fontSize=13, alignment=TA_RIGHT, spaceAfter=8)),
        Paragraph(f"<b>N° Transacción:</b> {transaction_id}", ParagraphStyle('RightSub', parent=contact_style, alignment=TA_RIGHT)),
        Paragraph(f"<b>Fecha de Emisión:</b> {fecha_emision}", ParagraphStyle('RightSub2', parent=contact_style, alignment=TA_RIGHT)),
        Paragraph("<b>Estado de Pago:</b> <font color='#2e7d32'><b>PAGADO</b></font>", ParagraphStyle('RightSub3', parent=contact_style, alignment=TA_RIGHT)),
    ]

    header_table_data = [
        [header_left, header_right]
    ]

    # colWidths suman 522 de ancho imprimible disponible
    header_table = Table(header_table_data, colWidths=[292, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # 6. Sección: Datos del Consultante
    story.append(Paragraph("Datos del Consultante", section_title))
    client_data = [
        [Paragraph("Nombre del Consultante:", body_label), Paragraph(client_name, body_regular)],
        [Paragraph("Correo Electrónico:", body_label), Paragraph(client_email or "No provisto", body_regular)]
    ]
    client_table = Table(client_data, colWidths=[160, 362])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(client_table)

    # 7. Sección: Detalles del Servicio
    story.append(Paragraph("Detalles del Servicio", section_title))
    service_data = [
        [Paragraph("Concepto de Consulta:", body_label), Paragraph("Lectura Completa de Quiromancia Védica", body_regular)],
        [Paragraph("Formato de Entrega:", body_label), Paragraph("Asíncrono (Audio de 3min + Reporte + PDF)", body_regular)]
    ]
    service_table = Table(service_data, colWidths=[160, 362])
    service_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(service_table)
    story.append(Spacer(1, 15))

    # 8. Tabla Principal de Conceptos Financieros
    table_data = [
        # Cabecera
        [
            Paragraph("Descripción del Concepto", table_header),
            Paragraph("Cantidad", table_header_right),
            Paragraph("Precio Unit.", table_header_right),
            Paragraph("Subtotal", table_header_right)
        ],
        # Fila 1
        [
            Paragraph("Lectura Completa de Quiromancia Védica: Análisis biométrico y lectura personalizada de señales en la mano.", table_cell),
            Paragraph("1", table_cell_right),
            Paragraph(f"{amount:.2f} {currency.upper()}", table_cell_right),
            Paragraph(f"{amount:.2f} {currency.upper()}", table_cell_right)
        ],
        # Fila Total
        [
            "",
            "",
            Paragraph("Total Pagado:", ParagraphStyle('TotalLbl', parent=body_bold, alignment=TA_RIGHT)),
            Paragraph(f"<b>{amount:.2f} {currency.upper()}</b>", ParagraphStyle('TotalVal', parent=body_bold, textColor=terracota_orus, alignment=TA_RIGHT))
        ]
    ]

    invoice_table = Table(table_data, colWidths=[262, 70, 95, 95])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), terracota_cabecera),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fbf9f5')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f5f0e6')),
        ('GRID', (0, 0), (-1, 1), 0.5, gris_borde),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        # Combinar celdas en la fila de Total
        ('SPAN', (0, 2), (1, 2)),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 15))

    # 9. Cita / Texto Destacado
    story.append(Paragraph('"Las líneas de tus manos no son más que el mapa de tu alma trazado por el destino, listo para ser descifrado por la sabiduría."', quote_style))
    
    # 10. Pie de Página
    story.append(Spacer(1, 10))
    story.append(Paragraph("Este documento es una confirmación de pago simplificada emitida electrónicamente por Orus Quiroterapia.", footer_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Una vez confirmado el pago, el análisis inicia su proceso de elaboración védica con un tiempo estimado de entrega de 24 a 48 horas hábiles.", footer_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Gracias por confiar en Orus. Tu camino está guiado por la luz del conocimiento.", ParagraphStyle('FooterSub', parent=footer_style, fontName='Times-Italic', alignment=TA_CENTER, spaceBefore=6)))

    # 11. Compilar el PDF con la función de fondo y marco ornamental
    doc.build(story, onFirstPage=draw_invoice_background)
    
    print(f"[Billing] Factura PDF generada exitosamente en: {file_path}", flush=True)
    return file_path

async def send_invoice_by_whatsapp(
    jid: str, 
    pdf_path: str, 
    client_name: str, 
    transaction_id: str
) -> dict:
    """
    Envía la factura en PDF generada a través de WhatsApp como un documento nativo adjunto.
    """
    caption = (
        f"Tu pago ha sido procesado con éxito (Transacción: {transaction_id}).\n"
        f"Adjunto tu comprobante oficial.\n"
        f"Tu espacio en el taller está asegurado.\n"
        f"En breve recibirás las opciones de agenda para coordinar tu primera sesión."
    )
    
    file_name = f"factura_{transaction_id}.pdf"
    
    print(f"[Billing] Despachando factura por WhatsApp a JID={jid}, Archivo={file_name}", flush=True)
    
    res = await wa_client.send_document_message(
        to=jid,
        file_path=pdf_path,
        file_name=file_name,
        caption=caption
    )
    
    return res
