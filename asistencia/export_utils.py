# export_utils.py
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from datetime import datetime, date
from django.http import HttpResponse
import io
from django.contrib.auth.models import User
from .models import Area, Estado


def exportar_incidencias_docx(tabla_datos, dias, area_responsable, fecha_inicio, fecha_fin, mes_actual,
                              areas_hijas=None):
    """
    Exporta las incidencias a un documento DOCX con formato específico
    """
    # Crear documento
    doc = Document()
    # _________________________________________________________________________
    # Añadir título y encabezado
    # _________________________________________________________________________

    # Período
    p = doc.add_paragraph()
    p.add_run("Período: 01/01/2026 al 13/01/2026").bold = True
    p.add_run(" Empresa: Universidad de La Habana")

    # Generado
    p = doc.add_paragraph()
    generated_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    p.add_run(f"Generado: {generated_date}").bold = True
    p.add_run(" Unidad: [Area]")

    # Organismo
    p = doc.add_paragraph()
    p.add_run("Organismo: MES").bold = True
    p.add_run(" Confeccionado por: [ResponsableArea]")

    # Aprobado por
    doc.add_paragraph("Aprobado por:")
    doc.add_paragraph("_" * 55)

    # Espacio
    doc.add_paragraph()
    # ________________________________________________________________________________
    # Crear tabla principal 5x17 (filas x columnas)
    # ________________________________________________________________________________
    mitad = len(dias)//2
    parte1 = dias[:mitad]  # [1,..., 15]
    parte2 = dias[mitad:]  # [16,...,31]
    for dia in parte1:
        print(dia.day )
    for dia in parte2:
        print(dia.day)
    table = doc.add_table(rows=4, cols=17)
    table.style = 'Table Grid'

    hdr_cells_row1 = table.rows[0].cells
    hdr_cells_row1[0].text = 'Expte'
    hdr_cells_row1[1].text = 'Nombre y Apellidos'
    for i in range(2, len(parte1) + 2):
        hdr_cells_row1[i].text = f"{parte1[i-2].day}"


    hdr_cells_row2 = table.rows[1].cells
    hdr_cells_row2[0].text = ''
    hdr_cells_row2[1].text = ''
    for i in range(2, len(parte1) + 2):
        hdr_cells_row1[i].text = f"{parte2[i-2].day}"


    # # Fusionar celdas de la primera columna para las primeras 4 filas
    # for i in range(4):
    #     table.cell(i, 0).merge(table.cell(i, 0))


    # Tercera fila (datos)
    data_row_1 = ["", ""] + ["x", "x", "S", "D", "x", "x", "x", "x", "x", "S", "D", "x", "x", "x", "x"]
    for i, text in enumerate(data_row_1):
        cell = table.cell(2, i)
        cell.text = text
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER



    # Cuarta fila (segunda fila de datos)
    data_row_2 = ["", ""] + ["x", "x", "S", "D", "x", "x", "x", "x", "x", "S", "D", "x", "x", "x", "x"]
    for i, text in enumerate(data_row_2):
        cell = table.cell(3, i)
        cell.text = text
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Ajustar ancho de columnas
    for i, width in enumerate([0.5, 2.0] + [0.4] * 15):
        for row in table.rows:
            row.cells[i].width = Inches(width)

    return doc

# def aplicar_estilos_documento(doc):
#     """Aplica estilos personalizados al documento"""
#     # Configurar estilos de párrafo normales
#     style = doc.styles['Normal']
#     style.font.name = 'Arial'
#     style.font.size = Pt(11)
#
#     # Estilo para encabezados
#     for i in range(1, 4):
#         style = doc.styles[f'Heading {i}']
#         style.font.name = 'Arial'
#         style.font.size = Pt(14 - i * 2)
#         style.font.bold = True
#
#     return doc
#
#
# def generar_respuesta_docx(doc, nombre_archivo):
#     """
#     Genera una respuesta HTTP con el documento DOCX
#     """
#     # Aplicar estilos
#     doc = aplicar_estilos_documento(doc)
#
#     # Guardar en buffer
#     buffer = io.BytesIO()
#     doc.save(buffer)
#     buffer.seek(0)
#
#     # Crear respuesta
#     response = HttpResponse(
#         buffer.getvalue(),
#         content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
#     )
#     response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}.docx"'
#
#     return response
