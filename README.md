# ai-lab

`ai-lab` is the internal AI systems lab for Ponti Studios — workers, evals,
retrieval, prompts, pipelines, and benchmarks.

The repo is scoped to five domains:

- extraction workers
- retrieval experiments
- agent pipelines
- evaluation harnesses
- prompt contracts and model benchmarks

The production app API remains in
`/Users/charlesponti/Developer/hominem/services/api`.

## Layout

```text
lab/                CLI entrypoints and shared lab runtime helpers
workers/            extraction and retrieval worker notes / implementations
pipelines/          orchestration pipelines and experiment flows
evals/              fixtures and regression-oriented evaluation inputs
prompts/            versioned prompt assets
benchmarks/         provider and model comparison artifacts
contracts/          prompt and runtime contract definitions
archive/legacy_api/ retired FastAPI-era product backend snapshot
```

## Quick start

```bash
python -m lab.cli worker smoke
python -m lab.cli pipeline smoke
python -m lab.cli eval run
python -m lab.cli benchmark run
python -m lab.cli contract validate contracts/prompt_contract.schema.json
```

## Principles

- This repo produces reusable AI workflow infrastructure, not app auth or user APIs.
- Production systems should consume stable outputs from this repo rather than
  reintroduce a monolithic product API here.
- Experiments must be regression-testable through fixtures and contracts.

## Legacy code

The previous FastAPI application, routers, prompts, and tests have been moved to
`archive/legacy_api/` so the old product surface remains inspectable without
competing with the new lab charter.
