import re

from app.integrations.ai.base import AIProvider
from app.integrations.ai.models import AIRequest, AIResponse, AIUsage

FIELD_ALIASES = {
    "vendor": "vendor",
    "contract value": "contract_value",
    "start date": "start_date",
    "end date": "end_date",
    "renewal date": "renewal_date",
    "invoice amount": "invoice_amount",
    "status": "status",
}

LINE_RE = re.compile(r"^\s*([A-Za-z ]+?)\s*:\s*(.+?)\s*$")
DOCUMENT_ID_RE = re.compile(r"Document ID:\s*(\S+)")
DOCUMENT_VERSION_ID_RE = re.compile(r"Document Version ID:\s*(\S+)")


class DeterministicKeyValueAIProvider(AIProvider):
    """Extracts "Label: value" lines from document content as structured facts.

    This is deliberately a real, reusable AIProvider implementation
    (selectable via `ai_provider=deterministic`), not merely a demo
    helper: it satisfies T154 ("tests run without a live LLM API key",
    "deterministic fake model provider") while still producing
    genuinely different, content-dependent output per document --
    unlike MockAIProvider, which always returns one canned response
    regardless of input. It only understands the simple fixture
    format used by the Task 1 contract-register corpus
    (tests/fixtures/contract_corpus/); it is not a general-purpose
    extractor.
    """

    def generate(self, request: AIRequest) -> AIResponse:
        document_message = request.messages[-1]["content"]

        document_id_match = DOCUMENT_ID_RE.search(document_message)
        document_version_id_match = DOCUMENT_VERSION_ID_RE.search(
            document_message
        )

        document_id = (
            document_id_match.group(1) if document_id_match else "unknown"
        )
        document_version_id = (
            document_version_id_match.group(1)
            if document_version_id_match
            else "unknown"
        )

        content = document_message

        if "DOCUMENT CONTENT START" in content:
            content = content.split("DOCUMENT CONTENT START", 1)[1]
            content = content.split("DOCUMENT CONTENT END", 1)[0]

        facts = []

        for line_number, line in enumerate(content.splitlines(), start=1):
            match = LINE_RE.match(line)

            if not match:
                continue

            label = match.group(1).strip().lower()
            value = match.group(2).strip()
            field = FIELD_ALIASES.get(label)

            if not field or not value:
                continue

            facts.append(
                {
                    "field": field,
                    "value": value,
                    "confidence": 0.9,
                    "evidence": [
                        {
                            "document_id": document_id,
                            "document_version_id": document_version_id,
                            "location": f"line {line_number}",
                            "chunk_id": None,
                            "quote": line.strip(),
                        }
                    ],
                }
            )

        return AIResponse(
            content={"facts": facts},
            model=request.model,
            usage=AIUsage(
                input_tokens=len(content.split()),
                output_tokens=max(len(facts) * 5, 1),
            ),
        )
