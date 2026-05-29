import re

def redact_pii(text: str) -> str:
    """
    A basic PII redaction utility using heuristics/regex to mask out potential identifiers 
    before sending the transcript to an external LLM.
    """
    # Redact obvious phone numbers
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    text = re.sub(phone_pattern, '[PHONE REDACTED]', text)
    
    # Redact potential Social Security Numbers
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    text = re.sub(ssn_pattern, '[SSN REDACTED]', text)
    
    # Redact emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    text = re.sub(email_pattern, '[EMAIL REDACTED]', text)
    
    return text
