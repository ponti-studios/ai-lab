from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab.classify import run_pipeline
from lab.runtime import DEFAULT_FIXTURE, ROOT, summarize_fixture, validate_contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-lab",
        description="Internal AI lab CLI for workers, pipelines, evals, prompts, and benchmarks.",
    )
    subparsers = parser.add_subparsers(dest="domain", required=True)

    worker = subparsers.add_parser("worker", help="Worker runtime commands")
    worker_sub = worker.add_subparsers(dest="command", required=True)
    worker_smoke = worker_sub.add_parser("smoke", help="Run a worker smoke summary")
    worker_smoke.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)

    pipeline = subparsers.add_parser("pipeline", help="Pipeline runtime commands")
    pipeline_sub = pipeline.add_subparsers(dest="command", required=True)
    pipeline_smoke = pipeline_sub.add_parser("smoke", help="Run a pipeline smoke summary")
    pipeline_smoke.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)

    evals = subparsers.add_parser("eval", help="Evaluation harness commands")
    evals_sub = evals.add_subparsers(dest="command", required=True)
    eval_run = evals_sub.add_parser("run", help="Run an evaluation summary")
    eval_run.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)

    benchmark = subparsers.add_parser("benchmark", help="Benchmark commands")
    benchmark_sub = benchmark.add_subparsers(dest="command", required=True)
    benchmark_run = benchmark_sub.add_parser("run", help="Run a benchmark summary")
    benchmark_run.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)

    contract = subparsers.add_parser("contract", help="Prompt/runtime contract commands")
    contract_sub = contract.add_subparsers(dest="command", required=True)
    contract_validate = contract_sub.add_parser("validate", help="Validate a contract JSON document")
    contract_validate.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=ROOT / "contracts" / "prompt_contract.schema.json",
    )

    classify = subparsers.add_parser("classify", help="Classify markdown essays")
    classify.add_argument(
        "dir", type=Path, nargs="?", default=Path.cwd(),
        help="Directory containing markdown essays (default: current)"
    )
    classify.add_argument("--threshold", type=float, default=0.75,
                          help="Classification confidence threshold")
    classify.add_argument("--cluster-threshold", type=float, default=0.75,
                          help="Clustering distance threshold")
    classify.add_argument("--execute", action="store_true",
                          help="Execute the move plan")
    classify.add_argument("--yes", "-y", action="store_true",
                          help="Skip confirmation prompts")
    classify.add_argument("--resume", action="store_true",
                          help="Resume from the highest completed pass")
    classify.add_argument("--from-pass", type=int, default=None,
                          help="Resume from a specific pass (1-5)")
    classify.add_argument("--json", action="store_true",
                          help="Output as JSON")

    return parser


def _print(payload: dict[str, object]) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.domain in {"worker", "pipeline", "eval", "benchmark"}:
        summary = summarize_fixture(args.fixture)
        summary["domain"] = args.domain
        summary["command"] = args.command
        return _print(summary)

    if args.domain == "classify":
        result = run_pipeline(
            Path(args.dir),
            threshold=args.threshold,
            cluster_threshold=args.cluster_threshold,
            execute=args.execute,
            assume_yes=args.yes,
            resume=args.resume,
            from_pass=args.from_pass,
        )
        if args.json:
            return _print(result)
        print(f"Essays: {result['fingerprints']}")
        print(f"Embeddings: {result['embeddings']}")
        print(f"Clusters: {result['clusters']} ({result['cluster_count']} groups, {result['outliers']} outliers)")
        print(f"Classifications: {result['classifications']}")
        print(f"Move plan entries: {result['move_plan']}")
        return 0

    if args.domain == "contract" and args.command == "validate":
        result = validate_contract(args.path)
        _print(result)
        return 0 if result["valid"] else 1

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
