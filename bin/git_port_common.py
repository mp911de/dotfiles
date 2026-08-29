"""Shared building blocks for the Git porting commands in this directory.

This module is the Python counterpart of ``git-port-common.sh``. It provides
three cohesive collaborators that the ``git-copy-fix``, ``git-edit-message`` and
``git-multiport`` commands build on:

``Ansi``
    A value object that resolves the ANSI colour palette once, honouring whether
    the program is attached to a terminal.
``Console``
    Renders the boxed headers, item lines, summaries and log messages that give
    the commands their consistent look.
``Git``
    A thin, well-named wrapper around the ``git`` executable.

It also offers :class:`StateStore` for persisting resumable workflow state inside
the repository, and :class:`PortError` as the single user-facing failure type.

The original shell helpers remain in ``git-port-common.sh`` because the bash
bootstrap scripts still source them; this module mirrors their behaviour and
visual output rather than replacing the file.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence


class PortError(Exception):
    """Signals a recoverable failure whose message is meant for the user.

    Command entry points catch this exception, print the message through
    :meth:`Console.error`, and exit with a non-zero status. It is the structured
    equivalent of the shell helpers' ``die`` function.
    """


# ── Terminal palette ──────────────────────────────────────────────────────────


class Ansi:
    """The ANSI colour palette, resolved once for the lifetime of a command.

    When the program is not attached to a terminal every colour resolves to the
    empty string, so the rendered output degrades cleanly to plain text.
    """

    _CODES = {
        "reset": "0",
        "grey": "2",
        "bold_white": "1;37",
        "purple": "35",
        "green": "32",
        "red": "31",
        "cyan": "36",
        "blue": "94",
        "bold_yellow": "1;93",
        "orange": "38;5;208",
    }

    _ESCAPE = re.compile(r"\033\[[0-9;]*m")

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        for name, code in self._CODES.items():
            setattr(self, name, f"\033[{code}m" if enabled else "")

    @classmethod
    def for_streams(cls) -> "Ansi":
        """Enable colour only when both stdout and stderr are terminals."""
        return cls(sys.stdout.isatty() and sys.stderr.isatty())

    @classmethod
    def strip(cls, text: str) -> str:
        """Return ``text`` with every ANSI colour escape removed."""
        return cls._ESCAPE.sub("", text)

    @classmethod
    def width(cls, text: str) -> int:
        """Return the visible width of ``text``, ignoring colour escapes."""
        return len(cls.strip(text))


# ── Console rendering ──────────────────────────────────────────────────────────


class Console:
    """Renders the headers, item lines, summaries and log lines of the commands.

    The console keeps two pieces of layout state that callers prime up front: the
    width of the most recent header box and the column width reserved for item
    names. Both mirror the module-level variables used by ``git-port-common.sh``.
    """

    def __init__(self, ansi: Optional[Ansi] = None) -> None:
        self.ansi = ansi or Ansi.for_streams()
        self._box_width = 0
        self._name_width = 0

    # -- low level output ------------------------------------------------------

    @staticmethod
    def _out(text: str) -> None:
        sys.stdout.write(text)

    @staticmethod
    def _err(text: str) -> None:
        sys.stderr.write(text)

    # -- path helpers ----------------------------------------------------------

    @staticmethod
    def shorten_path(value: str) -> str:
        """Replace a leading home directory in ``value`` with ``~``."""
        home = os.path.expanduser("~")
        if value == home:
            return "~"
        if value.startswith(home + os.sep):
            return "~" + value[len(home):]
        return value

    # -- header boxes ----------------------------------------------------------

    def _box_line(self, content: str, color: Optional[str] = None) -> None:
        a = self.ansi
        color = a.grey if color is None else color
        pad = self._box_width - a.width(content)
        self._out(f"{color}│{a.reset} {content}{' ' * pad} {color}│{a.reset}\n")

    def header(self, title: str, *pairs: str) -> None:
        """Render a boxed header with a ``title`` and ``label``/``value`` rows.

        ``pairs`` is a flat sequence of alternating labels and values, e.g.
        ``console.header(title, "source:", ref, "target:", repo)``. Values are
        shortened relative to the home directory before they are measured.
        """
        a = self.ansi
        lines = []
        labels_and_values = list(pairs)
        for index in range(0, len(labels_and_values) - 1, 2):
            label = labels_and_values[index]
            value = self.shorten_path(labels_and_values[index + 1])
            lines.append(f"{a.grey}{label}{a.reset}  {value}")

        self._box_width = max([a.width(title)] + [a.width(line) for line in lines])
        rule = "─" * (self._box_width + 2)

        self._out(f"\n{a.grey}╭{rule}╮{a.reset}\n")
        self._box_line(title)
        self._out(f"{a.grey}│{' ' * (self._box_width + 2)}│{a.reset}\n")
        for line in lines:
            self._box_line(line)
        self._out(f"{a.grey}╰{rule}╯{a.reset}\n\n")

    def message_box(self, border: str, title: str, body: str) -> None:
        """Render a single-message box framed in the ``border`` colour."""
        a = self.ansi
        self._box_width = max(a.width(title), a.width(body))
        rule = "─" * (self._box_width + 2)

        self._out(f"\n{border}╭{rule}╮{a.reset}\n")
        self._box_line(title, border)
        self._out(f"{border}│{' ' * (self._box_width + 2)}│{a.reset}\n")
        self._box_line(body, border)
        self._out(f"{border}╰{rule}╯{a.reset}\n\n")

    # -- item lines ------------------------------------------------------------

    def reserve_item_width(self, names: Sequence[str]) -> None:
        """Reserve the name column width for the upcoming :meth:`item` calls."""
        longest = max((len(name) for name in names), default=0)
        self._name_width = longest + 3

    def item(
        self,
        name: str,
        status: str,
        status_color: str,
        icon: str,
        icon_color: str,
        reason: str = "",
    ) -> None:
        """Render one result line: a branch name, its status and an icon.

        An optional ``reason`` is printed on a second, indented and dimmed line.
        """
        a = self.ansi
        self._out(
            f"    {a.blue}▸▸{a.reset}  {name:<{self._name_width}}"
            f"{status_color}{status}{a.reset} {icon_color}{icon}{a.reset}\n"
        )
        if reason:
            self._out(f"{' ' * (7 + self._name_width)}{a.grey}{reason}{a.reset}\n")

    # -- summary ---------------------------------------------------------------

    def summary(self, ok: int, total: int, errors: int = 0) -> None:
        """Render the closing ``ok / total`` count followed by ``Done.``.

        The count and the ``Done.`` label turn green only when every step
        succeeded (no errors and nothing left incomplete); otherwise they keep
        the yellow/orange tint, and the count turns red when there were errors.
        """
        a = self.ansi
        succeeded = errors == 0 and ok == total
        accent = a.green if succeeded else a.bold_yellow
        count_color = a.red if errors > 0 else accent
        self._out(
            f"\n        {count_color}{ok} / {total}{a.reset}"
            f"    {accent}Done.{a.reset}\n\n"
        )

    # -- log lines -------------------------------------------------------------

    def info(self, message: str) -> None:
        a = self.ansi
        self._out(f"  {a.grey}·  {message}{a.reset}\n")

    # ``done`` reads better at call sites but renders identically to ``info``.
    done = info

    def nest(self, message: str) -> None:
        a = self.ansi
        self._out(f"  {a.grey}→{a.reset}  {message}\n")

    def warn(self, message: str) -> None:
        a = self.ansi
        self._out(f"    {a.blue}▸▸{a.reset}  {message}  {a.bold_yellow}◆{a.reset}\n")

    def error(self, message: str) -> None:
        a = self.ansi
        self._err(f"{a.red}[ERROR]{a.reset} {message}\n")

    def step_ok(self, message: str) -> None:
        a = self.ansi
        self._out(f"    {a.blue}▸▸{a.reset}  {message}  {a.green}✓{a.reset}\n")

    def step_fail(self, message: str) -> None:
        a = self.ansi
        self._err(f"    {a.blue}▸▸{a.reset}  {message}  {a.red}✗{a.reset}\n")

    def step_skip(self, message: str) -> None:
        a = self.ansi
        self._out(f"    {a.blue}▸▸{a.reset}  {message}  {a.bold_yellow}◆{a.reset}\n")

    # -- inline formatting -----------------------------------------------------

    def branch(self, name: str) -> str:
        """Return ``name`` styled as a branch reference."""
        a = self.ansi
        return f"{a.bold_white}{name}{a.reset}"

    def commit(self, sha: str) -> str:
        """Return the abbreviated ``sha`` styled as a commit reference."""
        a = self.ansi
        return f"{a.green}{sha[:8]}{a.reset}"

    def branch_list(self, names: Sequence[str]) -> str:
        """Return a comma-separated list of styled branch names."""
        return ", ".join(self.branch(name) for name in names)


# ── Git access ─────────────────────────────────────────────────────────────────


class Git:
    """A small, intention-revealing wrapper around the ``git`` executable.

    Each instance is bound to a working directory (the current one by default).
    Low-level helpers (:meth:`text`, :meth:`succeeds`, :meth:`capture`,
    :meth:`interactive`) keep the subprocess plumbing in one place. The named
    methods express the operations the porting commands actually need.
    """

    def __init__(self, cwd: Optional[str] = None) -> None:
        self.cwd = cwd

    # -- subprocess plumbing ---------------------------------------------------

    def text(self, *args: str) -> str:
        """Run git, return stdout with trailing newlines stripped.

        Intended for commands that are expected to succeed; a non-zero exit
        raises :class:`PortError` since it indicates a broken invariant.
        """
        result = subprocess.run(
            ["git", *args], cwd=self.cwd, capture_output=True, text=True
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or f"git {' '.join(args)} failed"
            raise PortError(detail)
        return result.stdout.rstrip("\n")

    def capture(self, *args: str, merge_stderr: bool = False) -> subprocess.CompletedProcess:
        """Run git and return the completed process with captured output."""
        stderr = subprocess.STDOUT if merge_stderr else subprocess.PIPE
        return subprocess.run(
            ["git", *args], cwd=self.cwd, text=True,
            stdout=subprocess.PIPE, stderr=stderr,
        )

    def succeeds(self, *args: str) -> bool:
        """Run git silently and report whether it exited successfully."""
        return subprocess.run(
            ["git", *args], cwd=self.cwd,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0

    def interactive(self, *args: str) -> int:
        """Run git with inherited stdio (so editors and prompts work)."""
        return subprocess.run(["git", *args], cwd=self.cwd).returncode

    # -- repository state ------------------------------------------------------

    def is_repository(self) -> bool:
        return self.succeeds("rev-parse", "--git-dir")

    def require_repository(self) -> None:
        if not self.is_repository():
            raise PortError("Not inside a Git repository.")

    def top_level(self) -> str:
        return self.text("rev-parse", "--show-toplevel")

    def git_path(self, name: str) -> str:
        return self.text("rev-parse", "--git-path", name)

    def current_branch(self) -> str:
        """Return the checked-out branch, or an empty string when detached."""
        result = subprocess.run(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            cwd=self.cwd, capture_output=True, text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    def cherry_pick_in_progress(self) -> bool:
        return self.succeeds("rev-parse", "-q", "--verify", "CHERRY_PICK_HEAD")

    def is_worktree_clean(self) -> bool:
        return self.text("status", "--porcelain") == ""

    def has_unresolved_conflicts(self) -> bool:
        return self.text("diff", "--name-only", "--diff-filter=U") != ""

    def ensure_clean_worktree(self) -> None:
        """Require a clean worktree, tolerating an in-progress cherry-pick."""
        if self.cherry_pick_in_progress():
            return
        if not self.is_worktree_clean():
            raise PortError(
                "Working tree is not clean. Commit, stash, or discard changes first."
            )

    # -- inspecting commits ----------------------------------------------------

    def head_subject(self, ref: str) -> str:
        return self.text("log", "-1", "--pretty=%s", ref)

    def head_message(self, ref: str) -> str:
        """Return the full HEAD commit message of ``ref`` (trimmed)."""
        return self.text("log", "-1", "--pretty=%B", ref)

    def head_message_raw(self, ref: str) -> str:
        """Return the full HEAD commit message of ``ref``, verbatim."""
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B", ref],
            cwd=self.cwd, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise PortError(result.stderr.strip() or f"Could not read message of {ref}.")
        return result.stdout

    def branch_exists(self, branch: str) -> bool:
        return self.succeeds("show-ref", "--verify", "--quiet", f"refs/heads/{branch}")

    def has_ref(self, ref: str) -> bool:
        return self.succeeds("rev-parse", "--verify", ref)

    def resolve_commit(self, ref: str) -> Optional[str]:
        """Resolve ``ref`` to a commit SHA, or ``None`` when it cannot."""
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=self.cwd, capture_output=True, text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else None

    # -- mutating the repository -----------------------------------------------

    def switch(self, branch: str) -> bool:
        return self.succeeds("switch", branch)

    def reset_hard(self, ref: str) -> None:
        self.succeeds("reset", "--hard", ref)

    def fetch(self, remote: str, ref: str) -> bool:
        return self.succeeds("fetch", "--no-tags", remote, ref)

    def amend_with_message_file(self, path: str) -> bool:
        return self.succeeds("commit", "--amend", "-F", path)

    def stripspace(self, text: str) -> str:
        """Return ``text`` cleaned up the way ``git`` cleans commit messages."""
        result = subprocess.run(
            ["git", "stripspace"], cwd=self.cwd,
            input=text, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise PortError(result.stderr.strip() or "git stripspace failed.")
        return result.stdout

    def editor_command(self) -> str:
        """Return the editor command Git would use, honouring configuration."""
        command = self.text("var", "GIT_EDITOR")
        if not command:
            raise PortError("git did not return an editor command.")
        return command


def resolve_directory(path: str) -> Optional[str]:
    """Resolve ``path`` to a canonical directory, or ``None`` if it is not one."""
    candidate = Path(path)
    if not candidate.is_dir():
        return None
    return str(candidate.resolve())


# ── Resumable state ────────────────────────────────────────────────────────────


class StateStore:
    """Persists resumable workflow state inside the repository's ``.git`` dir.

    State is stored as a single JSON document under a command-specific namespace
    so that ``--continue`` can pick up exactly where a conflict interrupted the
    run. The document shape is the owning command's concern.
    """

    def __init__(self, git: Git, namespace: str) -> None:
        self._git = git
        self._namespace = namespace

    @property
    def directory(self) -> Path:
        return Path(self._git.git_path(self._namespace))

    @property
    def _file(self) -> Path:
        return self.directory / "state.json"

    def exists(self) -> bool:
        return self._file.is_file()

    def load(self) -> dict:
        if not self.exists():
            raise PortError("No saved state found. Nothing to continue.")
        return json.loads(self._file.read_text())

    def save(self, state: dict) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(state, indent=2) + "\n")

    def clear(self) -> None:
        shutil.rmtree(self.directory, ignore_errors=True)
