#!/bin/bash
# update-age-index.sh — auto-discover gitignored secret files and register
# new ones in .age-index, so paths don't have to be typed by hand.
#
# Only touches .age-index (a plain data file) — never modifies pre-commit,
# post-merge, or post-checkout. Run manually whenever a new secret file is
# added to the working tree; not invoked automatically by git.
#
# A file counts as "secret" here if it's gitignored by any pattern OTHER
# than the known non-secret ones below (editor/OS/local-settings junk) —
# an exclude-list rather than hardcoding the secret pattern list, so this
# script doesn't need updating every time a new secret pattern is added
# to .gitignore.
set -e

INDEX=".age-index"
touch "$INDEX"

NOT_SECRET_PATTERNS=(
  ".DS_Store"
  ".claude/settings.local.json"
  ".vscode/"
  ".idea/"
)

is_known_non_secret() {
  local pattern="$1"
  for p in "${NOT_SECRET_PATTERNS[@]}"; do
    [ "$pattern" = "$p" ] && return 0
  done
  return 1
}

already_listed() {
  grep -qxF "$1" "$INDEX" 2>/dev/null
}

new_entries=()

while IFS= read -r file; do
  [ -z "$file" ] && continue
  [ -f "$file" ] || continue
  already_listed "$file" && continue

  # find which .gitignore pattern actually matched this file
  match_line=$(git check-ignore -v -- "$file" 2>/dev/null | head -1)
  pattern=$(printf '%s' "$match_line" | sed -E 's/^[^:]+:[0-9]+:([^	]+)	.*/\1/')

  [ -z "$pattern" ] && continue
  is_known_non_secret "$pattern" && continue

  new_entries+=("$file")
done < <(git status --ignored --porcelain=v1 | awk '/^!!/{print substr($0,4)}')

if [ "${#new_entries[@]}" -eq 0 ]; then
  echo "update-age-index: no new secret files found"
  exit 0
fi

{
  echo "# Added $(date +%Y-%m-%d)"
  for f in "${new_entries[@]}"; do
    echo "$f"
  done
} >> "$INDEX"

echo "update-age-index: added ${#new_entries[@]} new entries to $INDEX:"
printf '  %s\n' "${new_entries[@]}"
