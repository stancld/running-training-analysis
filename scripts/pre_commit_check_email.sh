#!/usr/bin/env bash
set -euo pipefail

ALLOWED_EMAIL_REGEX='^daniel\.stancl@gmail\.com$'

ident="$(git var GIT_AUTHOR_IDENT 2>/dev/null || true)"
email="$(printf '%s\n' "${ident}" | sed -n 's/.*<\([^>]*\)>.*/\1/p')"

if ! printf '%s' "${email}" | grep -Eq "${ALLOWED_EMAIL_REGEX}"; then
  echo "ERROR: author email '${email}' is not the personal address for this repo." >&2
  echo "  git config --local user.email daniel.stancl@gmail.com" >&2
  exit 1
fi
