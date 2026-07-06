"""Essay classification pipeline — ported from toolbox/apps/filekit/src/classify.rs.

Five-pass pipeline:
  Pass 1 — fingerprint: scan markdown files, extract features
  Pass 2 — embed: generate hash-based embeddings
  Pass 3 — cluster: single-pass cosine-distance clustering
  Pass 4 — classify: domain classification from title/keywords
  Pass 5 — move plan: generate target paths
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

MAX_INTRO_WORDS = 500
MAX_CLOSING_WORDS = 200
EMBEDDING_DIM = 16
STOP_WORDS = {
    "the", "and", "with", "that", "this", "from", "have",
    "will", "your", "into", "more", "are", "not", "but",
    "for", "what", "can", "all", "was", "one", "its",
}

DOMAIN_RULES: list[tuple[str, list[str]]] = [
    ("technology", ["rust", "go", "python", "cli", "api", "code", "software"]),
    ("science", ["research", "data", "model", "analysis", "experiment"]),
    ("writing", ["essay", "write", "writing", "draft", "prose"]),
    ("product", ["product", "roadmap", "feature", "workflow"]),
    ("design", ["design", "ui", "ux", "interface"]),
    ("business", ["business", "strategy", "market", "revenue"]),
    ("personal", ["journal", "personal", "life", "note"]),
]


@dataclass
class Fingerprint:
    id: str
    filename: str
    relative_path: str
    title: str
    headings: list[str]
    intro_excerpt: str
    closing_excerpt: str
    keywords: list[str]
    word_count: int


@dataclass
class Embedding:
    id: str
    vector: list[float]


@dataclass
class ClusterResult:
    id: str
    cluster_id: int
    is_outlier: bool
    distance: float


@dataclass
class Classification:
    id: str
    primary_domain: str
    secondary_domain: str | None = None
    confidence: float = 0.0
    reason: str = ""
    needs_full_text_review: bool = False


@dataclass
class MoveEntry:
    id: str
    source: str
    target: str
    domain: str
    confidence: float
    reason: str


def _count_words(s: str) -> int:
    """Count words in a string."""
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
    """Extract H1 title from markdown."""
    for line in content.splitlines()[:10]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _extract_headings(content: str) -> list[str]:
    """Extract H2 headings."""
    return [
        line.strip()[3:].strip()
        for line in content.splitlines()
        if line.strip().startswith("## ")
    ]


def _extract_intro(content: str) -> str:
    """Extract the opening text (first ~500 words, excluding headings and code)."""
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
    return " ".join(out)


def _extract_closing(content: str) -> str:
    """Extract the closing text (last ~200 words)."""
    out: list[str] = []
    words = 0
    for line in reversed(content.splitlines()):
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("`") or trimmed.startswith("#"):
            continue
        wc = _count_words(trimmed)
        if words + wc > MAX_CLOSING_WORDS:
            break
        out.append(trimmed)
        words += wc
    out.reverse()
    return " ".join(out)


def _extract_keywords(content: str) -> list[str]:
    """Extract top keywords by frequency (non-stopwords, minimum 4 chars)."""
    tokens: list[str] = []
    for token in content.split():
        token = "".join(c for c in token.lower() if c.isalnum() or c == "-")
        if len(token) < 4 or token in STOP_WORDS:
            continue
        tokens.append(token)
    freq = Counter(tokens)
    return [word for word, count in freq.most_common(20) if count >= 2]


# ── Pass 1: Scan & Fingerprint ──────────────────────────────────────────────

def scan_directory(root: Path) -> list[Fingerprint]:
    """Scan a directory tree for markdown files and create fingerprints."""
    root = root.resolve()
    files = sorted(
        p for p in root.rglob("*.md")
        if ".filekit" not in p.parts and p.is_file()
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
                closing_excerpt=_extract_closing(content),
                keywords=_extract_keywords(content),
                word_count=_count_words(content),
            )
        )
    return fingerprints


# ── Pass 2: Embed ────────────────────────────────────────────────────────────

def _build_embedding_text(fp: Fingerprint) -> str:
    parts = [fp.filename, fp.title]
    parts.extend(fp.headings)
    parts.append(fp.intro_excerpt)
    parts.append(fp.closing_excerpt)
    parts.extend(fp.keywords)
    return " ".join(parts)


def _build_embedding_vector(fp: Fingerprint) -> list[float]:
    """Generate a 16-dim hash-based embedding vector."""
    text = _build_embedding_text(fp)
    vec = [0.0] * EMBEDDING_DIM
    tokens = [t for t in text.split() if t]

    for i, token in enumerate(tokens):
        h = 0
        for b in token.encode():
            h = (h * 31 + b) & 0xFFFFFFFFFFFFFFFF
        idx = h % EMBEDDING_DIM
        vec[idx] += 1.0 + (i % 7) * 0.1

    # Normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]

    return vec


def generate_embeddings(fingerprints: list[Fingerprint]) -> list[Embedding]:
    return [
        Embedding(id=fp.id, vector=_build_embedding_vector(fp))
        for fp in fingerprints
    ]


# ── Pass 3: Cluster ─────────────────────────────────────────────────────────

def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Cosine distance between two vectors (1 - cosine similarity)."""
    length = min(len(a), len(b))
    if length == 0:
        return 1.0
    dot = sum(a[i] * b[i] for i in range(length))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 1.0
    return 1.0 - (dot / (na * nb))


