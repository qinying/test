#!/usr/bin/env phantomjs

phantom.cookiesEnabled = true
var fs = require("fs")
var page = require('webpage').create();

var data_in = fs.read('/dev/stdin');
var data = JSON.parse(data_in)
//console.log(JSON.stringify(data))
var absoluteScriptPath = fs.absolute('./');
var absoluteScriptDir = absoluteScriptPath.substring(0, absoluteScriptPath.lastIndexOf('/'));
//console.log(absoluteScriptDir)
page.open('file://' + absoluteScriptDir + '/app/jsfunc/fe.html', function(status) {
  if (status !== 'success') {
    console.log('Unable to access passport login');
  } else {
    var ua = page.evaluate(function(status, data) {
     	var pts = parseInt(data.pts);
      var password = data.password;
    	var timespan = pts - new Date().getTime();
    	var timesign = new Date().getTime() + timespan;
    	var p1 = getm32str(password, timesign + "");
    	var p2 = getm16str(password, timesign + "");
    	var p3 = encryptString(timesign + encodeURIComponent(password), data.salt, data.key) 
    	return {"timespan": timespan, "timesign": timesign, "p1": p1, "p2":p2, "p3":p3, "pts": data.pts}
    }, function (err, anydata) {
    }, data);
    console.log(JSON.stringify(ua));
  }
  phantom.exit();
});