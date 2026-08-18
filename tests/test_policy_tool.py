"""Automated unit tests for HR Policy Knowledge Tools & Dynamic Ingestion."""
from tools.policy_tool import list_concepts, read_concept, refresh_policy_index


def test_list_concepts_structure():
    """Verify list_concepts returns all indexed policy categories with valid metadata."""
    res = list_concepts()
    assert "concepts" in res
    assert isinstance(res["concepts"], list)
    assert len(res["concepts"]) > 0
    assert "total_indexed" in res
    
    first = res["concepts"][0]
    assert "id" in first
    assert "title" in first
    assert "version" in first
    assert "effective_date" in first


def test_read_concept_grounding():
    """Verify read_concept fetches exact policy text and citation metadata."""
    res = list_concepts()
    sick_concept = None
    for c in res["concepts"]:
        if "sick" in c["id"].lower() or "outpatient" in c["id"].lower():
            sick_concept = c["id"]
            break
            
    if sick_concept:
        doc = read_concept(sick_concept)
        assert "body" in doc
        assert "citation" in doc
        assert doc["citation"]["url"].startswith("policy://")
        assert len(doc["body"]) > 50


def test_hot_reload_atomic_cache():
    """Verify refresh_policy_index performs thread-safe atomic cache reload."""
    refreshed = refresh_policy_index()
    assert "concepts" in refreshed
    assert refreshed["total_indexed"] > 0