def cluster_embeddings(
    embeddings: list[Embedding], threshold: float = 0.75
) -> list[ClusterResult]:
    """Single-pass clustering with cosine distance threshold."""
    results: list[ClusterResult] = []
    for i, emb in enumerate(embeddings):
        best_cluster = i
        best_distance = float("inf")
        for j in range(i):
            dist = _cosine_distance(emb.vector, embeddings[j].vector)
            if dist < best_distance:
                best_distance = dist
                best_cluster = results[j].cluster_id

        is_outlier = best_distance == float("inf") or best_distance > threshold
        results.append(
            ClusterResult(
                id=emb.id,
                cluster_id=-1 if is_outlier else best_cluster,
                is_outlier=is_outlier,
                distance=best_distance if best_distance != float("inf") else 0.0,
            )
        )
    return results


# ── Pass 4: Classify ────────────────────────────────────────────────────────

def _infer_domain(title: str, keywords: list[str], cluster_id: int) -> str:
    """Classify an essay into a domain using heuristic keyword rules."""
    haystack = f"{title.lower()} {' '.join(keywords).lower()}"
    for domain, terms in DOMAIN_RULES:
        if any(term in haystack for term in terms):
            return domain
    if cluster_id >= 0:
        return f"cluster-{cluster_id}"
    return "unclear"


def classify_essays(
    fingerprints: list[Fingerprint],
    clusters: list[ClusterResult],
    threshold: float = 0.75,
) -> list[Classification]:
    """Classify fingerprints using cluster data and domain heuristics."""
    fp_map = {fp.id: fp for fp in fingerprints}
    results: list[Classification] = []
    for cluster in clusters:
        fp = fp_map.get(cluster.id)
        title = fp.title if fp else ""
        keywords = fp.keywords if fp else []
        domain = _infer_domain(title, keywords, cluster.cluster_id)
        confidence = 0.35 if cluster.is_outlier else max(1.0 - cluster.distance, 0.0)
        results.append(
            Classification(
                id=cluster.id,
                primary_domain=domain,
                secondary_domain=None,
                confidence=confidence,
                reason="low cluster confidence"
                if cluster.is_outlier
                else "heuristic classification from title/keywords",
                needs_full_text_review=cluster.is_outlier or cluster.distance > threshold,
            )
        )
    return results


