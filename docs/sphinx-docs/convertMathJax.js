#!/usr/bin/env node
// Usage:
//    npm install jsdom
//    node convertTree.js build/html
/* eslint no-console:0 */
/* global katex */
"use strict";

/**
 * Set a global variables name to value.
 */
function setGlobal(name, value) {
    (function(globals) { globals[name] = value; }((1, eval)('this')));
}

const fs = require("fs");
//const await = require("await");
const mjpage = require('mathjax-node-page').mjpage;

function isDir(path) {
    const stat = fs.statSync(path);
    return (stat && stat.isDirectory());
}

/**
 * Walk a directory tree, yielding a list of matching filenames
 *
 * @param {path} dir - root of the tree which is walked
 * @param {regex} [pattern] - regular expression match for the full path
 */
function* walkit(dir, pattern = /./) {
    const _walk = function* (dir) {
        const entries = fs.readdirSync(dir);
        for (const entry of entries) {
            const path = dir + "/" + entry;
            if (isDir(path)) {
                //console.log('walking '+path);
                yield* _walk(path);
            } else if (pattern.test(path)) {
                //console.log('yielding '+path);
                yield path;
            }
        }
    };
    yield* _walk(dir);
}

function readFileAsync(path) {
    return new Promise((resolve, reject) =>
        fs.readFile(path, (err, data) => {
            if (err) { reject(err); } else { resolve(data); }
        }));
}

function writeFileAsync(path, data) {
    return new Promise((resolve, reject) =>
        fs.writeFile(path, data, (err) => {
            if (err) { reject(err); } else { resolve(data); }
        }));
}

const pageConfig = {
    format: ["TeX"],
    //output: 'html',
    output: 'svg',
    fontURL: 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js/fonts/HTML-CSS',
    MathJax: {
            //config: ["MMLorHTML.js"],
            //jax: ["input/TeX","input/MathML","output/HTML-CSS",
            //      "output/NativeMML", "output/PreviewHTML"],
            jax: ["input/TeX", "output/HTML-CSS"],
            //extensions: ["tex2jax.js","mml2jax.js","MathMenu.js",
            //             "MathZoom.js", "fast-preview.js",
            //             "AssistiveMML.js", "a11y/accessibility-menu.js"
            //            ],
            extensions: ["tex2jax.js"],
            TeX: {
                extensions: ["AMSmath.js","AMSsymbols.js",
                             "noErrors.js","noUndefined.js"]
            }
    }
}
const mjnodeConfig = {
  ex: 6, // ex-size in pixels
  width: 100, // width of math container (in ex) for linebreaking and tags
  fragment: false,
  useFontCache: true, // use <defs> and <use> in svg output?
  useGlobalCache: false, // use common <defs> for all equations?
  //state: mjstate, // track global state
  linebreaks: false, // do linebreaking?
  equationNumbers: "none", // or "AMS" or "all"
  //math: "", // the math to typeset
  html: true, // generate HTML output?
  css: true, // generate CSS for HTML output?
  //mml: false, // generate mml output?
  //svg: false, // generate svg output?
  //speakText: true, // add spoken annotations to output?
  //timeout: 10 * 1000, // 10 second timeout before restarting MathJax
}
function mjpageAsync(input, pageConfig, mjnodeConfig) {
    return new Promise((resolve, reject) =>
        mjpage(input, pageConfig, mjnodeConfig, output => resolve(output))
    );
}
async function updateHtmlAsync(path) {
  try {
    console.log("====> processing", path);
    const input = await readFileAsync(path);
    const output = await mjpageAsync(input, pageConfig, mjnodeConfig);
    return await writeFileAsync(path, output);
  } catch (err) {
    console.log(err);
  }
}

async function processTreeAsync(dir) {
    //console.log(dir);
    for (const path of walkit(dir, /\.html$/)) {
        await updateHtmlAsync(path);
    }
}

async function mainAsync(args) {
    //console.log(process.argv.slice(2));
    for (const arg of args) {
        if (isDir(arg)) {
            processTreeAsync(arg);
        } else if (/\.html$/.test(arg)) {
            updateHtmlAsync(arg);
        }
    }
}


function updateHtmlSortOfSync(path) {
    console.log("====> loading", path);
    const input = fs.readFileSync(path);
    //const pageConfig = {format: ['TeX']}
    //const mjnodeConfig = {html: true}
    mjpage(input, pageConfig, mjnodeConfig,
            //output => console.log(output));
            output => {
                console.log("====> processed", path);
                fs.writeFileSync(path, output)
            });
}

function processTreeSortOfSync(dir) {
    //console.log(dir);
    for (const path of walkit(dir, /\.html$/)) {
        updateHtmlSortOfSync(path);
    }
}

function mainSortOfSync(args) {
    //console.log(process.argv.slice(2));
    for (const arg of args) {
        if (isDir(arg)) {
            processTreeSortOfSync(arg);
        } else if (/\.html$/.test(arg)) {
            updateHtmlSortOfSync(arg);
        }
    }
}

if (typeof require !== 'undefined' && require.main === module) {
    console.log(mainAsync(process.argv.slice(2)));
}
