#!/usr/bin/env bash
###############################################################################
# prune_langgraph_prompts.sh
# ---------------------------------------------------------------------------
# Removes platform / SaaS / infra sections from
# docs/prompts/langgraph-llms-full.md while keeping core agentic material.
# Works on both GNU and BSD sed, and always backs up the file first.
###############################################################################

set -euo pipefail

DOC="langgraph-llms-full.md"

# ---- safety check -----------------------------------------------------------
if [[ ! -f $DOC ]]; then
  echo "ERROR: cannot find markdown file: $DOC" >&2
  exit 1
fi

backup="${DOC}.$(date +%Y%m%d_%H%M%S).bak"
cp "$DOC" "$backup"

# ---- cross-platform in-place edit helper ------------------------------------
sed_in_place() {
  if sed --version >/dev/null 2>&1; then
    # GNU sed
    sed -i "$@"
  else
    # BSD / macOS sed
    sed -i '' "$@"
  fi
}

# ---- actual pruning ---------------------------------------------------------
# NOTE: nothing may follow the back-slash at EOL – no space, no comment.
sed_in_place \
  -e '8001,$d' \
  -e '5241,7999d' \
  -e '2726,5099d' \
  -e '1451,2499d' \
  -e '701,1199d' \
  "$DOC"

echo "✓ Pruning complete."
echo "  Kept everything outside the ranges above."
echo "  Backup written to: $backup"