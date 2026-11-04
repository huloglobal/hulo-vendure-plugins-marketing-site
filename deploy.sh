#!/usr/bin/env bash
#
# Build → push huloglobal.com/vendure-plugins/*
#
#   1. Auto-fetches the current versions from npm so version chips stay
#      in sync with what customers will actually `yarn add`.
#   2. Builds the static pages and the manuals.
#   3. Tars + SCPs to the huloglobal box, atomically replaces the
#      live directory, fixes permissions.
#   4. If there are local changes to build.py / build_manuals.py / this
#      script itself, commits them with a sensible default message and
#      pushes to GitHub.
#
# Usage:
#
#     ./deploy.sh                # build + deploy + auto-commit
#     ./deploy.sh "commit msg"   # use a specific commit message
#     ./deploy.sh --no-commit    # skip the commit + push step
#
# Required env (already present on the build box):
#
#     SSHPASS or an SSH agent with the huloglobal box key
#
set -euo pipefail
cd "$(dirname "$0")"

MSG=""
DO_COMMIT=1
for arg in "$@"; do
    case "$arg" in
        --no-commit) DO_COMMIT=0 ;;
        *) MSG="$arg" ;;
    esac
done

BOX=root@192.168.1.33
ROOT=/var/www/huloglobal/current/dist/client

echo "→ Build"
# HULO_BUILD_DATE=YYYY-MM-DD ./deploy.sh measures the changelog "New" pills
# from that day instead of today.
python3 build.py
python3 build_manuals.py
python3 build_legal.py
python3 build_wordpress.py
# Stylesheet for all generated pages, compiled from huloglobal.com's
# Tailwind theme against the HTML just written (see build_css.mjs).
node build_css.mjs

echo
echo "→ Tar"
TARBALL=$(mktemp -t hulo-vp-XXXX.tgz)
tar czf "$TARBALL" -C dist vendure-plugins wordpress-plugins legal

echo "→ Upload to $BOX"
if [[ -n "${SSHPASS:-}" ]]; then
    sshpass -e scp -q -o StrictHostKeyChecking=no "$TARBALL" "$BOX:/tmp/vp-pages.tgz"
    sshpass -e ssh -q -o StrictHostKeyChecking=no "$BOX" "
        set -e
        rm -rf $ROOT/vendure-plugins $ROOT/wordpress-plugins $ROOT/legal
        tar xzf /tmp/vp-pages.tgz -C $ROOT
        chown -R huloglobal:huloglobal $ROOT/vendure-plugins $ROOT/wordpress-plugins $ROOT/legal
        chmod +x $ROOT/vendure-plugins/*/install.sh
        rm /tmp/vp-pages.tgz
    "
else
    scp -q "$TARBALL" "$BOX:/tmp/vp-pages.tgz"
    ssh -q "$BOX" "
        set -e
        rm -rf $ROOT/vendure-plugins $ROOT/wordpress-plugins $ROOT/legal
        tar xzf /tmp/vp-pages.tgz -C $ROOT
        chown -R huloglobal:huloglobal $ROOT/vendure-plugins $ROOT/wordpress-plugins $ROOT/legal
        chmod +x $ROOT/vendure-plugins/*/install.sh
        rm /tmp/vp-pages.tgz
    "
fi
rm "$TARBALL"

echo
echo "→ Verify live"
for url in \
    "https://huloglobal.com/vendure-plugins/" \
    "https://huloglobal.com/wordpress-plugins/" \
    "https://huloglobal.com/wordpress-plugins/geo-block/" \
    "https://huloglobal.com/wordpress-plugins/geo-block-pro/update.json" \
    "https://huloglobal.com/vendure-plugins/email-tracking/" \
    "https://huloglobal.com/vendure-plugins/geo-block/" \
    "https://huloglobal.com/vendure-plugins/visitor-analytics/" \
    "https://huloglobal.com/vendure-plugins/email-tracking/docs/" \
    "https://huloglobal.com/vendure-plugins/geo-block/docs/" \
    "https://huloglobal.com/vendure-plugins/visitor-analytics/docs/" \
    "https://huloglobal.com/vendure-plugins/fraud-prevention/" \
    "https://huloglobal.com/vendure-plugins/roadmap/" \
    "https://huloglobal.com/vendure-plugins/quotations/" \
    "https://huloglobal.com/vendure-plugins/quotations/changelog/" \
    "https://huloglobal.com/vendure-plugins/email-tracking/changelog/" \
    "https://huloglobal.com/vendure-plugins/fraud-prevention/changelog/" \
    "https://huloglobal.com/vendure-plugins/review-requests/changelog/" \
    "https://huloglobal.com/vendure-plugins/fraud-prevention/docs/" \
    "https://huloglobal.com/vendure-plugins/review-requests/" \
    "https://huloglobal.com/vendure-plugins/review-requests/docs/" \
    "https://huloglobal.com/legal/" \
    "https://huloglobal.com/legal/terms/" \
    "https://huloglobal.com/legal/privacy/" \
    "https://huloglobal.com/legal/cookies/" \
    "https://huloglobal.com/legal/acceptable-use/"
do
    status=$(curl -sSI -m 8 "$url" | head -1 | tr -d '\r')
    echo "  $status  $url"
done

if [[ "$DO_COMMIT" == "0" ]]; then
    echo
    echo "(--no-commit set, skipping git push)"
    exit 0
fi

echo
echo "→ Git"
# static/ holds the shared client code (hulo-ui.js / hulo-ui.css) and logos;
# git status (not git diff) so new, untracked files there are committed too.
SOURCES="build.py build_manuals.py build_legal.py build_wordpress.py build_css.mjs build_thumbs.mjs deploy.sh README.md static .github"
if [[ -n "$(git status --porcelain -- $SOURCES 2>/dev/null)" ]]; then
    git add $SOURCES 2>/dev/null || true
    if [[ -z "$MSG" ]]; then
        MSG="Deploy marketing site — $(date -u +%Y-%m-%d)"
    fi
    git commit -m "$MSG"
    git push
    echo "  pushed: $(git rev-parse --short HEAD)"
else
    echo "  no local changes — nothing to commit"
fi
