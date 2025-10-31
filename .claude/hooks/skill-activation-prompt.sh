#!/bin/bash
set -e

export CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$CLAUDE_PROJECT_DIR/.claude/hooks"
cat | npx tsx skill-activation-prompt.ts
