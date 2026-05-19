#!/usr/bin/env bash

# Shared helpers for the Git porting scripts in this directory.

if [[ -t 1 && -t 2 ]]; then
  RESET=$'\033[0m'
  GREY=$'\033[2m'
  BOLD_WHITE=$'\033[1;37m'
  PURPLE=$'\033[35m'
  GREEN=$'\033[32m'
  RED=$'\033[31m'
  CYAN=$'\033[36m'
  BL=$'\033[94m'
  BOLD_YELLOW=$'\033[1;93m'
  ORANGE=$'\033[38;5;208m'
else
  RESET=''
  GREY=''
  BOLD_WHITE=''
  PURPLE=''
  GREEN=''
  RED=''
  CYAN=''
  BL=''
  BOLD_YELLOW=''
  ORANGE=''
fi

_ESC=$'\033'
_NW=0
_BOX_W=0

# ── Visual helpers ────────────────────────────────────────────────────────────

vis_len() {
  local s
  s=$(printf '%s' "$1" | sed "s/${_ESC}\[[0-9;]*m//g")
  printf '%d' "${#s}"
}

shorten_path() {
  printf '%s' "${1/#${HOME}/~}"
}

# ── Header box ────────────────────────────────────────────────────────────────

_box_line() {
  local content="$1"
  local color="${2:-$GREY}"
  local pad=$(( _BOX_W - $(vis_len "$content") ))
  printf '%s│%s %s%*s %s│%s\n' "$color" "$RESET" "$content" "$pad" "" "$color" "$RESET"
}

# print_header <title> <label> <value> [<label> <value> ...]
print_header() {
  local title="$1"; shift
  local lines=()
  while [[ $# -ge 2 ]]; do
    local lbl val
    lbl="$1"
    val=$(shorten_path "$2")
    lines+=("${GREY}${lbl}${RESET}  ${val}")
    shift 2
  done

  _BOX_W=$(vis_len "$title")
  local line
  for line in "${lines[@]}"; do
    local lw
    lw=$(vis_len "$line")
    (( lw > _BOX_W )) && _BOX_W=$lw
  done

  local dw=$(( _BOX_W + 2 ))
  local hline
  printf -v hline '─%.0s' $(seq 1 "$dw")

  printf '\n%s╭%s╮%s\n' "$GREY" "$hline" "$RESET"
  _box_line "$title"
  printf '%s│%*s│%s\n' "$GREY" "$(( _BOX_W + 2 ))" "" "$RESET"
  for line in "${lines[@]}"; do
    _box_line "$line"
  done
  printf '%s╰%s╯%s\n\n' "$GREY" "$hline" "$RESET"
}

# print_message_box <border-color> <title> <body>
print_message_box() {
  local border="$1"
  local title="$2"
  local body="$3"

  _BOX_W=$(vis_len "$title")
  local bw
  bw=$(vis_len "$body")
  (( bw > _BOX_W )) && _BOX_W=$bw

  local dw=$(( _BOX_W + 2 ))
  local hline
  printf -v hline '─%.0s' $(seq 1 "$dw")

  printf '\n%s╭%s╮%s\n' "$border" "$hline" "$RESET"
  _box_line "$title" "$border"
  printf '%s│%*s│%s\n' "$border" "$(( _BOX_W + 2 ))" "" "$RESET"
  _box_line "$body" "$border"
  printf '%s╰%s╯%s\n\n' "$border" "$hline" "$RESET"
}

# ── Item lines ────────────────────────────────────────────────────────────────

init_item_widths() {
  local n
  for n in "$@"; do
    (( ${#n} > _NW )) && _NW=${#n}
  done
  _NW=$(( _NW + 3 ))
}

# print_item <name> <status> <status-color> <icon> <icon-color> [reason]
print_item() {
  local name="$1" status="$2" sc="$3" icon="$4" ic="$5" reason="${6:-}"
  printf "    %s▸▸%s  %-${_NW}s%s%s%s %s%s%s\n" \
    "$BL" "$RESET" "$name" "$sc" "$status" "$RESET" "$ic" "$icon" "$RESET"
  if [[ -n "$reason" ]]; then
    printf '%*s%s%s%s\n' "$(( 7 + _NW ))" "" "$GREY" "$reason" "$RESET"
  fi
}

# ── Summary ───────────────────────────────────────────────────────────────────

print_summary() {
  local ok="$1" total="$2" errors="$3"
  local cc="${BOLD_YELLOW}"
  (( errors > 0 )) && cc="${RED}"
  printf '\n        %s%d / %d%s    %sDone.%s\n\n' \
    "$cc" "$ok" "$total" "$RESET" "$BOLD_YELLOW" "$RESET"
}

# ── Log helpers ───────────────────────────────────────────────────────────────

log_info() {
  printf '  %s·  %s%s\n' "$GREY" "$*" "$RESET"
}

log_nest() {
  printf '  %s→%s  %s\n' "$GREY" "$RESET" "$*"
}

log_warn() {
  printf '    %s▸▸%s  %s  %s◆%s\n' "$BL" "$RESET" "$*" "$BOLD_YELLOW" "$RESET"
}

log_error() {
  printf '%s[ERROR]%s %s\n' "$RED" "$RESET" "$*" >&2
}

log_done() {
  printf '  %s·  %s%s\n' "$GREY" "$*" "$RESET"
}

log_step_ok() {
  printf "    %s▸▸%s  %s  %s✓%s\n" "$BL" "$RESET" "$*" "$GREEN"       "$RESET"
}

log_step_fail() {
  printf "    %s▸▸%s  %s  %s✗%s\n" "$BL" "$RESET" "$*" "$RED"         "$RESET" >&2
}

log_step_skip() {
  printf "    %s▸▸%s  %s  %s◆%s\n" "$BL" "$RESET" "$*" "$BOLD_YELLOW" "$RESET"
}

# ── Git utilities ─────────────────────────────────────────────────────────────

die() {
  log_error "$*"
  exit 1
}

require_git_repo() {
  git rev-parse --git-dir >/dev/null 2>&1 || die "Not inside a Git repository."
}

ensure_clean_worktree() {
  if git rev-parse -q --verify CHERRY_PICK_HEAD >/dev/null 2>&1; then
    return 0
  fi

  [[ -z "$(git status --porcelain)" ]] || die "Working tree is not clean. Commit, stash, or discard changes first."
}

has_unresolved_conflicts() {
  [[ -n "$(git diff --name-only --diff-filter=U)" ]]
}

git_current_branch() {
  git symbolic-ref --quiet --short HEAD 2>/dev/null || true
}

resolve_directory() {
  (
    cd "$1" >/dev/null 2>&1 || exit 1
    pwd -P
  )
}

resolve_path_from_parent() {
  local path="$1"
  local parent
  local base

  parent="$(dirname "$path")"
  base="$(basename "$path")"
  parent="$(resolve_directory "$parent")" || return 1

  printf '%s/%s\n' "$parent" "$base"
}

format_commit() {
  local sha="$1"
  printf '%s%s%s' "$GREEN" "${sha:0:8}" "$RESET"
}

format_branch() {
  local branch="$1"
  printf '%s%s%s' "$BOLD_WHITE" "$branch" "$RESET"
}

format_branch_list() {
  local branch
  local result=""

  for branch in "$@"; do
    if [[ -n "$result" ]]; then
      result+=", "
    fi
    result+="$(format_branch "$branch")"
  done

  printf '%s' "$result"
}
