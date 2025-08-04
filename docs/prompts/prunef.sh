#!/usr/bin/env bash
###############################################################################
# prune_langgraphjs_prompts.sh
# ---------------------------------------------------------------------------
# Retain ONLY the essential frontend/streaming sections in
# docs/prompts/langgraphjs-llms-full.md for UI/SSE/Redux work.
# Keeps: 1-755, 16854-17300, 20832-21100
# Works on all sed versions, always makes a timestamped backup.
###############################################################################

set -euo pipefail

DOC="langgraphjs-llms-full.md"

# ---- safety check -----------------------------------------------------------
if [[ ! -f $DOC ]]; then
  echo "ERROR: cannot find markdown file: $DOC" >&2
  exit 1
fi

backup="${DOC}.$(date +%Y%m%d_%H%M%S).bak"
cp "$DOC" "$backup"

# ---- extract only the keep-ranges -------------------------------------------
tmpfile=$(mktemp)

# Print only the three keep-ranges, in order.
sed -n '1,755p;16854,17300p;20832,21100p' "$DOC" > "$tmpfile"

# Overwrite the original file with the pruned content.
mv "$tmpfile" "$DOC"

echo "✓ Pruning complete."
echo "  Only lines 1-755, 16854-17300, 20832-21100 remain."
echo "  Backup written to: $backup"