"""PDF generation service for legal letters and reports."""

import io
from datetime import datetime
from typing import Optional


def generate_ccpa_letter_pdf(
    recipient_name: str,
    recipient_address: str,
    broker_name: str,
    broker_address: str,
    profile_data: dict,
    request_id: str,
) -> bytes:
    """Generate a CCPA deletion request letter as PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.units import inch
        from reportlab.lib.colors import black
    except ImportError:
        # Fallback: generate a text-based PDF using reportlab's basic primitives
        return _generate_text_pdf(
            _build_ccpa_letter_text(recipient_name, recipient_address, broker_name, broker_address, profile_data, request_id)
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch, leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=24)
    story.append(Paragraph("NOTICE OF REQUEST TO DELETE PERSONAL INFORMATION", title_style))
    story.append(Paragraph("Under the California Consumer Privacy Act (CCPA), Cal. Civ. Code § 1798.100 et seq.", styles['Normal']))
    story.append(Spacer(1, 24))

    # Date
    story.append(Paragraph(f"Date: {datetime.utcnow().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 24))

    # Recipient
    story.append(Paragraph(f"To: {broker_name}", styles['Heading2']))
    story.append(Paragraph(recipient_address.replace('\n', '<br/>'), styles['Normal']))
    story.append(Spacer(1, 24))

    # Sender
    story.append(Paragraph("From:", styles['Heading2']))
    story.append(Paragraph(recipient_name, styles['Normal']))
    story.append(Paragraph(recipient_address.replace('\n', '<br/>'), styles['Normal']))
    story.append(Spacer(1, 24))

    # Body
    body_text = f"""I am writing to exercise my right under the California Consumer Privacy Act (CCPA) to request the deletion of my personal information that you have collected.

Reference ID: {request_id}

The personal information I request you delete includes, but is not limited to:
<ul>
<li>Full Name: {profile_data.get('full_name', 'N/A')}</li>
<li>Date of Birth: {profile_data.get('dob', 'N/A')}</li>
<li>Email Addresses: {', '.join(profile_data.get('emails', ['N/A']))}</li>
<li>Phone Numbers: {', '.join(profile_data.get('phones', ['N/A']))}</li>
<li>Physical Addresses: {', '.join(profile_data.get('addresses', ['N/A']))}</li>
</ul>

Pursuant to Cal. Civ. Code § 1798.105, I request that you delete all personal information about me that you have collected and retained. Please confirm in writing within 45 days that you have complied with this request.

If you require additional information to verify my identity, please contact me at the address above or via email at {profile_data.get('emails', ['N/A'])[0] if profile_data.get('emails') else 'N/A'}.

