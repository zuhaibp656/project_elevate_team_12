"""HR Policy Knowledge Retrieval Tools (OKF - Open Knowledge Format) with Dynamic Real-Time Indexing."""
import os
import re
import yaml
from agents import config

RESERVED_FILES = {"index.md", "log.md"}
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

_FILE_CACHE = {}
_CONCEPTS_CACHE = None
_LAST_DIR_MTIME = 0


def _get_dir_mtime(directory: str) -> float:
    """Calculate the latest modification time across all policy files in the directory."""
    latest = 0.0
    if not os.path.exists(directory):
        return latest
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".md"):
                try:
                    m = os.path.getmtime(os.path.join(root, f))
                    if m > latest:
                        latest = m
                except OSError:
                    pass
    return latest


def refresh_policy_index() -> dict:
    """Force refresh the policy concept index and clear in-memory caches.
    
    Used by event-driven GCS sync triggers or when policies are modified at runtime.
    """
    global _FILE_CACHE, _CONCEPTS_CACHE, _LAST_DIR_MTIME
    _FILE_CACHE.clear()
    _CONCEPTS_CACHE = None
    _LAST_DIR_MTIME = 0.0
    return list_concepts()


def _parse_file(path: str):
    """Read a markdown file and separate frontmatter dict from body text (with mtime auto-invalidation)."""
    current_mtime = os.path.getmtime(path) if os.path.exists(path) else 0.0
    if path in _FILE_CACHE:
        cached_mtime, data, body = _FILE_CACHE[path]
        if cached_mtime == current_mtime:
            return data, body

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    match = FRONTMATTER_RE.match(text)
    if not match:
        _FILE_CACHE[path] = (current_mtime, {}, text)
        return {}, text

    raw_frontmatter = match.group(1)
    body = text[match.end():]
    try:
        data = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError:
        data = {}
    _FILE_CACHE[path] = (current_mtime, data, body)
    return data, body


def list_concepts() -> dict:
    """List the available policy concepts and domains in the Knowledge Base with dynamic hot-reload.

    Returns:
        {"concepts": [{"id": str, "title": str, "description": str, "version": str, "effective_date": str}, ...]}
    """
    global _CONCEPTS_CACHE, _LAST_DIR_MTIME
    knowledge_dir = os.path.abspath(config.KNOWLEDGE_DIR)

    if not os.path.exists(knowledge_dir):
        return {"concepts": [], "error": f"Knowledge directory not found: {knowledge_dir}"}

    current_mtime = _get_dir_mtime(knowledge_dir)
    if _CONCEPTS_CACHE is not None and current_mtime == _LAST_DIR_MTIME:
        return _CONCEPTS_CACHE

    concepts = []
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
            version = meta.get("version", "2026.1")
            effective_date = meta.get("effective_date", "2026-01-01")

            concepts.append({
                "id": concept_id,
                "title": title,
                "description": description,
                "version": version,
                "effective_date": effective_date
            })

    _CONCEPTS_CACHE = {"concepts": concepts, "total_indexed": len(concepts), "last_synced_mtime": current_mtime}
    _LAST_DIR_MTIME = current_mtime
    return _CONCEPTS_CACHE


def read_concept(concept_id: str) -> dict:
    """Read the full policy text and metadata for a specific concept ID.

    Args:
        concept_id: The identifier returned by list_concepts (e.g., "01-paid-time-off-leave-operations/1.1-outpatient-sick-time-hospitalization-leave-singapore")

    Returns:
        {"id": str, "title": str, "body": str, "citation": dict, "version": str, "effective_date": str} or {"error": str}
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
        "version": meta.get("version", "2026.1"),
        "effective_date": meta.get("effective_date", "2026-01-01"),
        "citation": {
            "title": title,
            "url": source_url,
            "concept_id": concept_id
        }
    }
