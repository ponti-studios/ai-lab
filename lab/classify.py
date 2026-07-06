"""Essay classification pipeline — LLM-powered domain classification.

Three-pass pipeline:
  Pass 1 — fingerprint: scan markdown files, extract features
  Pass 2 — classify: LLM-powered domain classification via OpenAI-compatible API
  Pass 3 — move plan: generate target paths from classifications
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import openai

MAX_INTRO_WORDS = 500
STOP_WORDS = {
    "the",
    "and",
    "with",
    "that",
    "this",
    "from",
    "have",
    "will",
    "your",
    "into",
    "more",
    "are",
    "not",
    "but",
    "for",
    "what",
    "can",
    "all",
    "was",
    "one",
    "its",
}

DEFAULT_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

CLASSIFY_SYSTEM_PROMPT = """You are an expert content classifier. Given a markdown essay, classify it into
1-3 domain tags that describe its primary subject matter. Use lowercase kebab-case
tags like "rust-programming", "product-strategy", "personal-journal", "ai-research".

Respond ONLY with a JSON object:
{
  "domains": ["primary", "secondary", "tertiary"],
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "needs_review": true/false
}

Rules:
- Domains should be descriptive, not generic. Prefer "postgres-tuning" over "database".
- If the content spans multiple equal-weighted topics, list up to 3.
- Set needs_review=true if the content is ambiguous, very short, or doesn't fit clear domains.
- confidence = how sure you are about the primary domain classification."""


@dataclass
class Fingerprint:
    id: str
    filename: str
    relative_path: str
    title: str
    headings: list[str]
    intro_excerpt: str
    keywords: list[str]
    word_count: int


@dataclass
class Classification:
    id: str
    domains: list[str]
    confidence: float
    reasoning: str
    needs_review: bool


@dataclass
class MoveEntry:
    id: str
    source: str
    target: str
    domain: str
    confidence: float
    reason: str


def _count_words(s: str) -> int:
    in_word = False
    count = 0
    for ch in s:
        if ch.isalnum() or ch == "-":
            if not in_word and ch.isalpha():
                count += 1
                in_word = True
        else:
            in_word = False
    return count


def _extract_title(content: str) -> str:
    for line in content.splitlines()[:10]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _extract_headings(content: str) -> list[str]:
    return [
        line.strip()[3:].strip()
        for line in content.splitlines()
        if line.strip().startswith("## ")
    ]


def _extract_intro(content: str) -> str:
    out: list[str] = []
    words = 0
    in_code = False
    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not trimmed or trimmed.startswith("#"):
            continue
        wc = _count_words(line)
        if words + wc > MAX_INTRO_WORDS:
            break
        out.append(trimmed)
        words += wc
    return "\n".join(out)


def _extract_keywords(content: str) -> list[str]:
    tokens: list[str] = []
    for token in content.split():
        token = "".join(c for c in token.lower() if c.isalnum() or c == "-")
        if len(token) < 4 or token in STOP_WORDS:
            continue
        tokens.append(token)
    freq = Counter(tokens)
    return [word for word, count in freq.most_common(15) if count >= 2]


def scan_directory(root: Path) -> list[Fingerprint]:
    """Scan a directory tree for markdown files and create fingerprints."""
    root = root.resolve()
    files = sorted(
        p for p in root.rglob("*.md") if ".filekit" not in p.parts and p.is_file()
    )

    fingerprints: list[Fingerprint] = []
    for idx, path in enumerate(files):
        content = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(root))
        fingerprints.append(
            Fingerprint(
                id=f"essay_{idx:04d}",
                filename=path.name,
                relative_path=rel,
                title=_extract_title(content),
                headings=_extract_headings(content),
                intro_excerpt=_extract_intro(content),
                keywords=_extract_keywords(content),
                word_count=_count_words(content),
            )
        )
    return fingerprints


def _build_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> openai.OpenAI:
    """Build an OpenAI-compatible client from env vars or explicit config."""
    # Load .env if not already done (safe no-op if already loaded)
    try:
        from dotenv import load_dotenv as _load  # noqa: F811

        _load()
    except ImportError:
        pass

    key = (
        api_key
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENAI_API_KEY", "")
    )
    url = base_url or os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL)
    if not key:
        raise ValueError(
            "No API key provided. Set OPENAI_API_KEY env var or pass --api-key."
        )
    return openai.OpenAI(api_key=key, base_url=url)


def _classify_essay(
    client: openai.OpenAI,
    fp: Fingerprint,
    model: str,
) -> Classification:
    """Classify a single essay using an LLM."""
    prompt = f"""Title: {fp.title or "(untitled)"}
