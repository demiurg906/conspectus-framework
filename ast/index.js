const path = require('path');
const unified = require('unified');
const remarkParse = require('remark-parse');
const rehypeParse = require('rehype-parse');
const remarkRehype = require('remark-rehype');
const remarkStringify = require('remark-stringify');
const rehypeStringify = require('rehype-stringify');
const rehypeAutolink = require('rehype-autolink-headings');
const rehypeSlug = require('rehype-slug');
const doc = require('rehype-document');
const vfile = require('to-vfile');
const deepClone = require('lodash/fp/cloneDeep');
const math = require('remark-math');
const highlight = require('remark-highlight.js');
const fs = require('fs');

process.argv.length < 3 && (console.log(`node ${path.basename(process.argv[1])} source.md`) || process.exit(0));

var headers = [];
var terms = [];
var description = "";


function addSpanToEmp(options = {}) {
    return (node, file) => { span(node) };

    function span(node) {
        if (node.type == "emphasis") {
            node.type = "html";
            text = node.children[0].value;
            node.value = `<a class="term">${text}</a>`;
            delete node.children;
            terms.push(text)
        }
        else (node.children || []).forEach(span)
    }
}

function print(options = {}) {
  // return tree => { console.log(inspect(tree)) }
  return tree => { console.log(JSON.stringify(tree, null, 2)) }
}

function addTagToList(options = {}) {
    return (node, file) => { tag(node) };

    function tag(node) {
        if (node.type == "element" && node.tagName[0] == "h") {
            tagNumber = parseInt(node.tagName[1]) || 0;
            if ([1,2,3,4,5,6].indexOf(tagNumber) != -1) {
                objHeader = {};
                objHeader.anchor = node.properties.id;
                objHeader.tag = tagNumber;
                for (i = 0; i < node.children.length; ++i) {
                    child = node.children[i];
                    if (child.type == "text") {
                        objHeader.title = child.value
                    }
                }
                headers.push(objHeader)
            }
        }
        else (node.children || []).forEach(tag)
    }
}

function formulasProcessing(options = {}) {
    return (node, file) => { addDollars(node) };

    function addDollars(node) {
        if (node.type == "element" && node.properties.className == "inlineMath")
            for (i = 0; i < node.children.length; ++i) {
                child = node.children[i];
                if (child.type == "text") {
                    text = child.value;
                    child.value = "$" + text + "$"
                }
            }
        else (node.children || []).forEach(addDollars)
    }
}

function exptractDescription(options = {}) {
    return (node, file) => { extract(node) };

    function extract(node) {
        if (node.type == "code" || node.type == "table" ||
            (node.type == "heading" && node.depth == 1))
                return;
        if (node.type == "text" || node.type == "inlineMath")
            description += node.value + " ";
        else
            (node.children || []).forEach(extract)
    }
}


sourceFileName = process.argv[2];
resultFilePath = process.argv[3];
resultFileName = resultFilePath + "/" + process.argv[4];
sourceFile = vfile.readSync(sourceFileName);

unified()
  .use(remarkParse)
  .use(exptractDescription)
  .use(addSpanToEmp)
  .use(math)
  .use(remarkRehype, { commonmark: true, allowDangerousHTML: true })
  .use(rehypeSlug)
  .use(rehypeAutolink)
  .use(addTagToList)
  .use(formulasProcessing)
  .use(highlight)
  .use(rehypeStringify, { allowDangerousHTML: true })
  .process(sourceFile)
  .then(file => {
    file.extname = ".html";
    file.path = "_template/" + file.path;
    vfile.writeSync(file)
  })
  .catch(err => console.log('errors: ', err));

termsFileName = resultFileName.substr(0, resultFileName.lastIndexOf(".")) + ".terms.json";
fs.writeFile(termsFileName, JSON.stringify(terms),
        (err) => { if (err) return console.log(err);});

headersFileName = resultFileName.substr(0, resultFileName.lastIndexOf(".")) + ".headers.json";
fs.writeFile(headersFileName, JSON.stringify(headers),
        (err) => { if (err) return console.log(err);});

descFileName = resultFileName.substr(0, resultFileName.lastIndexOf(".")) + ".desc.txt";
fs.writeFile(descFileName, description.substring(0, 155).replace("\n", ""),
        (err) => { if (err) return console.log(err);});