This request is made in good faith and in reliance on the provisions of the CCPA. Failure to comply with this request may result in legal action."""

    story.append(Paragraph(body_text, styles['Normal']))
    story.append(Spacer(1, 36))
    story.append(Paragraph("Sincerely,", styles['Normal']))
    story.append(Spacer(1, 48))
    story.append(Paragraph(recipient_name, styles['Normal']))

    doc.build(story)
    return buffer.getvalue()


def generate_gdpr_letter_pdf(
    recipient_name: str,
    recipient_address: str,
    broker_name: str,
    broker_address: str,
    profile_data: dict,
    request_id: str,
) -> bytes:
    """Generate a GDPR deletion request letter as PDF."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
    except ImportError:
        return _generate_text_pdf(
            _build_gdpr_letter_text(recipient_name, recipient_address, broker_name, broker_address, profile_data, request_id)
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch, leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=24)
    story.append(Paragraph("REQUEST FOR ERASURE UNDER ARTICLE 17 GDPR", title_style))
    story.append(Paragraph("Under the General Data Protection Regulation (EU) 2016/679 (GDPR)", styles['Normal']))
    story.append(Spacer(1, 24))

    story.append(Paragraph(f"Date: {datetime.utcnow().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 24))

    story.append(Paragraph(f"To: {broker_name}", styles['Heading2']))
    story.append(Paragraph(recipient_address.replace('\n', '<br/>'), styles['Normal']))
    story.append(Spacer(1, 24))

    story.append(Paragraph("From:", styles['Heading2']))
    story.append(Paragraph(recipient_name, styles['Normal']))
    story.append(Paragraph(recipient_address.replace('\n', '<br/>'), styles['Normal']))
    story.append(Spacer(1, 24))

    body_text = f"""I am writing to exercise my right to erasure ("right to be forgotten") under Article 17 of the General Data Protection Regulation (GDPR).

Reference ID: {request_id}

I request the immediate erasure of my personal data that you hold, including but not limited to:
<ul>
<li>Full Name: {profile_data.get('full_name', 'N/A')}</li>
<li>Date of Birth: {profile_data.get('dob', 'N/A')}</li>
<li>Email Addresses: {', '.join(profile_data.get('emails', ['N/A']))}</li>
<li>Phone Numbers: {', '.join(profile_data.get('phones', ['N/A']))}</li>
<li>Physical Addresses: {', '.join(profile_data.get('addresses', ['N/A']))}</li>
</ul>

Under Article 17(1) GDPR, you are required to erase personal data without undue delay. Please confirm in writing within 30 days that you have complied with this request.

If you have shared my personal data with other parties, please inform them of this erasure request pursuant to Article 19 GDPR.

Contact me at {profile_data.get('emails', ['N/A'])[0] if profile_data.get('emails') else 'N/A'} for any questions."""

    story.append(Paragraph(body_text, styles['Normal']))
    story.append(Spacer(1, 36))
    story.append(Paragraph("Sincerely,", styles['Normal']))
    story.append(Spacer(1, 48))
    story.append(Paragraph(recipient_name, styles['Normal']))

    doc.build(story)
    return buffer.getvalue()


def _generate_text_pdf(text_content: str) -> bytes:
    """Fallback: generate a simple text-based PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch, leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()

    story = []
    for line in text_content.split('\n'):
        if line.strip():
            story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 6))

    doc.build(story)
    return buffer.getvalue()


def _build_ccpa_letter_text(recipient_name, recipient_address, broker_name, broker_address, profile_data, request_id):
    return f"""NOTICE OF REQUEST TO DELETE PERSONAL INFORMATION
Under the California Consumer Privacy Act (CCPA), Cal. Civ. Code 1798.100 et seq.

Date: {datetime.utcnow().strftime('%B %d, %Y')}

To: {broker_name}
{recipient_address}

From: {broker_address}

Reference ID: {request_id}

I am writing to exercise my right under the California Consumer Privacy Act (CCPA) to request the deletion of my personal information.

Personal information to delete:
- Full Name: {profile_data.get('full_name', 'N/A')}
- Date of Birth: {profile_data.get('dob', 'N/A')}
- Emails: {', '.join(profile_data.get('emails', ['N/A']))}
- Phones: {', '.join(profile_data.get('phones', ['N/A']))}
- Addresses: {', '.join(profile_data.get('addresses', ['N/A']))}

Please confirm in writing within 45 days.

Sincerely,
{broker_address}"""


def _build_gdpr_letter_text(recipient_name, recipient_address, broker_name, broker_address, profile_data, request_id):
    return f"""REQUEST FOR ERASURE UNDER ARTICLE 17 GDPR
Under the General Data Protection Regulation (EU) 2016/679

Date: {datetime.utcnow().strftime('%B %d, %Y')}

To: {broker_name}
{recipient_address}

From: {broker_address}

Reference ID: {request_id}

I request the immediate erasure of my personal data under Article 17 GDPR.

Personal data to erase:
- Full Name: {profile_data.get('full_name', 'N/A')}
- Date of Birth: {profile_data.get('dob', 'N/A')}
- Emails: {', '.join(profile_data.get('emails', ['N/A']))}
- Phones: {', '.join(profile_data.get('phones', ['N/A']))}
- Addresses: {', '.join(profile_data.get('addresses', ['N/A']))}

Please confirm within 30 days.

Sincerely,
{broker_address}"""
