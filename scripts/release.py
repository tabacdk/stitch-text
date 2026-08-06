#!/usr/bin/env python3
"""Release helper for stitch-text."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
LOCKFILE = ROOT / "uv.lock"
VERSION_RE = re.compile(r'^version = "(\d+)\.(\d+)\.(\d+)(-pre)?"$', re.MULTILINE)


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    pre: bool = False

    @classmethod
    def parse(cls, value: str) -> Version:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(-pre)?", value)
        if not match:
            abort(f"Unsupported version {value!r}; expected x.y.z or x.y.z-pre.")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            pre=match.group(4) is not None,
        )

    def release(self) -> Version:
        return Version(self.major, self.minor, self.patch)

    def next_pre(self) -> Version:
        return Version(self.major, self.minor, self.patch + 1, pre=True)

    def __str__(self) -> str:
        suffix = "-pre" if self.pre else ""
        return f"{self.major}.{self.minor}.{self.patch}{suffix}"


def run(
    args: list[str],
    *,
    dry_run: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(args))
    if dry_run:
        return subprocess.CompletedProcess(args, 0, "", "")
    return subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def abort(message: str) -> None:
    print(f"release: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_project_version() -> Version:
    content = PYPROJECT.read_text(encoding="utf-8")
    match = VERSION_RE.search(content)
    if not match:
        abort("Could not find a supported project.version in pyproject.toml.")
    return Version.parse(match.group(0).split('"')[1])


def write_project_version(version: Version) -> None:
    content = PYPROJECT.read_text(encoding="utf-8")
    updated, replacements = VERSION_RE.subn(f'version = "{version}"', content, count=1)
    if replacements != 1:
        abort("Could not update project.version in pyproject.toml.")
    PYPROJECT.write_text(updated, encoding="utf-8")


def ensure_clean_worktree() -> None:
    status = run(["git", "status", "--porcelain", "--untracked-files=all"]).stdout.strip()
    if status:
        abort(
            "Working tree is not clean. Commit, stash, or remove tracked and non-ignored "
            "changes before releasing.\n\n" + status
        )


def ensure_main_branch() -> None:
    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    if branch != "main":
        abort(f"Releases must be made from main; current branch is {branch!r}.")


def ensure_remote_main_current(remote: str) -> None:
    local = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    remote_result = run(["git", "ls-remote", remote, "refs/heads/main"], check=False)
    if remote_result.returncode != 0:
        abort(remote_result.stderr.strip() or f"Could not check {remote}/main.")
    remote_fields = remote_result.stdout.split()
    if len(remote_fields) < 2:
        abort(f"Could not find refs/heads/main on remote {remote}.")
    remote_head = remote_fields[0]
    if local != remote_head:
        abort(f"Local main is not identical to {remote}/main. Sync main before releasing.")


def ensure_tag_absent(tag: str, remote: str) -> None:
    local = run(["git", "tag", "--list", tag]).stdout.strip()
    if local:
        abort(f"Local tag {tag} already exists.")
    remote_tag = run(["git", "ls-remote", "--tags", remote, f"refs/tags/{tag}"], check=False)
    if remote_tag.returncode != 0:
        abort(remote_tag.stderr.strip() or f"Could not check remote tag {tag}.")
    if remote_tag.stdout.strip():
        abort(f"Remote tag {tag} already exists.")


def ensure_only_version_files_changed() -> None:
    status = run(["git", "status", "--porcelain", "--untracked-files=all"]).stdout.splitlines()
    allowed = {"pyproject.toml", "uv.lock"}
    unexpected = [
        line
        for line in status
        if line[3:] not in allowed or line.startswith("??") or line[:2] not in {" M", "M ", "MM"}
    ]
    if unexpected:
        abort("Unexpected changes after version update:\n\n" + "\n".join(unexpected))


def commit_version(message: str, *, dry_run: bool) -> None:
    ensure_only_version_files_changed()
    run(
        ["git", "add", str(PYPROJECT.relative_to(ROOT)), str(LOCKFILE.relative_to(ROOT))],
        dry_run=dry_run,
    )
    run(["git", "commit", "-m", message], dry_run=dry_run)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Release stitch-text from main.")
    parser.add_argument(
        "--remote",
        default="upstream",
        help="Git remote to push to. Default: upstream.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Execute the release. Default is dry-run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = not args.yes

    ensure_main_branch()
    ensure_clean_worktree()
    ensure_remote_main_current(args.remote)

    current = read_project_version()
    release = current.release()
    next_pre = release.next_pre()
    tag = f"v{release}"
    ensure_tag_absent(tag, args.remote)

    print()
    print(f"Current version: {current}")
    print(f"Release version: {release}")
    print(f"Release tag:     {tag}")
    print(f"Next dev version:{next_pre!s:>8}")
    print(f"Remote:          {args.remote}")
    print("Mode:            " + ("execute" if args.yes else "dry-run"))
    print()

    if dry_run:
        print("Dry-run only. Re-run with --yes to execute.")
        return 0

    write_project_version(release)
    run(["uv", "sync"])
    commit_version(f"Releasing v{release}", dry_run=False)
    run(["git", "push", args.remote, "main"])
    run(["git", "tag", "-a", tag, "-m", f"Release {tag}"])
    run(["git", "push", args.remote, tag])

    write_project_version(next_pre)
    run(["uv", "sync"])
    commit_version(f"Bump version to v{next_pre}", dry_run=False)
    run(["git", "push", args.remote, "main"])

    print(f"Released {tag}; main is now on {next_pre}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