# ── Pass 5: Move Plan ───────────────────────────────────────────────────────

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
        domain = c.primary_domain or "unclear"
        target = str(Path(domain) / fp.filename)
        plan.append(
            MoveEntry(
                id=c.id,
                source=fp.relative_path,
                target=target,
                domain=domain,
                confidence=c.confidence,
                reason=c.reason,
            )
        )
    return plan


# ── Full Pipeline ────────────────────────────────────────────────────────────

def run_pipeline(
    target_dir: Path,
    *,
    threshold: float = 0.75,
    cluster_threshold: float = 0.75,
    execute: bool = False,
    assume_yes: bool = False,
    resume: bool = False,
    from_pass: int | None = None,
) -> dict:
    """Run the full 5-pass classification pipeline.

    Returns a dict with keys: fingerprints, embeddings, clusters, classifications, move_plan.
    """
    state_dir = target_dir / ".filekit" / "classify"
    state_dir.mkdir(parents=True, exist_ok=True)

    pass1_path = state_dir / "pass1_fingerprints.json"
    pass2_path = state_dir / "pass2_embeddings.json"
    pass3_path = state_dir / "pass3_clusters.json"
    pass4_path = state_dir / "pass4_classifications.json"
    pass5_path = state_dir / "move_plan.json"

    start_pass = from_pass or (2 if resume else 1)
    start_pass = max(1, min(start_pass, 5))

    # Pass 1: Fingerprint
    if start_pass > 1 and pass1_path.exists():
        raw = json.loads(pass1_path.read_text())
        fingerprints = [Fingerprint(**fp) for fp in raw["fingerprints"]]
    else:
        fingerprints = scan_directory(target_dir)
        pass1_path.write_text(
            json.dumps({"fingerprints": [fp.__dict__ for fp in fingerprints]}, indent=2)
        )

    # Pass 2: Embed
    if start_pass > 2 and pass2_path.exists():
        raw = json.loads(pass2_path.read_text())
        embeddings = [Embedding(**e) for e in raw["embeddings"]]
    else:
        embeddings = generate_embeddings(fingerprints)
        pass2_path.write_text(
            json.dumps({"embeddings": [e.__dict__ for e in embeddings]}, indent=2)
        )

    # Pass 3: Cluster
    if start_pass > 3 and pass3_path.exists():
        raw = json.loads(pass3_path.read_text())
        clusters = [ClusterResult(**c) for c in raw]
    else:
        clusters = cluster_embeddings(embeddings, cluster_threshold)
        pass3_path.write_text(
            json.dumps([c.__dict__ for c in clusters], indent=2)
        )

    # Pass 4: Classify
    if start_pass > 4 and pass4_path.exists():
        raw = json.loads(pass4_path.read_text())
        classifications = [Classification(**c) for c in raw]
    else:
        classifications = classify_essays(fingerprints, clusters, threshold)
        pass4_path.write_text(
            json.dumps([c.__dict__ for c in classifications], indent=2)
        )

    # Pass 5: Move Plan
    if start_pass > 5 and pass5_path.exists():
        raw = json.loads(pass5_path.read_text())
        move_plan = [MoveEntry(**m) for m in raw]
    else:
        move_plan = generate_move_plan(fingerprints, classifications)
        pass5_path.write_text(
            json.dumps([m.__dict__ for m in move_plan], indent=2)
        )

    result = {
        "fingerprints": len(fingerprints),
        "embeddings": len(embeddings),
        "clusters": len(clusters),
        "cluster_count": len({c.cluster_id for c in clusters}),
        "outliers": sum(1 for c in clusters if c.is_outlier),
        "classifications": len(classifications),
        "move_plan": len(move_plan),
    }

    if execute:
        _execute_move(target_dir, move_plan, assume_yes)
        result["executed"] = True

    return result


def _execute_move(
    source_dir: Path, plan: list[MoveEntry], assume_yes: bool
) -> None:
    """Execute a move plan by renaming files."""
    if not plan:
        print("No move plan entries to execute.")
        return

    print(f"Executing move plan: {len(plan)} files")
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
