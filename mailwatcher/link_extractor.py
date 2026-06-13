# ---------------------------------------------------------------------------
# Link Extractor — Parse removal confirmation links from broker emails
# ---------------------------------------------------------------------------
# Extracts opt-out/removal confirmation URLs from email content.
# Used by the email processing workflow to auto-discover broker opt-out pages.
# ---------------------------------------------------------------------------

import logging
import re
from typing import Optional
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


# Patterns that commonly indicate opt-out/removal links
OPT_OUT_PATTERNS = [
    re.compile(r'opt[- ]?out', re.IGNORECASE),
    re.compile(r'remove[^\n]*request', re.IGNORECASE),
    re.compile(r'privacy[^\n]*request', re.IGNORECASE),
    re.compile(r'delete[^\n]*account', re.IGNORECASE),
    re.compile(r'unlist', re.IGNORECASE),
    re.compile(r'do[^\n]*not[^\n]*sell', re.IGNORECASE),
    re.compile(r'object[^\n]*to[^\n]*sharing', re.IGNORECASE),
    re.compile(r'withdraw[^\n]*consent', re.IGNORECASE),
]


def extract_urls_from_html(html_content: str) -> list[str]:
    """Extract all URLs from HTML content."""
    urls = []
    
    # Extract href attributes
    href_pattern = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    for match in href_pattern.finditer(html_content):
        url = match.group(1).strip()
        if url.startswith(('http://', 'https://')):
            urls.append(url)
    
    # Extract action attributes from forms
    action_pattern = re.compile(r'action\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    for match in action_pattern.finditer(html_content):
        url = match.group(1).strip()
        if url.startswith(('http://', 'https://')):
            urls.append(url)
    
    return list(set(urls))


def extract_urls_from_text(text_content: str) -> list[str]:
    """Extract URLs from plain text content."""
    urls = []
    
    # Match URL patterns in text
    url_pattern = re.compile(
        r'https?://[^\s<>"\')\]}]+',
        re.IGNORECASE,
    )
    for match in url_pattern.finditer(text_content):
        url = match.group(0).rstrip(".)';:!?>")
        urls.append(url)
    
    return list(set(urls))


def classify_url_as_opt_out(url: str, context_text: str = "") -> bool:
    """Classify whether a URL is likely an opt-out/removal link."""
    # Check URL path for opt-out keywords
    parsed = urlparse(url)
    path_lower = (parsed.path + parsed.query).lower()
    
    opt_out_keywords = [
        'opt-out', 'optout', 'opt_out',
        'remove', 'removal', 'unlist',
        'privacy', 'do-not-sell', 'dns',
        'delete', 'deactivate',
        'object', 'consent',
    ]
    
    for keyword in opt_out_keywords:
        if keyword in path_lower:
            return True
    
    # Check surrounding context text
    if context_text:
        for pattern in OPT_OUT_PATTERNS:
            if pattern.search(context_text):
                return True
    
    return False


def get_context_around_url(html_content: str, url: str, window: int = 200) -> str:
    """Get the text context around a URL in HTML content."""
    # Strip HTML tags for context extraction
    clean_text = re.sub(r'<[^>]+>', ' ', html_content)
    
    url_path = urlparse(url).path
    idx = clean_text.find(url_path)
    if idx == -1:
        idx = clean_text.find(url)
    
    if idx == -1:
        return ""
    
    start = max(0, idx - window)
    end = min(len(clean_text), idx + len(url_path) + window)
    
    return clean_text[start:end].strip()


def extract_opt_out_links(html_content: str, text_content: str = "") -> list[dict]:
    """Extract and classify opt-out/removal links from email content.
    
    Args:
        html_content: HTML body of the email
        text_content: Plain text body of the email (fallback)
    
    Returns:
        List of dicts with 'url', 'confidence', and 'context' keys.
    """
    results = []
    
    # Extract URLs from both HTML and text
    html_urls = extract_urls_from_html(html_content)
    text_urls = extract_urls_from_text(text_content or "")
    all_urls = list(set(html_urls + text_urls))
    
    for url in all_urls:
        # Get context around the URL
        context = get_context_around_url(html_content, url)
        
        # Classify the URL
        is_opt_out = classify_url_as_opt_out(url, context)
        
        if is_opt_out:
            # Calculate confidence based on signals
            confidence = 0.5
            
            # URL path contains opt-out keywords
            parsed = urlparse(url)
            path_lower = (parsed.path + parsed.query).lower()
            if any(kw in path_lower for kw in ['opt-out', 'optout', 'remove', 'privacy']):
                confidence += 0.3
            
            # Context contains opt-out patterns
            if context:
                for pattern in OPT_OUT_PATTERNS:
                    if pattern.search(context):
                        confidence += 0.2
                        break
            
            confidence = min(confidence, 1.0)
            
            results.append({
                "url": url,
                "confidence": round(confidence, 2),
                "context": context[:500],  # Limit context length
            })
    
    # Sort by confidence descending
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    logger.info("extract_opt_out_links found %d candidates", len(results))
    return results


def extract_broker_domain(url: str) -> Optional[str]:
    """Extract the broker domain from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.hostname.lower() if parsed.hostname else None
    except Exception:
        return None


def normalize_opt_out_url(url: str) -> str:
    """Normalize an opt-out URL for storage/comparison."""
    try:
        parsed = urlparse(url)
        # If no scheme detected, return as-is (invalid URL)
        if not parsed.scheme or not parsed.netloc:
            return url
        # Remove tracking parameters
        query_params = dict(re.findall(r'([^&=]+)=([^&]*)', parsed.query))
        # Keep only essential parameters
        essential = {k: v for k, v in query_params.items() 
                     if not k.startswith(('utm_', 'fbclid', 'gclid', 'ref'))}
        # Rebuild URL
        new_query = '&'.join(f'{k}={v}' for k, v in essential.items())
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if new_query:
            normalized += f"?{new_query}"
        return normalized
    except Exception:
        return url
