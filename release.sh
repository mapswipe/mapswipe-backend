#!/usr/bin/env bash
# Original https://github.com/orhun/git-cliff/blob/main/release.sh
set -e

REPO_NAME=mapswipe-backend
DEFAULT_BRANCH=develop
# Update this to archive old changelogs
# NOTE: Make sure to also update cliff.toml:footer to includes those archived changelogs as well
START_COMMIT="6d1ebcd644aaae0801e74d24d2b2277952c841d4"


RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_success() {
    echo -e "${GREEN}$1${NC}"
}

log_error() {
    echo -e "${RED}$1${NC}"
}

log_warning() {
    echo -e "${YELLOW}$1${NC}"
}

if ! command -v typos &>/dev/null; then
  log_error "typos is not installed."
  log_error "Run 'cargo install typos-cli' to install it, otherwise the typos won't be fixed"
  exit 1
fi

if ! command -v git-cliff &>/dev/null; then
  log_error "git-cliff is not installed."
  log_error "Follow the instruction from https://git-cliff.org/docs/installation/"
  exit 1
fi

if ! command -v semver &>/dev/null; then
  log_error "semver is required to validate the tag."
  exit 1
fi

if [ ! -d .git ]; then
    log_error "Detected '$REPO_NAME' as a git submodule"
    log_error "Please run this script in a standalone '$REPO_NAME' repository"
    exit 1
fi

current_branch=$(git symbolic-ref --short HEAD 2>/dev/null)
if [ "$current_branch" != "$DEFAULT_BRANCH" ]; then
    log_warning "You are on branch '${current_branch}', not '${DEFAULT_BRANCH}'."
    read -p "Proceed anyway? Y to confirm: " confirm
    if [[ "$confirm" != "Y" ]]; then
        log_error "Aborted by user."
        exit 1
    fi
fi


echo "Existing tags:"
git for-each-ref --sort=-creatordate --format '- %(refname:short)' refs/tags | head -n 10
echo

read -p "Enter new version tag (e.g. v1.2.3, v1.2.3-dev0): " version_tag

# Trim leading/trailing whitespace
version_tag=$(echo "$version_tag" | xargs)

if [ -z "$version_tag" ]; then
    log_error "No version tag provided."
    exit 1
fi

if semver valid "$version_tag" > /dev/null; then
  log_success "Valid SemVer: $version_tag"
else
  log_error "Invalid SemVer: \"$version_tag\""
  exit 1
fi

# Define your cleanup or final function
exit_message() {
    log_warning "-----------------"
    log_warning "If you aren't happy with these changes, try again with"
    log_warning "git reset --soft HEAD~1"
    log_warning "git tag -d $version_tag"
}
trap exit_message EXIT


BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR"

echo "Preparing $version_tag..."
# update the version
msg="# managed by release.sh"
sed -E -i "s/^version = .* $msg$/version = \"${version_tag#v}\"  $msg/" "./pyproject.toml"
uv sync --all-groups --all-extras
git add ./pyproject.toml ./uv.lock

sed -E -i "s/^version: .* $msg$/version: ${version_tag#v}-SET-BY-CICD  $msg/" "./helm/Chart.yaml"
git add ./helm/Chart.yaml

# update the changelog
git-cliff "$START_COMMIT..HEAD" --config cliff.toml --tag "$version_tag" > CHANGELOG.md
git add CHANGELOG.md
git commit -m "chore(release): prepare for $version_tag"
git show

# generate a changelog for the tag message
export GIT_CLIFF_TEMPLATE="\
    {% for group, commits in commits | group_by(attribute=\"group\") %}
    {{ group | upper_first }}\
    {% for commit in commits %}
        - {% if commit.breaking %}(breaking) {% endif %}{{ commit.message | upper_first }} ({{ commit.id | truncate(length=7, end=\"\") }})\
    {% endfor %}
    {% endfor %}"
changelog=$(git-cliff "$START_COMMIT..HEAD" --config detailed.toml --unreleased --strip all)

# create a signed tag
# https://keyserver.ubuntu.com/pks/lookup?search=0x4A92FA17B6619297&op=vindex
git tag "$version_tag" -m "Release $version_tag" -m "$changelog"
git tag -v "$version_tag"
log_success "Done!"
log_success "You can now push the tag (git push origin $version_tag)"
log_success "If the github workflow works as expected, push the commit (git push) to default branch"
