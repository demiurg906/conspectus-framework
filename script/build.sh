#!/bin/bash

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
git clone "https://${GH_TOKEN}@github.com/${1}.git" --branch gh-pages --depth=1 ./_site

# clean repo from all files
( cd ./_site && git rm -rf --ignore-unmatch ./* )
( cd ./_site && rm -rf ./* )

# persuade github not to use jekyll
touch ./_site/.nojekyll 2>/dev/null || :

# make the template accessible from current dir
ln -s ./conspectus-framework/ast/template.html 2>/dev/null || :

# using the template, convert source markdown to html + json
mkdir ./input 2>/dev/null || :
find . -maxdepth 1 -name '*md' ! -name 'README.md' -print0 | xargs -n1 --null -t -I {} -- node ./conspectus-framework/ast/index.js {}

# generate the contents, move images & htmls the root folder
python ./conspectus-framework/terms/generate_html.py "${1}" "${2}" . ./_site
cp ./source/*.jpg ./source/*.png ./source/*.svg ./_site 2> /dev/null || :

mkdir -p ./_site/assets
cp ./conspectus-framework/res/*.css ./res/*.js ./_site/assets 2>/dev/null || :

# push generated htmls back to repository
if [ ${GH_TOKEN} ]
then
    cd _site
    git config user.email "no-reply@github.com"
    git config user.name "Travis Bot"
    git add --all
    git commit --amend -m "Travis #$TRAVIS_BUILD_NUMBER"
    git push --force origin gh-pages
    cd ..
fi

# ssh
# echo 'Send gh-pages to mmcs server...'
# ping users.mmcs.sfedu.ru -c1
# echo sshpass -p "$USERS_PASSWD" ssh xamgore@users.mmcs.sfedu.ru '{rm -rf ./public_html; mkdir public_html;}'
# sshpass -p "$USERS_PASSWD" ssh xamgore@users.mmcs.sfedu.ru '{rm -rf ./public_html; mkdir public_html;}'
# echo sshpass -p "$USERS_PASSWD" scp -r ._site/ xamgore@users.mmcs.sfedu.ru:/home/xamgore/public_html
# sshpass -p "$USERS_PASSWD" scp -r ._site/ xamgore@users.mmcs.sfedu.ru:/home/xamgore/public_html
# sshpass -p "$USERS_PASSWD" ssh xamgore@users.mmcs.sfedu.ru '{ rm -rf ./public_html; git clone "https://github.com/xamgore/au-conspectus.git" --branch gh-pages ./public_html; }'


# send notification to telegram chat


git show --name-status --oneline | tail -n +2
message=$(git show --name-status --oneline | tail -n +2 | python ./conspectus-framework/telegram/message_generator.py "${2}")
[[ -z "$TM_TOKEN" ]] || TM_TOKEN="$TM_TOKEN" CHAT='${3}' MSG="$message" node ./conspectus-framework/telegram/index
