import json
from collections.abc import Iterator

from app.llm.base import LLMProvider

UNSUPPORTED = "I couldn't find enough information in your documents to answer this reliably."


class MockProvider(LLMProvider):
    """Deterministic provider for tests and offline development. Not a fake product demo path
    unless LLM_PROVIDER=mock is set explicitly."""

    def generate(self, *, system: str, user: str, json_mode: bool = False) -> str:
        lowered = user.lower()
        if json_mode and "action" in system.lower() + user.lower() and "priority" in lowered:
            return json.dumps(
                {
                    "items": [
                        {
                            "task": "Review retrieved requirements",
                            "description": "Follow up on items mentioned in the provided context.",
                            "priority": "Medium",
                            "deadline": None,
                            "source": "retrieved context",
                        }
                    ]
                }
            )
        if json_mode and ("people" in lowered or "insights" in lowered or "extract" in system.lower()):
            return json.dumps(
                {
                    "people": [{"value": "Alex Rivera", "source": "context"}],
                    "organizations": [{"value": "Northwind Labs", "source": "context"}],
                    "dates": [],
                    "amounts": [],
                    "technologies": [{"value": "OAuth 2.0", "source": "context"}],
                    "requirements": [],
                    "deadlines": [],
                    "risks": [],
                    "action_items": [],
                }
            )
        if json_mode and ("overview" in lowered or "executive" in system.lower() or "summary" in lowered):
            return json.dumps(
                {
                    "overview": "Summary generated from retrieved document context.",
                    "key_points": ["Point derived from context."],
                    "important_findings": [],
                    "important_numbers": [],
                    "risks": [],
                    "recommendations": ["Review the source document for details."],
                }
            )
        if json_mode and ("similarities" in lowered or "compare" in lowered):
            return json.dumps(
                {
                    "sections": [
                        {"category": "Key similarities", "details": "Both documents discuss related topics."},
                        {"category": "Key differences", "details": "Details differ in the retrieved excerpts."},
                        {"category": "Added information", "details": "See document B excerpts."},
                        {"category": "Removed information", "details": "See document A excerpts."},
                        {"category": "Contradictions", "details": "None identified in the provided context."},
                        {"category": "Important changes", "details": "Scope or wording may differ."},
                    ],
                    "summary": "Comparison based only on retrieved chunks.",
                }
            )
        if "context:" in lowered and "no retrieved" not in lowered:
            if "unsupported-eval-question" in lowered:
                return UNSUPPORTED
            return "Based on the retrieved context [1], the documents describe the requested topic."
        return UNSUPPORTED

    def stream(self, *, system: str, user: str) -> Iterator[str]:
        yield self.generate(system=system, user=user)
