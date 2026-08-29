#!/usr/bin/env bash
# Claude Code PreToolUse hook for the Bash tool.
# Blocks any command that invokes `git push` or `git pull`.
#
# Reads the hook payload JSON on stdin and, when the command matches,
# emits a deny decision on stdout. Otherwise it stays silent and the
# tool call proceeds as normal.
#
# Wired up from ~/.claude/settings.json under hooks.PreToolUse (matcher "Bash").

set -uo pipefail

cmd=$(jq -r '.tool_input.command // ""')

# Match `git ... push` or `git ... pull`:
#   - optional path prefix (e.g. /usr/bin/git) or a preceding shell separator
#     so compound commands like `cd repo && git push` are caught
#   - optional git global options before the subcommand
#     (-C <path>, -c <path>, --git-dir=..., --work-tree=..., --flag)
#   - the `push`/`pull` subcommand itself
# Deliberately does NOT match look-alikes such as `git commit -m "...push..."`,
# `legit pushups`, or `npm run push-build`.
pattern='(^|[^[:alnum:]_-])git[[:space:]]+(-[Cc][[:space:]]+[^[:space:]]+[[:space:]]+|--[a-z-]+=[^[:space:]]+[[:space:]]+|--[a-z-]+[[:space:]]+)*(push|pull)([[:space:]]|$)'

if printf '%s' "$cmd" | grep -Eq "$pattern"; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked: git push and git pull are disabled by a global PreToolUse hook."}}'
fi

exit 0
