def hallucination_classifier(text: str) -> bool:
    """Simple placeholder classifier for hallucination-like language."""
    suspicious_markers = ["certainly in stock", "100% guaranteed", "unverified"]
    normalized = text.lower()
    return any(marker in normalized for marker in suspicious_markers)
