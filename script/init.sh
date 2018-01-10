#!/usr/bin/env bash

cd ast
npm i
cd ../telegram
npm i
cd ..

pip install regex lxml requests textile cssselect jinja2