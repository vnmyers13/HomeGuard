# ---------------------------------------------------------------------------
# Email & Legal Letter Templates
# ---------------------------------------------------------------------------
# Generates HTML/text templates for:
# - Opt-out request emails to brokers
# - Legal demand letters (CCPA/GDPR)
# - User notification emails
# ---------------------------------------------------------------------------

import base64
from datetime import datetime, timezone
from typing import Optional
from jinja2 import Template


# ---------------------------------------------------------------------------
# Generic Removal Request - HTML Letter
# ---------------------------------------------------------------------------

GENERIC_REMOVAL_HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Times New Roman', serif; margin: 60px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #2c5282; padding-bottom: 20px; }
        .title { font-size: 24px; font-weight: bold; color: #2c5282; }
        .subtitle { font-size: 14px; color: #718096; margin-top: 5px; }
        .date { text-align: right; margin-bottom: 30px; }
        .content { margin: 20px 0; }
        .consumer-info { background-color: #ebf8ff; padding: 15px; border-left: 4px solid #2c5282; margin: 20px 0; }
        .laws { background-color: #f0fff4; padding: 15px; border-left: 4px solid #38a169; margin: 20px 0; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #718096; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">OpenDataRemoval Privacy Services</div>
        <div class="subtitle">Data Removal Request</div>
    </div>

    <div class="date">{{ date }}</div>

    <div class="content">
        <p>Dear Sir/Madam,</p>

        <p>I am writing to formally request the removal of my personal information from your website and databases.</p>

        <div class="consumer-info">
            <strong>Consumer Information:</strong><br>
            Full Name: {{ full_name }}<br>
            {% if dob %}Date of Birth: {{ dob }}<br>{% endif %}
            {% if address %}Current Address: {{ address }}<br>{% endif %}
            {% if previous_addresses %}Previous Addresses: {{ previous_addresses }}<br>{% endif %}
            Email: {{ email }}
        </div>
        <p>I have found my personal information listed on your platform and I request its immediate removal.</p>
        <div class="laws">
            <strong>Applicable Privacy Laws:</strong><br>
            This request is made in accordance with applicable privacy laws including but not limited to:
            <ul>
                <li>The California Consumer Privacy Act (CCPA)</li>
                <li>The General Data Protection Regulation (GDPR) if applicable</li>
                <li>The Right of Erasure under Article 17 of GDPR</li>
            </ul>
        </div>
        <p>Please confirm the removal of my data within 30 days as required by law.</p>
        <p>If you require additional verification of my identity, please let me know what steps are needed.</p>
        <p>Failure to comply with this request may result in legal action and reporting to the appropriate data protection authorities.</p>
        <p>Sincerely,<br>{{ full_name }}</p>
    </div>
    <div class="footer">
        <p>This is an automated request sent via OpenDataRemoval Privacy Services.</p>
    </div>
 </body>
</html>
""")


# ---------------------------------------------------------------------------
# Generic Removal Request - Plain Text
# ---------------------------------------------------------------------------

GENERIC_REMOVAL_TXT_TEMPLATE = Template("""
Data Removal Request - {{ full_name }}

Dear Sir/Madam,

I am writing to formally request the removal of my personal information from your website and databases.

My details are as follows:
- Full Name: {{ full_name }}
{% if dob %}- Date of Birth: {{ dob }}
{% endif %}
{% if address %}- Current Address: {{ address }}
{% endif %}
{% if previous_addresses %}- Previous Addresses: {{ previous_addresses }}
{% endif %}

I have found my personal information listed on your platform and I request its immediate removal in accordance with applicable privacy laws including but not limited to:
- The California Consumer Privacy Act (CCPA)
- The General Data Protection Regulation (GDPR) if applicable
- The Right of Erasure under Article 17 of GDPR

Please confirm the removal of my data within 30 days as required by law.

If you require additional verification of my identity, please let me know what steps are needed.

Failure to comply with this request may result in legal action and reporting to the appropriate data protection authorities.

Sincerely,
{{ full_name }}
{{ email }}
""")


# ---------------------------------------------------------------------------
# Opt-out Request Email Template (legacy plain text)
# ---------------------------------------------------------------------------

OPT_OUT_EMAIL_TEMPLATE = Template("""
Subject: Request for Data Removal - {{ full_name }}

Dear Sir/Madam,

I am writing to formally request the removal of my personal information from your website and databases.

My details are as follows:
- Full Name: {{ full_name }}
- Date of Birth: {{ dob|default("N/A") }}
- Current Address: {{ address|default("N/A") }}
- Previous Addresses: {{ previous_addresses|default("N/A") }}

I have found my personal information listed on your platform and I request its immediate removal in accordance with applicable privacy laws including but not limited to:
- The California Consumer Privacy Act (CCPA)
- The General Data Protection Regulation (GDPR) if applicable
- The Right of Erasure under Article 17 of GDPR

Please confirm the removal of my data within 30 days as required by law.

If you require additional verification of my identity, please let me know what steps are needed.

Failure to comply with this request may result in legal action and reporting to the appropriate data protection authorities.

Sincerely,
{{ full_name }}
{{ address|default("") }}
{{ email }}
""")


# ---------------------------------------------------------------------------
# CCPA Data Deletion Request - HTML Letter
# ---------------------------------------------------------------------------

CCPA_LETTER_HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Times New Roman', serif; margin: 60px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #2c5282; padding-bottom: 20px; }
        .title { font-size: 24px; font-weight: bold; color: #2c5282; }
        .subtitle { font-size: 14px; color: #718096; margin-top: 5px; }
        .date { text-align: right; margin-bottom: 30px; }
        .content { margin: 20px 0; }
        .consumer-info { background-color: #ebf8ff; padding: 15px; border-left: 4px solid #2c5282; margin: 20px 0; }
        .legal-ref { background-color: #f0fff4; padding: 15px; border-left: 4px solid #38a169; margin: 20px 0; }
        .deadline { background-color: #fff5f5; padding: 15px; border-left: 4px solid #e53e3e; margin: 20px 0; font-weight: bold; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #718096; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">OpenDataRemoval Privacy Services</div>
        <div class="subtitle">CCPA Data Deletion Request</div>
    </div>

    <div class="date">{{ date }}</div>

    <div class="content">
        <p>To Whom It May Concern,</p>

        <p>Pursuant to the California Consumer Privacy Act of 2018 (CCPA), I am submitting a formal request for the deletion of all personal information you have collected about me.</p>

        <div class="consumer-info">
            <strong>Consumer Information:</strong><br>
            Name: {{ full_name }}<br>
            Email: {{ email }}<br>
            {% if address %}Address: {{ address }}<br>{% endif %}
            {% if dob %}Date of Birth: {{ dob }}<br>{% endif %}
        </div>

        <div class="legal-ref">
            <strong>CCPA Section 1798.105 Requirements:</strong><br>
            Under the CCPA, I request that you:
            <ol>
                <li>Delete all personal information you have collected from me</li>
                <li>Direct your service providers to delete such information</li>
                <li>Confirm completion of this deletion in writing</li>
            </ol>
        </div>

        <div class="deadline">
            Response Deadline: 45 days from the date of this request as provided by CCPA law.
            If you decline this request, you must provide the reasons for denial and any information necessary to submit an appeal.
        </div>

        <p>This request is being made through my authorized agent (OpenDataRemoval) acting on my behalf.</p>

        <p>Regards,<br>{{ full_name }}</p>
    </div>

    <div class="footer">
        <p>This is an automated request sent via OpenDataRemoval Privacy Services on your behalf.</p>
    </div>
</body>
</html>
""")


# ---------------------------------------------------------------------------
# CCPA Data Deletion Request (plain text)
# ---------------------------------------------------------------------------

CCPA_DELETION_TEMPLATE = Template("""
Subject: CCPA Data Deletion Request - {{ full_name }}

To Whom It May Concern,

Pursuant to the California Consumer Privacy Act of 2018 (CCPA), I am submitting a formal request for the deletion of all personal information you have collected about me.

Consumer Information:
- Name: {{ full_name }}
- Email: {{ email }}
- Address: {{ address|default("N/A") }}
- Date of Birth: {{ dob|default("N/A") }}

Under CCPA Section 1798.105, I request that you:
1. Delete all personal information you have collected from me
2. Direct your service providers to delete such information
3. Confirm completion of this deletion in writing

I expect a response within 45 days as provided by law. If you decline this request, you must provide the reasons for denial and any information necessary to submit an appeal.

This request is being made through my authorized agent (OpenDataRemoval) acting on my behalf.

Regards,
{{ full_name }}
""")


# ---------------------------------------------------------------------------
# GDPR Right to Erasure Request - HTML Letter
# ---------------------------------------------------------------------------

GDPR_LETTER_HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Times New Roman', serif; margin: 60px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #2c5282; padding-bottom: 20px; }
        .title { font-size: 24px; font-weight: bold; color: #2c5282; }
        .subtitle { font-size: 14px; color: #718096; margin-top: 5px; }
        .date { text-align: right; margin-bottom: 30px; }
        .content { margin: 20px 0; }
        .subject-info { background-color: #ebf8ff; padding: 15px; border-left: 4px solid #2c5282; margin: 20px 0; }
        .legal-ref { background-color: #f0fff4; padding: 15px; border-left: 4px solid #38a169; margin: 20px 0; }
        .deadline { background-color: #fff5f5; padding: 15px; border-left: 4px solid #e53e3e; margin: 20px 0; font-weight: bold; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #718096; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">OpenDataRemoval Privacy Services</div>
        <div class="subtitle">GDPR Right to Erasure Request</div>
    </div>

    <div class="date">{{ date }}</div>

    <div class="content">
        <p>Dear Data Protection Officer,</p>

        <p>I am writing to exercise my Right to Erasure under Article 17 of the General Data Protection Regulation (GDPR).</p>

        <div class="subject-info">
            <strong>Data Subject Information:</strong><br>
            Full Name: {{ full_name }}<br>
            Email: {{ email }}<br>
            {% if address %}Address: {{ address }}<br>{% endif %}
        </div>

        <p>I request the immediate deletion of all personal data you hold about me.</p>

        <div class="legal-ref">
            <strong>Article 17(1) of the GDPR</strong><br>
            You are required to erase personal data without undue delay where one of the following applies:
            <ol>
                <li>(a) The data is no longer necessary for the purposes it was collected</li>
                <li>(b) I withdraw my consent</li>
                <li>(c) I object to the processing under Article 21(1)</li>
                <li>(d) The data has been unlawfully processed</li>
            </ol>
        </div>

        <div class="deadline">
            Response Deadline: 30 days from the date of this request, or notification of any extension with reasons.
        </div>

        <p>Failure to comply may result in complaints to the relevant supervisory authority and potential legal action.</p>

        <p>Yours sincerely,<br>{{ full_name }}</p>
    </div>

    <div class="footer">
        <p>This is an automated request sent via OpenDataRemoval Privacy Services on your behalf.</p>
    </div>
</body>
</html>
""")


# ---------------------------------------------------------------------------
# GDPR Erasure Request (plain text)
# ---------------------------------------------------------------------------

GDPR_ERASURE_TEMPLATE = Template("""
Subject: GDPR Right to Erasure Request - {{ full_name }}

Dear Data Protection Officer,

I am writing to exercise my Right to Erasure under Article 17 of the General Data Protection Regulation (GDPR).

I request the immediate deletion of all personal data you hold about me:

- Full Name: {{ full_name }}
- Email: {{ email }}
- Address: {{ address|default("N/A") }}

Under Article 17(1) of the GDPR, you are required to erase personal data without undue delay where one of the following applies:
(a) The data is no longer necessary for the purposes it was collected
(b) I withdraw my consent
(c) I object to the processing under Article 21(1)
(d) The data has been unlawfully processed

I request confirmation of deletion within 30 days, or notification of any extension with reasons.

Failure to comply may result in complaints to the relevant supervisory authority and potential legal action.

Yours sincerely,
{{ full_name }}
""")


# ---------------------------------------------------------------------------
# Legal Demand Letter Template (HTML)
# ---------------------------------------------------------------------------

LEGAL_DEMAND_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Times New Roman', serif; margin: 60px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; }
        .firm-name { font-size: 18px; font-weight: bold; text-transform: uppercase; }
        .date { margin-top: 20px; }
        .recipient { margin-bottom: 30px; }
        .subject { font-weight: bold; margin: 20px 0; }
        .body-text { text-align: justify; margin-bottom: 15px; }
        .signature { margin-top: 40px; }
        .deadline { background-color: #ffe6e6; padding: 10px; border-left: 3px solid red; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <div class="firm-name">OpenDataRemoval Privacy Services</div>
        <div>Data Protection & Privacy Compliance</div>
    </div>

    <div class="date">{{ date }}</div>

    <div class="recipient">
        {{ recipient_name|default("Data Protection Officer") }}<br>
        {{ company_name }}<br>
        {{ company_address|default("N/A") }}
    </div>

    <div class="subject">RE: Formal Demand for Data Removal - {{ full_name }}</div>

    <div class="body-text">
        Dear {{ recipient_name|default("Sir/Madam") }},
    </div>

    <div class="body-text">
        We represent {{ full_name }} ("our client") in matters relating to data privacy and protection. 
        We are writing to formally demand the immediate removal of our client's personal information from 
        your website ({{ domain }}) and all associated databases.
    </div>

    <div class="body-text">
        Our client's personal information has been identified on your platform, including but not limited to:
    </div>

    <ul>
        {% if full_name %}<li>Full Name: {{ full_name }}</li>{% endif %}
        {% if address %}<li>Address: {{ address }}</li>{% endif %}
        {% if dob %}<li>Date of Birth: {{ dob }}</li>{% endif %}
        {% if phone %}<li>Phone Number: {{ phone }}</li>{% endif %}
        {% if email %}<li>Email Address: {{ email }}</li>{% endif %}
    </ul>

    <div class="body-text">
        This unauthorized listing violates applicable privacy legislation including:
    </div>

    <ul>
        <li>California Consumer Privacy Act (CCPA) - Cal. Civ. Code § 1798.100 et seq.</li>
        <li>California Online Privacy Protection Act (CalOPPA)</li>
        <li>General Data Protection Regulation (GDPR) - where applicable</li>
    </ul>

    <div class="deadline">
        <strong>DEADLINE:</strong> You have {{ deadline_days|default(10) }} calendar days from the date of this letter 
        to confirm in writing that our client's personal information has been permanently removed from all 
        your platforms and databases. Failure to comply will result in immediate legal action.
    </div>

    <div class="body-text">
        Please direct your written confirmation to:
    </div>

    <div class="body-text">
        {{ full_name }}<br>
        Via OpenDataRemoval Privacy Services<br>
        {{ email }}
    </div>

    <div class="body-text">
        This letter is without prejudice to our client's rights and remedies, all of which are expressly reserved.
    </div>

    <div class="signature">
        Sincerely,<br><br>
        <strong>OpenDataRemoval Privacy Services</strong><br>
        Automated Privacy Compliance System
    </div>
</body>
</html>
""")


# ---------------------------------------------------------------------------
# User Notification Templates
# ---------------------------------------------------------------------------

SCAN_COMPLETE_TEMPLATE = Template("""
Subject: Your Privacy Scan is Complete - {{ profile_count }} Profiles Found

Hi {{ user_name }},

Your privacy scan has been completed! Here's a summary:

- Profiles found: {{ profile_count }}
- High-risk exposures: {{ high_risk_count }}
- Removal requests submitted: {{ requests_submitted }}

Log in to OpenDataRemoval to see detailed results and track your removal requests.

Regards,
OpenDataRemoval Team
""")


# ---------------------------------------------------------------------------
# Template rendering functions
# ---------------------------------------------------------------------------

def render_generic_removal_html(context: dict) -> str:
    """Render generic removal request as HTML."""
    context.setdefault("date", datetime.now(timezone.utc).strftime("%B %d, %Y"))
    return GENERIC_REMOVAL_HTML_TEMPLATE.render(**context)


def render_generic_removal_txt(context: dict) -> str:
    """Render generic removal request as plain text."""
    return GENERIC_REMOVAL_TXT_TEMPLATE.render(**context)


def render_opt_out_email(context: dict) -> str:
    """Render opt-out request email."""
    return OPT_OUT_EMAIL_TEMPLATE.render(**context)


def render_ccpa_letter_html(context: dict) -> str:
    """Render CCPA deletion request as HTML letter."""
    context.setdefault("date", datetime.now(timezone.utc).strftime("%B %d, %Y"))
    return CCPA_LETTER_HTML_TEMPLATE.render(**context)


def render_ccpa_deletion(context: dict) -> str:
    """Render CCPA deletion request."""
    return CCPA_DELETION_TEMPLATE.render(**context)


def render_gdpr_letter_html(context: dict) -> str:
    """Render GDPR erasure request as HTML letter."""
    context.setdefault("date", datetime.now(timezone.utc).strftime("%B %d, %Y"))
    return GDPR_LETTER_HTML_TEMPLATE.render(**context)


def render_gdpr_erasure(context: dict) -> str:
    """Render GDPR erasure request."""
    return GDPR_ERASURE_TEMPLATE.render(**context)


def render_legal_demand(context: dict) -> str:
    """Render legal demand letter as HTML."""
    context.setdefault("date", datetime.now(timezone.utc).strftime("%B %d, %Y"))
    return LEGAL_DEMAND_TEMPLATE.render(**context)


def render_scan_complete(context: dict) -> str:
    """Render scan completion notification."""
    return SCAN_COMPLETE_TEMPLATE.render(**context)


def render_legal_demand_pdf_context(context: dict) -> dict:
    """Prepare context for PDF generation of legal demand letter."""
    context.setdefault("date", datetime.now(timezone.utc).strftime("%B %d, %Y"))
    context.setdefault("deadline_days", 10)
    return context


def encode_pdf_for_email(pdf_bytes: bytes, filename: str = "legal_demand.pdf") -> str:
    """Encode PDF bytes for email attachment."""
    return base64.b64encode(pdf_bytes).decode("ascii")


# ---------------------------------------------------------------------------
# Template registry for lookup by type
# ---------------------------------------------------------------------------

TEMPLATES = {
    "generic_removal_html": render_generic_removal_html,
    "generic_removal_txt": render_generic_removal_txt,
    "opt_out_email": render_opt_out_email,
    "ccpa_letter_html": render_ccpa_letter_html,
    "ccpa_deletion": render_ccpa_deletion,
    "gdpr_letter_html": render_gdpr_letter_html,
    "gdpr_erasure": render_gdpr_erasure,
    "legal_demand": render_legal_demand,
    "scan_complete": render_scan_complete,
}


def render_template(template_name: str, context: dict) -> Optional[str]:
    """Render a template by name."""
    renderer = TEMPLATES.get(template_name)
    if not renderer:
        raise ValueError(f"Unknown template: {template_name}")
    return renderer(context)