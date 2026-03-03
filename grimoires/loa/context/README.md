# Context Directory

This directory is for user-provided context that feeds into the PRD discovery process (`/plan-and-analyze`).

## What to Put Here

- Product briefs, specs, or requirements documents
- Market research or competitive analysis
- Technical constraints or architecture notes
- Stakeholder feedback or user research
- Any documents that inform what you want to build

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

Place your context files here, then run `/plan-and-analyze` to begin discovery.
