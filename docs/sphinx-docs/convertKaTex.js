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

const fs = require("fs");  // standard node
const jsdom = require("jsdom");  // npm install jsdom
const { JSDOM } = jsdom;

// Need a fake document in order to initialize katex, and it needs to be strict
const DTD = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">';
const empty_dom = new JSDOM(DTD+'\n<html><body></body></html>');
setGlobal('document', empty_dom.window.document);

const path = require("path");
setGlobal('katex', require(path.resolve("./build/html/_static/katex/katex.min")));
const renderMathInElement = require(path.resolve("./build/html/_static/katex/contrib/auto-render.min"));
//setGlobal('katex', require("../../katex.js"));
//const renderMathInElement = require("../auto-render/auto-render");

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

function processHtml(path) {
    JSDOM.fromFile(path).then(dom => {
        console.log("====> processing", path);
        //console.log(dom.serialize());
        setGlobal('document', dom.window.document);
        //console.log(document.compatMode);
        renderMathInElement(dom.window.document.body);
        //console.log(dom.serialize());
        fs.writeFileSync(path, dom.serialize());
    }).catch(console.log.bind(console));
}

function processTree(dir) {
    //console.log(process.argv.slice(2));
    for (const path of walkit(dir, /\.html$/)) {
        processHtml(path);
    }
}

if (typeof require !== 'undefined' && require.main === module) {
    //console.log(process.argv.slice(2));
    for (const arg of process.argv.slice(2)) {
        if (isDir(arg)) {
            processTree(arg);
        } else if (/\.html$/.test(arg)) {
            processHtml(arg);
        }
    }
}
