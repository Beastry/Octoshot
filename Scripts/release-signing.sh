#!/bin/bash
# Sourced by package.sh. Keep authentication selection testable without building,
# touching a real keychain, or contacting Apple. Never enable shell tracing here.

configure_release_signing() {
  SIGN_IDENTITY="${DEVELOPER_ID_IDENTITY:-${SIGN_IDENTITY:-}}"
  if [ -z "$SIGN_IDENTITY" ]; then
    if [ -n "${KEYCHAIN_PATH:-}" ]; then
      SIGN_IDENTITY=$(security find-identity -v -p codesigning "$KEYCHAIN_PATH" | grep -o '"Developer ID Application:[^"]*"' | head -1 | tr -d '"' || true)
    else
      SIGN_IDENTITY=$(security find-identity -v -p codesigning | grep -o '"Developer ID Application:[^"]*"' | head -1 | tr -d '"' || true)
    fi
  fi
  [ -n "$SIGN_IDENTITY" ] || { echo "No Developer ID Application identity found" >&2; return 1; }

  # The toolkit supplies whitespace-separated flags, never shell code or paths.
  # Keep KEYCHAIN_PATH separate so paths containing spaces remain one argument.
  read -r -a RELEASE_CODESIGN_FLAGS <<< "${CODESIGN_FLAGS:---options runtime --timestamp}"
  NOTARIZE=false
  if [ -n "${ASC_API_KEY_PATH:-}${ASC_API_KEY_ID:-}${ASC_API_ISSUER_ID:-}" ]; then
    if [ -z "${ASC_API_KEY_PATH:-}" ] || [ ! -f "$ASC_API_KEY_PATH" ] || [ ! -r "$ASC_API_KEY_PATH" ] ||
       [ -z "${ASC_API_KEY_ID:-}" ] || [ -z "${ASC_API_ISSUER_ID:-}" ]; then
      echo "ASC API notarization requires a readable key file, key ID, and issuer ID" >&2
      return 1
    fi
    NOTARY_AUTH=(--key "$ASC_API_KEY_PATH" --key-id "$ASC_API_KEY_ID" --issuer "$ASC_API_ISSUER_ID")
    NOTARIZE=true
  else
    NOTARY_PROFILE="${NOTARY_PROFILE-Octoshot-notary}"
    if [ -n "$NOTARY_PROFILE" ]; then
      NOTARY_AUTH=(--keychain-profile "$NOTARY_PROFILE")
      NOTARIZE=true
    fi
  fi
}

release_codesign() {
  if [ -n "${KEYCHAIN_PATH:-}" ]; then
    codesign --force --sign "$SIGN_IDENTITY" --keychain "$KEYCHAIN_PATH" "$@"
  else
    codesign --force --sign "$SIGN_IDENTITY" "$@"
  fi
}

sign() { release_codesign "${RELEASE_CODESIGN_FLAGS[@]}" "$@"; }

notarize() {
  local file="$1" log="$DIST/notary-$(basename "$1").log" i
  for i in 1 2 3; do
    if xcrun notarytool submit "$file" "${NOTARY_AUTH[@]}" --wait --timeout 90m 2>&1 | tee "$log"; then
      grep -q "status: Accepted" "$log" && return 0
      grep -qi "not found\|keychain" "$log" || break
    fi
    echo "↻ retrying notarytool ($i)…"; sleep 3
  done
  echo "Notarization failed; inspect the notary log using the configured authentication" >&2
  return 1
}
