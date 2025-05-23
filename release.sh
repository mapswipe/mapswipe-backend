#!/usr/bin/env bash
# Original https://github.com/orhun/git-cliff/blob/main/release.sh
set -e

# Update this to archive old changelogs
# NOTE: Make sure to also update cliff.toml:footer to includes those archvied changelogs as well
START_COMMIT="6d1ebcd644aaae0801e74d24d2b2277952c841d4"

if ! command -v typos &>/dev/null; then
  echo "typos is not installed. Run 'cargo install typos-cli' to install it, otherwise the typos won't be fixed"
fi

if ! command -v semver &>/dev/null; then
  echo "semver is required to validate the tag."
fi

version_tag="$1"

if [ -z "$version_tag" ]; then
    echo "Please provide a tag."
    echo "Usage: ./release.sh v[X.Y.Z]"
    exit
fi

if semver valid "$version_tag" > /dev/null; then
  echo "Valid SemVer: $version_tag"
else
  echo "Invalid SemVer: \"$version_tag\"" >&2
  echo "Eg: 0.1.1 0.1.1-dev0"
  exit 1
fi

# Define your cleanup or final function
exit_message() {
    echo "-----------------"
    echo "If you aren't happy with these changes. try again with"
    echo "git reset --soft HEAD~1"
    echo "git tag -d $version_tag"
}
trap exit_message EXIT


BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR"

echo "Preparing $version_tag..."
# update the version
msg="# managed by release.sh"
sed -E -i "s/^version = .* $msg$/version = \"${version_tag#v}\"  $msg/" "./pyproject.toml"
uv sync
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
echo "Done!"
echo "Now push the commit (git push) and the tag (git push --tags)."
