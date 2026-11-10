"""Source-level regression checks for the opt-in Cracked guidance bridge."""
import asyncio
import json

import pytest

from app.cracked_suite import CoachRequest, FEATURES, INDEX, ROOT, coach, feature_catalog


def test_all_nineteen_skills_have_imported_sources():
    catalog = feature_catalog()
    assert len(FEATURES) == len(catalog) == len(INDEX) == 19
    assert len({item["id"] for item in catalog}) == 19
    for item in catalog:
        source = ROOT / item["group"] / item["id"] / "SKILL.md"
        assert source.is_file(), source
        assert source.read_text(encoding="utf-8").startswith("---\n")
        assert item["integration"] in {"guided-only", "related-native", "requires-executor"}


def test_coach_context_and_consent_are_bounded():
    with pytest.raises(Exception):
        CoachRequest(skill="pattern-coach", context="short")
    req = CoachRequest(skill="pattern-coach", context="Discuss an approach to two pointers.")
    assert not req.consent
    with pytest.raises(ValueError, match="Consent"):
        asyncio.run(coach(FakeProvider(), req))


class FakeProvider:
    def __init__(self):
        self.last = None
    def configured(self):
        return True
    def _select_model(self, name):
        return name
    async def _post(self, path, **kwargs):
        self.last = (path, kwargs)
        return {
            "choices": [{
                "message": {"content": json.dumps({
                    "response": "Explain the invariant before coding.",
                    "suggestions": ["Draw a small example."],
                    "limitations": ["No code was executed."]
                })}
            }]
        }


def test_guided_coach_does_not_claim_tool_execution():
    provider = FakeProvider()
    request = CoachRequest(
        skill="mock-interview",
        context="I want a DSA interview for a backend internship.",
        company="Example",
        consent=True,
    )
    result = asyncio.run(coach(provider, request))
    assert result["method"] == "model-guidance-only"
    assert result["executed_code"] is False
    assert result["external_sources_checked"] is False
    assert provider.last[0] == "chat/completions"
    system = provider.last[1]["json"]["messages"][0]["content"]
    assert "NO filesystem, terminal, compiler" in system
    assert "Never grade code you did not execute" in system


def test_unknown_skill_cannot_load_arbitrary_path():
    provider = FakeProvider()
    request = CoachRequest(
        skill="../outside", context="A valid sufficiently long request.",
        consent=True,
    )
    with pytest.raises(ValueError, match="Unknown skill"):
        asyncio.run(coach(provider, request))
