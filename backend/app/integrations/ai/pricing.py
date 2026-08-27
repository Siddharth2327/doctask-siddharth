"""Token-cost estimation.

Prices are USD per 1,000 tokens and are necessarily a point-in-time
snapshot -- providers change pricing periodically. This is a best-
effort estimate for cost visibility, not a billing-grade calculation.
Unknown models (including the mock/deterministic providers used in
tests and the demo) always cost 0.0 rather than raising, so this never
breaks a run.
"""

# (input_price_per_1k, output_price_per_1k)
_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4.1": (0.002, 0.008),
    "gpt-4.1-mini": (0.0004, 0.0016),
    "gpt-4.1-nano": (0.0001, 0.0004),
    # Anthropic
    "claude-opus-4-8": (0.015, 0.075),
    "claude-sonnet-5": (0.003, 0.015),
    "claude-haiku-4-5": (0.0008, 0.004),
    # Gemini
    "gemini-2.5-pro": (0.00125, 0.005),
    "gemini-2.5-flash": (0.0003, 0.0025),
    "gemini-2.5-flash-lite": (0.0001, 0.0004),
}


def estimate_cost(model: str, *, input_tokens: int, output_tokens: int) -> float:
    """Best-effort USD cost for one call. Returns 0.0 for unknown models
    (this deliberately includes "mock-model" and "deterministic-v1")."""

    pricing = _PRICING.get(model)

    if pricing is None:
        # Fall back to a prefix match so dated/suffixed model names
        # ("gpt-4o-mini-2026-08-01") still resolve to their base
        # pricing. Longest prefix wins so more specific model names
        # (e.g. "gpt-4o-mini") are preferred over shorter ones that
        # also happen to match (e.g. "gpt-4o").
        candidates = [
            known_model
            for known_model in _PRICING
            if model.startswith(known_model)
        ]

        if candidates:
            best_match = max(candidates, key=len)
            pricing = _PRICING[best_match]

    if pricing is None:
        return 0.0

    input_price, output_price = pricing

    return round(
        (input_tokens / 1000) * input_price
        + (output_tokens / 1000) * output_price,
        6,
    )
