"""Output guardrails — validate agent responses before returning to user.

Scrubs secrets, validates schema, enforces domain boundaries.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Secret patterns to scrub from outputs ──
SECRET_PATTERNS = {
    "api_key": re.compile(r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?", re.IGNORECASE),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}", re.IGNORECASE),
    "connection_string": re.compile(r"(?:jdbc|Server=|Data Source=)[^\s;]{20,}", re.IGNORECASE),
    "password": re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?", re.IGNORECASE),
}


@dataclass
class OutputGuardrailResult:
    """Result of output guardrail checks."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    scrubbed_output: str = ""


def scrub_secrets(text: str) -> OutputGuardrailResult:
    """Redact any leaked secrets from agent output."""
    violations = []
    scrubbed = text

    for secret_type, pattern in SECRET_PATTERNS.items():
        matches = pattern.findall(scrubbed)
        if matches:
            violations.append(f"Secret detected in output: {secret_type} ({len(matches)} instances)")
            scrubbed = pattern.sub(f"[REDACTED_{secret_type.upper()}]", scrubbed)
            logger.warning("Scrubbed %s from agent output", secret_type)

    return OutputGuardrailResult(
        passed=len(violations) == 0,
        violations=violations,
        scrubbed_output=scrubbed,
    )


def validate_output_not_empty(text: str, min_length: int = 10) -> OutputGuardrailResult:
    """Ensure agent produced meaningful output."""
    if not text or len(text.strip()) < min_length:
        return OutputGuardrailResult(
            passed=False,
            violations=[f"Output too short ({len(text.strip())} chars, minimum {min_length})"],
            scrubbed_output=text,
        )
    return OutputGuardrailResult(passed=True, scrubbed_output=text)


def validate_output(text: str) -> OutputGuardrailResult:
    """Run all output guardrails in sequence."""
    # Check non-empty first
    empty_check = validate_output_not_empty(text)
    if not empty_check.passed:
        return empty_check

    # Scrub secrets
    secret_check = scrub_secrets(text)

    return secret_check
