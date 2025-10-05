#!/usr/bin/env bash

set -euo pipefail

# Colors
bold() { printf "\033[1m%s\033[0m\n" "$*"; }
err() { printf "\033[31m%s\033[0m\n" "$*" 1>&2; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing required command: $1"
    exit 1
  fi
}

require_cmd git
require_cmd uv
require_cmd sed
require_cmd grep

# Args
DEPLOY_ONLY=false
DRY_RUN=false
NO_DEPLOY=false
NO_PUSH=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --deploy-only)
      DEPLOY_ONLY=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --no-deploy)
      NO_DEPLOY=true
      shift
      ;;
    --no-push)
      NO_PUSH=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--deploy-only] [--dry-run] [--no-deploy] [--no-push]"
      exit 0
      ;;
    *)
      err "Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Ensure we're in repo root (file exists)
if [[ ! -f "pyproject.toml" ]]; then
  err "Run this script from the project root (pyproject.toml not found)."
  exit 1
fi

# 1) Check git state: clean and pushed (skip in dry-run)
if [[ "${DRY_RUN}" != "true" ]]; then
  bold "Checking git working tree and upstream..."

  if [[ -n "$(git status --porcelain)" ]]; then
    err "Working tree has uncommitted changes. Commit or stash before deploying."
    exit 1
  fi

  current_branch=$(git rev-parse --abbrev-ref HEAD)
  if ! git rev-parse --abbrev-ref @{upstream} >/dev/null 2>&1; then
    err "No upstream set for branch '${current_branch}'. Run: git push -u origin ${current_branch}"
    exit 1
  fi

  read -r behind ahead < <(git rev-list --left-right --count @{upstream}...HEAD | awk '{print $1, $2}')
  if [[ "${behind}" != "0" ]]; then
    err "Branch is behind upstream by ${behind} commits. Pull/rebase before deploying."
    exit 1
  fi
  if [[ "${ahead}" != "0" ]]; then
    err "Branch has ${ahead} commits not pushed. Push before deploying."
    exit 1
  fi
else
  bold "--dry-run: Skipping git state checks."
fi

if [[ "${DEPLOY_ONLY}" != "true" ]]; then
  # 2) Print current version, prompt for new
  bold "Reading current version from pyproject.toml..."
  current_version=$(grep -E '^[[:space:]]*version[[:space:]]*=[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+"' pyproject.toml | head -n1 | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/')
  if [[ -z "${current_version}" ]]; then
    err "Could not parse current version from pyproject.toml"
    exit 1
  fi
  echo "Current version: ${current_version}"

  read -r -p "Enter new version (semver, must be > current): " new_version

  if [[ ! "${new_version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    err "New version must be semantic (e.g., 0.2.5)"
    exit 1
  fi

  # Compare versions using sort -V
  version_gt() {
    [[ "$1" != "$2" ]] && [[ "$1" == $(printf "%s\n%s\n" "$1" "$2" | sort -V | tail -n1) ]]
  }

  if ! version_gt "${new_version}" "${current_version}"; then
    err "New version (${new_version}) must be greater than current (${current_version})."
    exit 1
  fi

  bold "Updating version to ${new_version} in pyproject.toml..."
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "(dry-run) Would run: uv version ${new_version} --no-sync"
  else
    uv version "${new_version}" --no-sync
  fi

  # Ensure uv.lock is up to date
  bold "Updating uv.lock..."
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "(dry-run) Would run: uv lock"
  else
    uv lock
  fi

  # 4) Compile clean requirements.txt
  bold "Compiling clean requirements.txt (universal, no comments)..."
  require_cmd awk
  set -o pipefail
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "(dry-run) Would generate requirements.txt"
  else
    uv pip compile pyproject.toml --universal | grep -v '^[[:space:]]*#' | sed '/^[[:space:]]*$/d' > requirements.txt
  fi

  # 5) Commit, tag, push
  tag="v${new_version}"
  bold "Committing version bump and requirements, creating tag ${tag} (no push yet)..."
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "(dry-run) Would git add pyproject.toml requirements.txt"
    echo "(dry-run) Would git commit -m 'Release & Deploy: ${tag}'"
    echo "(dry-run) Would git tag -a '${tag}' -m 'Release ${tag}'"
  else
    git add pyproject.toml requirements.txt uv.lock
    git commit -m "Release & Deploy: ${tag}" || true
    git tag -a "${tag}" -m "Release ${tag}"
  fi
else
  bold "--deploy-only: Skipping version bump, requirements compile, and tagging."
fi

# 6) Deploy with Reflex, then push commit/tag IFF deploy succeeds
if [[ "${NO_DEPLOY}" == "true" || "${DRY_RUN}" == "true" ]]; then
  bold "Skipping deploy (${NO_DEPLOY:+--no-deploy }${DRY_RUN:+--dry-run})."
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "(dry-run) Would push commit and tag only after successful deploy"
  fi
else
  bold "Running Reflex deploy..."
  deploy_cmd=(uv run reflex deploy)
  if "${deploy_cmd[@]}"; then
    if [[ "${DEPLOY_ONLY}" != "true" && "${NO_PUSH}" != "true" ]]; then
      bold "Deploy succeeded. Pushing commit and tag..."
      git push
      git push --tags
    else
      bold "Deploy succeeded. Skipping push (${DEPLOY_ONLY:+--deploy-only }${NO_PUSH:+--no-push})."
    fi
  else
    err "Deploy failed. Commit and tag were NOT pushed."
    exit 1
  fi
fi

bold "Done."


