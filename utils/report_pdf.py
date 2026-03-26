import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

class CRCReport(FPDF):
    def header(self):
        # Logo placeholder or just Title
        self.set_font("helvetica", "B", 16)
        self.set_text_color(13, 27, 42) # Navy
        self.cell(0, 10, "Relatorio Executivo | Status CRC", ln=True, align="C")
        self.set_font("helvetica", "I", 10)
        self.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

def sanitize(text):
    """Deeply sanitize text to ensure compatibility with standard PDF fonts."""
    if text is None: return ""
    text = str(text)
    # Manual mapping for common Portuguese accented characters to non-accented
    rep = {
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 
        'Á': 'A', 'À': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C',
        '–': '-', '—': '-', '“': '"', '”': '"', '‘': "'", '’': "'"
    }
    for char, replacement in rep.items():
        text = text.replace(char, replacement)
    
    # Final cleanup of any other non-ascii characters
    return text.encode('ascii', 'ignore').decode('ascii')

def generate_pdf_report(kpi_data, df_esc, df_trib):
    pdf = CRCReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. KPIs Section
    pdf.set_font("helvetica", "B", 12)
    pdf.set_fill_color(5, 150, 105) # Teal
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "  Indicadores de Performance (KPIs)", ln=True, fill=True)
    pdf.ln(5)

    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    # KPI Table Header
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(60, 8, "Metrica", border=1, align="C")
    pdf.cell(40, 8, "Vl. Atual", border=1, align="C")
    pdf.cell(40, 8, "Vl. Anterior", border=1, align="C")
    pdf.cell(50, 8, "Variacao", border=1, align="C", ln=True)
    
    pdf.set_font("helvetica", "", 10)
    for kpi in kpi_data:
        pdf.cell(60, 8, sanitize(kpi['label']), border=1)
        pdf.cell(40, 8, str(kpi['current']), border=1, align="C")
        pdf.cell(40, 8, str(kpi['prev']), border=1, align="C")
        
        delta = kpi['current'] - kpi['prev']
        delta_pct = (delta / kpi['prev'] * 100) if kpi['prev'] else 0
        delta_str = f"{'+' if delta >= 0 else ''}{round(delta_pct, 1)}%"
        
        pdf.cell(50, 8, delta_str, border=1, align="C", ln=True)

    pdf.ln(10)

    # 2. Escalations Table
    if not df_esc.empty:
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(214, 40, 40) # Danger Red
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "  Casos em Escalation", ln=True, fill=True)
        pdf.ln(3)
        
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 7, "Cliente", border=1)
        pdf.cell(30, 7, "Regional", border=1)
        pdf.cell(20, 7, "Saude", border=1, align="C")
        pdf.cell(0, 7, "Status", border=1, ln=True)
        
        pdf.set_font("helvetica", "", 7)
        for _, row in df_esc.head(20).iterrows(): # Limit to top 20 for PDF
            pdf.cell(40, 7, sanitize(row['Cliente'])[:25], border=1)
            pdf.cell(30, 7, sanitize(row['Regional']), border=1)
            pdf.cell(20, 7, f"{row['HealthScore']}%", border=1, align="C")
            # Multi-cell for status wrapping
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(0, 7, sanitize(row['Status']), border=1)
            pdf.set_xy(x, y + 7) # This is tricky with multi_cell, let's simplify for now
            pdf.ln(0) # Placeholder

    # 3. Ref Tributaria Table
    if not df_trib.empty:
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(13, 27, 42) # Navy
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "  Reforma Tributaria / OnePass", ln=True, fill=True)
        pdf.ln(3)
        
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 7, "Cliente", border=1)
        pdf.cell(0, 7, "Status de Homologacao", border=1, ln=True)
        
        pdf.set_font("helvetica", "", 7)
        for _, row in df_trib.head(15).iterrows():
            pdf.cell(50, 7, sanitize(row['Cliente'])[:35], border=1)
            pdf.cell(0, 7, sanitize(row['Status'])[:100], border=1, ln=True)

    return bytes(pdf.output())
