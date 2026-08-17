"""HR Policy Knowledge Retrieval Tools (OKF - Open Knowledge Format)."""
import os
import re
import yaml
from agents import config

RESERVED_FILES = {"index.md", "log.md"}
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

_FILE_CACHE = {}
_CONCEPTS_CACHE = None


def _parse_file(path: str):
    """Read a markdown file and separate frontmatter dict from body text (cached)."""
    if path in _FILE_CACHE:
        return _FILE_CACHE[path]

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    match = FRONTMATTER_RE.match(text)
    if not match:
        _FILE_CACHE[path] = ({}, text)
        return {}, text

    raw_frontmatter = match.group(1)
    body = text[match.end():]
    try:
        data = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError:
        data = {}
    _FILE_CACHE[path] = (data, body)
    return data, body


def list_concepts() -> dict:
    """List the available policy concepts and domains in the Knowledge Base.

    Returns:
        {"concepts": [{"id": str, "title": str, "description": str}, ...]}
        where `id` is the concept path, e.g. "01-paid-time-off-leave-operations/1.1-outpatient-sick-time-hospitalization-leave-singapore".
    """
    global _CONCEPTS_CACHE
    if _CONCEPTS_CACHE is not None:
        return _CONCEPTS_CACHE

    concepts = []
    knowledge_dir = os.path.abspath(config.KNOWLEDGE_DIR)

    if not os.path.exists(knowledge_dir):
        return {"concepts": [], "error": f"Knowledge directory not found: {knowledge_dir}"}

    for dirpath, _dirnames, filenames in os.walk(knowledge_dir):
        for fname in sorted(filenames):
            if not fname.endswith(".md") or fname in RESERVED_FILES:
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, knowledge_dir)
            concept_id = rel_path[:-3]  # strip .md

            meta, _body = _parse_file(full_path)
            title = meta.get("title") or fname[:-3].replace("-", " ").title()
            description = meta.get("description") or ""

            concepts.append({
                "id": concept_id,
                "title": title,
                "description": description
            })

    _CONCEPTS_CACHE = {"concepts": concepts}
    return _CONCEPTS_CACHE


def read_concept(concept_id: str) -> dict:
    """Read the full policy text and metadata for a specific concept ID.

    Args:
        concept_id: The identifier returned by list_concepts (e.g., "01-paid-time-off-leave-operations/1.1-outpatient-sick-time-hospitalization-leave-singapore")

    Returns:
        {"id": str, "title": str, "body": str, "source": str} or {"error": str}
    """
    knowledge_dir = os.path.abspath(config.KNOWLEDGE_DIR)
    target_path = os.path.join(knowledge_dir, f"{concept_id}.md")

    if not os.path.exists(target_path):
        return {"error": f"Concept '{concept_id}' not found in knowledge base."}

    meta, body = _parse_file(target_path)
    title = meta.get("title", concept_id)
    source_url = meta.get("source_url", f"policy://{concept_id}")

    return {
        "id": concept_id,
        "title": title,
        "body": body,
        "citation": {
            "title": title,
            "url": source_url,
            "concept_id": concept_id
        }
    }
