# Context Directory

This directory contains user-provided context that feeds into the PRD discovery process (`/plan-and-analyze`).

## Current Files

| File | Purpose |
|------|---------|
| `echelon_platform_roadmap.md` | Full build sequence, cycle dependency graph, project vision |
| `echelon_cycle_014.md` | Active cycle context: Bounded Inquiry Markets |
| `Echelon_System_Bible_v13.md` | Canonical architecture document (LMSR, Theatres, Agents, etc.) |
| `Echelon_System_Bible_v13_Addendum.md` | Addendum to System Bible v13 |
| `Echelon_Theatre_Template_Library_Live_v2.md` | Theatre template definitions and library |
| `Echelon_Composed_Oracle_Spec_v2_Addendum.md` | Composed Oracle specification addendum |
| `REPO_MAP.md` | Repository structure and module map |
| `config_snapshot.json` | Configuration snapshot |

## Important: Files Are Tracked

**Context files in this directory are tracked in git.** This is intentional for Echelon — cycle context files, the platform roadmap, and core specs are part of the project's documented build history. Sensitive business information should not be placed here.

## How It Works

When you run `/plan-and-analyze`, the discovering-requirements agent will:
1. Read all files in this directory
2. Use them as input for generating your PRD
3. Ask clarifying questions based on what it finds

## Supported Formats

- Markdown (`.md`)
- Text files (`.txt`)
- PDFs (`.pdf`)
- Images (`.png`, `.jpg`) - for mockups or diagrams
- JSON (`.json`) - for configuration snapshots

Place your context files here, then run `/plan-and-analyze` to begin discovery.
