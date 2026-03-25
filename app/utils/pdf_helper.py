from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

def generate_event_pdf(event):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=5,
        borderPadding=(0, 0, 2, 0),
        borderWidth=0,
        borderColor=colors.HexColor("#e2e8f0")
    )
    
    normal_style = styles['Normal']
    
    elements = []
    
    # Title
    elements.append(Paragraph(f"Event Confirmation Report: #{event.reference_id}", title_style))
    elements.append(Spacer(1, 12))
    
    # Basic Info Section
    elements.append(Paragraph("Section 1: Basic Information", section_style))
    data = [
        ["Event Title", event.title],
        ["Event Type", event.event_type],
        ["Venue", event.venue],
        ["Date", event.event_date.strftime('%B %d, %Y')],
        ["Timing", f"{event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}"],
        ["Status", event.status.value.replace('_', ' ')]
    ]
    
    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor("#64748b")),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))
    
    # Audience Section
    elements.append(Paragraph("Section 2: Audience & Participants", section_style))
    data = [
        ["Target Audience", event.audience_type],
        ["Expected Size", f"{event.audience_size} attendees"],
        ["External Guests", 'Yes' if event.is_external_audience else 'No']
    ]
    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor("#64748b")),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))
    
    # Technical & Security Section
    elements.append(Paragraph("Section 3: Resources & Budget", section_style))
    data = [
        ["Projector | Display", 'Yes' if event.requires_projector else 'No'],
        ["Microphone | Sound", 'Yes' if event.requires_microphone else 'No'],
        ["Security Personnel", 'Yes' if event.requires_security else 'No'],
        ["Estimated Budget", f"Rs. {event.budget:,.2f}"]
    ]
    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor("#64748b")),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