Filename: {fp.filename}
Headings: {", ".join(fp.headings[:5]) if fp.headings else "(none)"}
Keywords: {", ".join(fp.keywords[:10]) if fp.keywords else "(none)"}
Word count: {fp.word_count}

Content excerpt:
{fp.intro_excerpt[:2000]}"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=300,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    if not raw:
        return Classification(
            id=fp.id,
            domains=["unclassified"],
            confidence=0.0,
            reasoning="LLM returned empty response",
            needs_review=True,
        )

    try:
        data = json.loads(raw)
        return Classification(
            id=fp.id,
            domains=data.get("domains", ["unclassified"]),
            confidence=float(data.get("confidence", 0.0)),
            reasoning=str(data.get("reasoning", "")),
            needs_review=bool(data.get("needs_review", False)),
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return Classification(
            id=fp.id,
            domains=["unclassified"],
            confidence=0.0,
            reasoning=f"Failed to parse LLM response: {raw[:200]}",
            needs_review=True,
        )


def classify_essays(
    fingerprints: list[Fingerprint],
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
) -> list[Classification]:
    """Classify a batch of essays using an LLM."""
    client = _build_client(api_key=api_key, base_url=base_url)
    results: list[Classification] = []
    for i, fp in enumerate(fingerprints):
        try:
            classification = _classify_essay(client, fp, model)
        except Exception as exc:
            classification = Classification(
                id=fp.id,
                domains=["error"],
                confidence=0.0,
                reasoning=f"LLM call failed: {exc}",
                needs_review=True,
            )
        results.append(classification)
        if (i + 1) % 10 == 0:
            print(f"  Classified {i + 1}/{len(fingerprints)}...")
    return results


def generate_move_plan(
    fingerprints: list[Fingerprint],
    classifications: list[Classification],
) -> list[MoveEntry]:
    """Generate a move plan from classifications."""
    fp_map = {fp.id: fp for fp in fingerprints}
    plan: list[MoveEntry] = []
    for c in classifications:
        fp = fp_map.get(c.id)
        if not fp:
            continue
        domain = c.domains[0] if c.domains else "unclassified"
        target = str(Path(domain) / fp.filename)
        plan.append(
            MoveEntry(
                id=c.id,
                source=fp.relative_path,
                target=target,
                domain=domain,
                confidence=c.confidence,
                reason=c.reasoning,
            )
        )
    return plan


def run_pipeline(
    target_dir: Path,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
    execute: bool = False,
    assume_yes: bool = False,
    resume: bool = False,
    from_pass: int | None = None,
) -> dict:
    """Run the LLM-powered classification pipeline.

    Returns a dict with keys: fingerprints, classifications, move_plan.
    """
    state_dir = target_dir / ".filekit" / "classify"
    state_dir.mkdir(parents=True, exist_ok=True)

    pass1_path = state_dir / "pass1_fingerprints.json"
    pass2_path = state_dir / "pass2_classifications.json"
    pass3_path = state_dir / "move_plan.json"

    start_pass = from_pass or (2 if resume else 1)
    start_pass = max(1, min(start_pass, 3))

    # Pass 1: Fingerprint
    if start_pass > 1 and pass1_path.exists():
        raw = json.loads(pass1_path.read_text())
        fingerprints = [Fingerprint(**fp) for fp in raw["fingerprints"]]
        print(f"Resumed: loaded {len(fingerprints)} fingerprints")
    else:
        fingerprints = scan_directory(target_dir)
        pass1_path.write_text(
            json.dumps({"fingerprints": [fp.__dict__ for fp in fingerprints]}, indent=2)
        )
        print(f"Pass 1: scanned {len(fingerprints)} essays")

    # Pass 2: LLM Classification
    if start_pass > 2 and pass2_path.exists():
        raw = json.loads(pass2_path.read_text())
        classifications = [Classification(**c) for c in raw]
        print(f"Resumed: loaded {len(classifications)} classifications")
    else:
        print(f"Pass 2: classifying {len(fingerprints)} essays via {model}...")
        classifications = classify_essays(
            fingerprints,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        pass2_path.write_text(
            json.dumps([c.__dict__ for c in classifications], indent=2)
        )
        domains = Counter(d for c in classifications for d in c.domains)
        print(
            f"  Discovered {len(domains)} domains: {', '.join(d for d, _ in domains.most_common(10))}"
        )

    # Pass 3: Move Plan
    if start_pass > 3 and pass3_path.exists():
        raw = json.loads(pass3_path.read_text())
        move_plan = [MoveEntry(**m) for m in raw]
        print(f"Resumed: loaded {len(move_plan)} move plan entries")
    else:
        move_plan = generate_move_plan(fingerprints, classifications)
        pass3_path.write_text(json.dumps([m.__dict__ for m in move_plan], indent=2))
        print(f"Pass 3: generated {len(move_plan)} move plan entries")

    needs_review = sum(1 for c in classifications if c.needs_review)
    all_domains = Counter(d for c in classifications for d in c.domains)

    result = {
        "fingerprints": len(fingerprints),
        "classifications": len(classifications),
        "needs_review": needs_review,
        "domains": dict(all_domains.most_common()),
        "move_plan": len(move_plan),
    }

    if execute:
        _execute_move(target_dir, move_plan, assume_yes)
        result["executed"] = True

    # Persist to lab database (best-effort, never kills the pipeline)
    try:
        _save_to_db(fingerprints, classifications, model)
    except Exception as exc:
        print(f"  Warning: failed to persist to lab.db: {exc}")

    return result


def _save_to_db(
    fingerprints: list[Fingerprint],
    classifications: list[Classification],
    model: str,
) -> None:
    """Persist classification results to the lab database."""
    from lab.db import connect, save_classification

    fp_map = {fp.id: fp for fp in fingerprints}
    conn = connect()
    try:
        for c in classifications:
            fp = fp_map.get(c.id)
            if not fp:
                continue
            save_classification(
                conn,
                filename=fp.filename,
                relative_path=fp.relative_path,
                title=fp.title,
                word_count=fp.word_count,
                domains=c.domains,
                confidence=c.confidence,
                reasoning=c.reasoning,
                needs_review=c.needs_review,
                model_id=model,
            )
        print(f"  Saved {len(classifications)} classifications to lab.db")
    finally:
        conn.close()


def _execute_move(source_dir: Path, plan: list[MoveEntry], assume_yes: bool) -> None:
    """Execute a move plan by renaming files."""
    if not plan:
        print("No move plan entries to execute.")
        return

    print(f"\nExecuting move plan: {len(plan)} files")
    if not assume_yes:
        response = input("Execute? [y/N] ").strip().lower()
        if response not in ("y", "yes"):
            print("Aborted.")
            return

    moved = 0
    failed = 0
    for entry in plan:
        source = source_dir / entry.source
        target = source_dir / entry.target
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.rename(source, target)
            moved += 1
            print(f"  MOVED: {source} -> {target}")
        except OSError as err:
            failed += 1
            print(f"  FAILED: {source} -> {target}: {err}")

    print(f"Done: {moved} moved, {failed} failed")
