# au-conspectus <a href="https://travis-ci.org/xamgore/au-conspectus/builds"><img src="https://travis-ci.org/xamgore/au-conspectus.svg?branch=master" alt="build status"></a>

This repository is a storage of all notes written by [@xamgore](https://github.com/xamgore), [@demiurg906](https://github.com/demiurg906) and [@AlexandraOlegovna](https://github.com/AlexandraOlegovna). We are students of the Saint Petersburg Academic University, whose courses records are kept.

In order to synchronize our work and simplify the verification and publication, we decided to write a pipeline that would generate a site with materials. We tried to make it so that our classmates could easily report errors or make changes there. We also made a telegram bot, which notifies that a new lecture was added to the site.

While preparing for exams, it is important to re-read the material. We highlight important terms in the text, so when you click on them, an illustration with brief information appears — it's easier to recall what this term means and how it is applied in the current context. If this is not enough, one can use the fuzzy search on the site.

## Installation

### Local machine

* Run `./script/init.sh` to install all required pacakges
* Put your documents into `source` folder
* Run `python3 ./script/build.py` to generate your docs. All pages will be collected in `site` directory

### Travis

Switch on the project on https://travis-ci.org/, like on the image:

![](https://i.imgur.com/nskScTv.png)

Set the following variables for Travis, on the project page → "settings" → "Environment Variables":

* `GH_TOKEN` — a [personal access token](https://help.github.com/articles/creating-an-access-token-for-command-line-use/) with the `public_repo` or `repo` scope (`repo` is required for private repositories).
* `TM_TOKEN` — telegram api token, you can ask @BotFather for it.

Edit the `config.json` file, there should be the repository name, repo holder, and other information.

## How it works

We build the AST from the markup files, make the transformations over it, extract useful information (like headers, terms, function names) and then convert to the HTML AST. At this point we also do some useful preparations (for math and syntax highlighting) and then convert everything to HTML. Extra information is stored in separate JSON files. Thanks to [@AlexandraOlegovna](https://github.com/AlexandraOlegovna), she did this part of the project perfectly.

Then we need to generate the contents, wrap lectures by shiny templates, find the meaning of terms on the internet, detect which files were updated and how — all this work was done in python scripts by [@demiurg906](https://github.com/demiurg906). He is really a cool guy with strong python experience. The remaining tasks: the telegram bot, set up of the continuous integration service, frontend stuff — were made by [@xamgore](https://github.com/xamgore).
