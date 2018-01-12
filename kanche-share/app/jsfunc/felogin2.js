#!/usr/bin/env phantomjs

phantom.cookiesEnabled = true
var fs = require("fs")
var page = require('webpage').create();

//var data_in = fs.read('/dev/stdin');
//var data = JSON.parse(data_in)
//console.log(JSON.stringify(data))

page.open('file:///Users/triplex/Source/kkche/kkche-share/jsfunc/fe.html', function(status) {
  if (status !== 'success') {
    console.log('Unable to access passport login');
  } else {
    var ua = page.evaluate(function(status, data) {
     	var pts = 1404752079652;
      var password = "asasas";
    	//var timespan = pts - new Date().getTime();
    	var timesign = 1404753101972;
    	var p1 = getm32str(password, timesign + "");
    	var p2 = getm16str(password, timesign + "");
    	var p3 = encryptString(timesign + encodeURIComponent(password), "010001", "008baf14121377fc76eaf7794b8a8af17085628c3590df47e6534574efcfd81ef8635fcdc67d141c15f51649a89533df0db839331e30b8f8e4440ebf7ccbcc494f4ba18e9f492534b8aafc1b1057429ac851d3d9eb66e86fce1b04527c7b95a2431b07ea277cde2365876e2733325df04389a9d891c5d36b7bc752140db74cb69f") 
    	return {"timesign": timesign, "p1": p1, "p2":p2, "p3":p3, "pts": pts}
    }, function (err, anydata) {
    }, null);
    console.log(JSON.stringify(ua));
  }
  phantom.exit();
});