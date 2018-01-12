#!/usr/bin/env phantomjs

var fs = require("fs")
var code = fs.read('/dev/stdin');
console.log(eval(code));
phantom.exit();