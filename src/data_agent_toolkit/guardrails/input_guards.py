"""Input guardrails — validate and sanitize before agent execution.

Defense-in-depth: deterministic checks first (cheap, fast),
then model-based checks second (expensive, thorough).

Layer 1: Length/format validation (regex)
Layer 2: PII detection (presidio or regex fallback)
Layer 3: Prompt injection detection (pattern matching)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Common PII patterns (regex fallback when presidio unavailable) ──
PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone_us": re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
}

# ── Prompt injection indicators ──
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"```\s*system", re.IGNORECASE),
]


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    sanitized_input: str = ""


def check_input_length(text: str, max_length: int = 10000) -> GuardrailResult:
    """Reject inputs that exceed maximum length."""
    if len(text) > max_length:
        return GuardrailResult(
            passed=False,
            violations=[f"Input length {len(text)} exceeds maximum {max_length}"],
        )
    return GuardrailResult(passed=True, sanitized_input=text)


def detect_pii(text: str) -> GuardrailResult:
    """Detect PII patterns in input text.

    Uses regex patterns as fallback. In production, install
    presidio-analyzer for more comprehensive detection.
    """
    violations = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            violations.append(f"Detected {pii_type}: {len(matches)} instance(s)")
            logger.warning("PII detected in input: %s (%d instances)", pii_type, len(matches))

    return GuardrailResult(
        passed=len(violations) == 0,
        violations=violations,
        sanitized_input=text,
    )


def detect_prompt_injection(text: str) -> GuardrailResult:
    """Detect common prompt injection patterns."""
    violations = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            violations.append(f"Potential prompt injection detected: {pattern.pattern}")
            logger.warning("Prompt injection attempt detected")

    return GuardrailResult(
        passed=len(violations) == 0,
        violations=violations,
        sanitized_input=text,
    )


def validate_input(text: str, max_length: int = 10000) -> GuardrailResult:
    """Run all input guardrails in sequence.

    Deterministic checks first (length, PII, injection),
    then returns combined result.
    """
    # Layer 1: Length
    length_check = check_input_length(text, max_length)
    if not length_check.passed:
        return length_check

    # Layer 2: PII detection
    pii_check = detect_pii(text)

    # Layer 3: Prompt injection
    injection_check = detect_prompt_injection(text)

    # Combine results
    all_violations = pii_check.violations + injection_check.violations
    return GuardrailResult(
        passed=len(all_violations) == 0,
        violations=all_violations,
        sanitized_input=text,
    )
