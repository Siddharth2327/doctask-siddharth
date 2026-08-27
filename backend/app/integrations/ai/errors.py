class AIProviderError(Exception):
    """Base error for all AI provider failures."""


class AIAuthenticationError(AIProviderError):
    """Provider authentication failed."""


class AIRateLimitError(AIProviderError):
    """Provider rate limit was exceeded."""


class AITimeoutError(AIProviderError):
    """Provider request timed out."""


class AIInvalidRequestError(AIProviderError):
    """Provider rejected the request."""


class AIStructuredOutputError(AIProviderError):
    """Provider returned invalid structured output."""


class AIUnavailableError(AIProviderError):
    """Provider is temporarily unavailable."""


class AIUnknownProviderError(AIProviderError):
    """Requested provider is not configured or supported."""


class AIOutputValidationError(AIProviderError):
    """AI output failed application-level schema validation."""