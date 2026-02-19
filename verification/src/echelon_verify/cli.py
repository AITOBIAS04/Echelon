"""Click-based CLI for the verification pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
import sys

import click

from echelon_verify.config import (
    IngestionConfig,
    OracleConfig,
    PipelineConfig,
    ScoringConfig,
)
from echelon_verify.models import CalibrationCertificate
from echelon_verify.oracle.base import OracleAdapter
from echelon_verify.scoring.anthropic_scorer import AnthropicScorer
from echelon_verify.storage import Storage


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _progress_bar(completed: int, total: int) -> None:
    pct = int(completed / total * 100) if total else 0
    click.echo(f"\r  Progress: {completed}/{total} ({pct}%)", nl=False, err=True)
    if completed == total:
        click.echo("", err=True)


@click.group()
@click.version_option(package_name="echelon-verify")
def cli() -> None:
    """Echelon — Community Oracle Verification Pipeline."""


@cli.command()
@click.argument("repo_url")
@click.option("--oracle-url", required=True, help="HTTP oracle endpoint URL")
@click.option("--construct-id", default="unnamed-oracle", help="Oracle construct identifier")
@click.option("--github-token", envvar="GITHUB_TOKEN", help="GitHub API token")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key")
@click.option("--model", default="claude-sonnet-4-6", help="Scoring model")
@click.option("--limit", default=100, help="Max PRs to ingest")
@click.option("--min-replays", default=50, help="Minimum replays for certificate")
@click.option("--output-dir", default="data", help="Output directory")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--dry-run", is_flag=True, help="Ingest only, skip oracle invocation")
def verify(
    repo_url: str,
    oracle_url: str,
    construct_id: str,
    github_token: str | None,
    api_key: str | None,
    model: str,
    limit: int,
    min_replays: int,
    output_dir: str,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Run full verification pipeline."""
    _setup_logging(verbose)

    config = PipelineConfig(
        ingestion=IngestionConfig(
            repo_url=repo_url,
            github_token=github_token,
            limit=limit,
        ),
        oracle=OracleConfig(type="http", url=oracle_url),
        scoring=ScoringConfig(api_key=api_key, model=model),
        min_replays=min_replays,
        output_dir=output_dir,
        construct_id=construct_id,
    )

    oracle = OracleAdapter.from_config(config.oracle)
    scorer = AnthropicScorer(config.scoring)

    from echelon_verify.pipeline import VerificationPipeline

    pipeline = VerificationPipeline(config, oracle, scorer)

    if dry_run:
        records = asyncio.run(pipeline.ingest_only())
        click.echo(f"Ingested {len(records)} ground truth records (dry run — no oracle invocation)")
        return

    progress = _progress_bar if verbose else None
    cert = asyncio.run(pipeline.run(progress=progress))
    click.echo(json.dumps(cert.model_dump(mode="json"), indent=2))


@cli.command()
@click.argument("repo_url")
@click.option("--github-token", envvar="GITHUB_TOKEN", help="GitHub API token")
@click.option("--limit", default=100, help="Max PRs to ingest")
@click.option("--since", default=None, help="Ingest PRs merged since (ISO datetime)")
@click.option("--output-dir", default="data", help="Output directory")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def ingest(
    repo_url: str,
    github_token: str | None,
    limit: int,
    since: str | None,
    output_dir: str,
    verbose: bool,
) -> None:
    """Fetch and cache ground truth from GitHub."""
    _setup_logging(verbose)

    from echelon_verify.ingestion.github import GitHubIngester

    ingestion_config = IngestionConfig(
        repo_url=repo_url,
        github_token=github_token,
        limit=limit,
        since=since,
    )
    ingester = GitHubIngester(ingestion_config)
    records = asyncio.run(ingester.ingest())

    storage = Storage(output_dir)
    owner_repo = repo_url.split("/")[-2:]
    repo_key = "_".join(owner_repo) if len(owner_repo) == 2 else "unknown"

    for record in records:
        storage.append_jsonl(repo_key, "ground_truth.jsonl", record)

    click.echo(f"Ingested {len(records)} ground truth records to {output_dir}/{repo_key}/")


@cli.command()
@click.argument("repo_url")
@click.option("--oracle-url", required=True, help="HTTP oracle endpoint URL")
@click.option("--construct-id", default="unnamed-oracle", help="Oracle construct identifier")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key")
@click.option("--model", default="claude-sonnet-4-6", help="Scoring model")
@click.option("--min-replays", default=50, help="Minimum replays for certificate")
@click.option("--output-dir", default="data", help="Output directory")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def score(
    repo_url: str,
    oracle_url: str,
    construct_id: str,
    api_key: str | None,
    model: str,
    min_replays: int,
    output_dir: str,
    verbose: bool,
) -> None:
    """Score cached data and generate certificate."""
    _setup_logging(verbose)

    config = PipelineConfig(
        ingestion=IngestionConfig(repo_url=repo_url),
        oracle=OracleConfig(type="http", url=oracle_url),
        scoring=ScoringConfig(api_key=api_key, model=model),
        min_replays=min_replays,
        output_dir=output_dir,
        construct_id=construct_id,
    )

    oracle = OracleAdapter.from_config(config.oracle)
    scorer = AnthropicScorer(config.scoring)

    from echelon_verify.pipeline import VerificationPipeline

    pipeline = VerificationPipeline(config, oracle, scorer)

    progress = _progress_bar if verbose else None
    cert = asyncio.run(pipeline.score_only(progress=progress))
    click.echo(json.dumps(cert.model_dump(mode="json"), indent=2))


@cli.command()
@click.argument("certificate_id")
@click.option("--output-dir", default="data", help="Output directory")
def inspect(certificate_id: str, output_dir: str) -> None:
    """Display a certificate in human-readable format."""
    storage = Storage(output_dir)
    cert = storage.read_certificate(certificate_id)

    if cert is None:
        click.echo(f"Certificate {certificate_id} not found.", err=True)
        raise SystemExit(1)

    click.echo(f"Certificate: {cert.certificate_id}")
    click.echo(f"Construct:   {cert.construct_id}")
    click.echo(f"Domain:      {cert.domain}")
    click.echo(f"Replays:     {cert.replay_count}")
    click.echo(f"Precision:   {cert.precision:.4f}")
    click.echo(f"Recall:      {cert.recall:.4f}")
    click.echo(f"Reply Acc:   {cert.reply_accuracy:.4f}")
    click.echo(f"Composite:   {cert.composite_score:.4f}")
    click.echo(f"Brier:       {cert.brier:.4f}")
    click.echo(f"Model:       {cert.scoring_model}")
    click.echo(f"Methodology: {cert.methodology_version}")
    click.echo(f"Source:      {cert.ground_truth_source}")
    click.echo(f"Timestamp:   {cert.timestamp.isoformat()}")
