#!/usr/bin/env bash

# skip if build is triggered by pull request
if [ "$TRAVIS_PULL_REQUEST" == "true" ]; then
  echo "this is PR, exiting"
  exit 0
fi

# enable error reporting to the console
set -e

# cleanup "_site"
rm -rf _site
mkdir _site

echo "${1}"

# clone remote repo to "_site"
repo="https://${GH_TOKEN}@github.com/${1}.git"
git clone "$repo" --branch gh-pages --depth=1 ./_site || {
  git clone "$repo" --depth=1 ./_site;
  git checkout -b gh-pages;
}

# clean repo from all files
( cd ./_site && git rm -rf --ignore-unmatch ./* )
( cd ./_site && rm -rf ./* )

# persuade github not to use jekyll
touch ./_site/.nojekyll 2>/dev/null || :
