"""Command-line interface for the OSINT Pipeline.

Supports four commands:
- run: Execute full 3-stage pipeline
- inspect: Pretty-print a bundle/output file
- validate: Load and validate registry
- collect: Run a single collector
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from osint_pipeline.config import PipelineConfig


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="osint_pipeline",
        description="Echelon OSINT Pipeline — Composed Oracle CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Execute full 3-stage pipeline")
    run_parser.add_argument(
        "--theatre", required=True, help="Theatre ID"
    )
    run_parser.add_argument(
        "--query", required=True, help="Query context as JSON string"
    )
    run_parser.add_argument(
        "--output", "-o", default=None, help="Output file path (default: stdout)"
    )
    run_parser.add_argument(
        "--registry", default=None, help="Registry file path (overrides env)"
    )

    # --- inspect ---
    inspect_parser = subparsers.add_parser(
        "inspect", help="Pretty-print a bundle or output file"
    )
    inspect_parser.add_argument(
        "--bundle", required=True, help="Path to JSON bundle/output file"
    )

    # --- validate ---
    validate_parser = subparsers.add_parser(
        "validate", help="Load and validate registry"
    )
    validate_parser.add_argument(
        "--registry", required=True, help="Path to registry JSON"
    )

    # --- collect ---
    collect_parser = subparsers.add_parser(
        "collect", help="Run a single collector"
    )
    collect_parser.add_argument(
        "--source", required=True, help="Source ID to collect from"
    )
    collect_parser.add_argument(
        "--query", required=True, help="Query context as JSON string"
    )
    collect_parser.add_argument(
        "--output", "-o", default=None, help="Output file path (default: stdout)"
    )

    return parser


def _parse_query(raw: str) -> dict[str, Any]:
    """Parse a JSON query string."""
    try:
        ctx = json.loads(raw)
        if not isinstance(ctx, dict):
            raise ValueError("Query must be a JSON object")
        return ctx
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Error: Invalid query JSON: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _get_collector_map() -> dict[str, type]:
    """Lazy import and return source_id -> collector class map."""
    from osint_pipeline.collectors.boe import BoECollector
    from osint_pipeline.collectors.companies_house import CompaniesHouseCollector
    from osint_pipeline.collectors.ecb_sdmx import ECBDataCollector
    from osint_pipeline.collectors.fred import FREDCollector
    from osint_pipeline.collectors.gazette import GazetteCollector
    from osint_pipeline.collectors.sec_edgar import SECEdgarCollector

    return {
        "companies_house_api": CompaniesHouseCollector,
        "sec_edgar": SECEdgarCollector,
        "ecb_data_api": ECBDataCollector,
        "fred_api": FREDCollector,
        "boe_rates": BoECollector,
        "uk_gazette": GazetteCollector,
    }


def _write_output(data: Any, output_path: str | None) -> None:
    """Write JSON output to file or stdout."""
    text = json.dumps(data, indent=2, default=str)
    if output_path:
        Path(output_path).write_text(text)
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(text)


def cmd_run(args: argparse.Namespace) -> int:
    """Execute full 3-stage pipeline."""
    from osint_pipeline.engine.collection_runner import CollectionRunner
    from osint_pipeline.engine.corroboration import CorroborationEngine
    from osint_pipeline.engine.counter_signal import CounterSignalChecker
    from osint_pipeline.engine.scorer import Scorer

    config = PipelineConfig.from_env()
    if args.registry:
        config = PipelineConfig(
            registry_path=args.registry,
            companies_house_api_key=config.companies_house_api_key,
            sec_edgar_user_agent=config.sec_edgar_user_agent,
            fred_api_key=config.fred_api_key,
            max_workers=config.max_workers,
            timeout_budget=config.timeout_budget,
            collector_timeout=config.collector_timeout,
        )

    query_context = _parse_query(args.query)
    collector_configs = config.collector_configs()
    collector_map = _get_collector_map()

    # Build available collectors
    collectors = []
    for source_id, cls in collector_map.items():
        if source_id in collector_configs:
            try:
                collectors.append(cls(config=collector_configs[source_id]))
            except ValueError as exc:
                print(
                    f"Skipping {source_id}: {exc}", file=sys.stderr
                )

    if not collectors:
        print(
            "Error: No collectors available. Check API key env vars.",
            file=sys.stderr,
        )
        return 1

    # Stage 1: Collection
    runner = CollectionRunner(
        collectors=collectors,
        max_workers=config.max_workers,
        timeout_budget_seconds=config.timeout_budget,
    )
    try:
        summary = runner.run(
            query_context=query_context, theatre_id=args.theatre
        )

        # Stage 2: Corroboration
        corr_engine = CorroborationEngine()
        corr_results = corr_engine.evaluate_all(summary)

        # Stage 2b: Counter-signal
        cs_checker = CounterSignalChecker()
        cs_bundles = [
            b for b in summary.bundles
            if b.query_context.get("counter_signal_class")
        ]
        cs_gaps = [
            g for g in summary.gaps
            if g.source_group in ("official_gov",)
        ]
        cs_results = cs_checker.evaluate(cs_bundles, cs_gaps)

        # Stage 3: Scoring
        scorer = Scorer()
        output = scorer.score(
            collection=summary,
            corroboration_results=corr_results,
            counter_signal_results=cs_results,
            theatre_id=args.theatre,
        )

        _write_output(output.model_dump(mode="json"), args.output)
    finally:
        runner.close_all()

    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Pretty-print a bundle or output file."""
    path = Path(args.bundle)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2, default=str))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Load and validate registry."""
    from osint_pipeline.models.registry import RegistryLoader

    path = Path(args.registry)
    if not path.exists():
        print(f"Error: Registry not found: {path}", file=sys.stderr)
        return 1

    try:
        registry = RegistryLoader.from_file(path)
    except Exception as exc:
        print(f"Error: Registry validation failed: {exc}", file=sys.stderr)
        return 1

    free = registry.free_public_sources()
    eligible = registry.settlement_eligible()
    upstreams = registry.upstream_groups()

    print(f"Registry: {path.name}")
    print(f"Version:  {registry.version}")
    print(f"Sources:  {registry.total_sources}")
    print(f"Free:     {len(free)}")
    print(f"Eligible: {len(eligible)}")
    print(f"Upstreams:{len(upstreams)}")

    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    """Run a single collector."""
    config = PipelineConfig.from_env()
    collector_configs = config.collector_configs()
    collector_map = _get_collector_map()

    source_id = args.source
    if source_id not in collector_map:
        print(
            f"Error: Unknown source '{source_id}'. "
            f"Available: {', '.join(sorted(collector_map))}",
            file=sys.stderr,
        )
        return 1

    cls = collector_map[source_id]
    source_config = collector_configs.get(source_id, {})

    try:
        collector = cls(config=source_config)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    query_context = _parse_query(args.query)

    try:
        result = collector.collect(query_context)
    finally:
        collector.close()

    if result.succeeded:
        _write_output(result.bundle.model_dump(mode="json"), args.output)
    else:
        print(
            f"Collection failed: {result.status.value} — {result.error_message}",
            file=sys.stderr,
        )
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    handlers = {
        "run": cmd_run,
        "inspect": cmd_inspect,
        "validate": cmd_validate,
        "collect": cmd_collect,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)
