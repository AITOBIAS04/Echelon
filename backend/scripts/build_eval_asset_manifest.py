"""CLI utility to generate an eval asset manifest from a local folder.

Usage:
    python3 build_eval_asset_manifest.py \
        --asset-id humaneval \
        --asset-class benchmark \
        --source-url https://github.com/openai/human-eval \
        --version v1 \
        --root /path/to/data

Outputs the manifest as JSON to stdout.
"""

import argparse
import json
import sys
from pathlib import Path

from backend.services.r2_manifest_builder import build_manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an eval asset manifest from a local folder.",
    )
    parser.add_argument(
        "--asset-id",
        required=True,
        help="Filesystem-safe asset identifier (e.g. humaneval, wcag)",
    )
    parser.add_argument(
        "--asset-class",
        default="benchmark",
        choices=["benchmark", "standard"],
        help="Asset classification (default: benchmark)",
    )
    parser.add_argument(
        "--source-url",
        required=True,
        help="Canonical upstream URL for the dataset",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version tag for this snapshot (e.g. v1, 2.2)",
    )
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Path to the local directory containing asset files",
    )
    parser.add_argument(
        "--license",
        default=None,
        help="Optional SPDX license identifier (e.g. MIT, Apache-2.0)",
    )

    args = parser.parse_args()

    try:
        entry = build_manifest(
            args.root,
            asset_id=args.asset_id,
            asset_class=args.asset_class,
            source_url=args.source_url,
            version=args.version,
            license=args.license,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Pretty-print the manifest JSON to stdout
    print(json.dumps(json.loads(entry.model_dump_json()), indent=2))


if __name__ == "__main__":
    main()
