//由phantomjs根据url生成图片

// create_port.js

var page = require('webpage').create();
var system = require('system');

page.settings.userAgent = 'WebKit/534.46 Mobile/9A405 Safari/7534.48.3';
page.settings.viewportSize = { width: 1000, height: 1070 };
var URL = system.args[1];
console.log(URL)
var size = system.args[2];

page.open(URL, function (status) {
    if (status !== 'success') {
    console.log('Unable to load!');
    phantom.exit();
  } else {
      page.zoomFactor = size;
      var title = 'testport';

      //window.setTimeout(function () {
        page.clipRect = { top: 0, left: 0, width: 1000, height: 1070 };
        page.render(title + ".jpg");
        //var pic64 = page.renderBase64();
        //return pic64;
        phantom.exit();
    //}, 1000);
     }
});


//var page = require('webpage').create();
//var system = require('system');
//var url, output, size; //
//
//if (system.args.length < 3 || system.args.length > 5) {
//    console.log('Usage: createPic.js URL filename [paperwidth*paperheight|paperformat] [zoom]');
//    console.log('  paper (pdf output) examples: "5in*7.5in", "10cm*20cm", "A4", "Letter"');
//    phantom.exit(1);
//} else {
//        url = system.args[1];
//        output = system.args[2];
//        page.viewportSize = { width: 600, height: 600 };
//
//        if (system.args.length > 3 && system.args[2].substr(-4) === ".pdf") {
//            size = system.args[3].split('*');
//            page.paperSize = size.length === 2 ? { width: size[0], height: size[1], margin: '0px' }
//                : { format: system.args[3], orientation: 'portrait', margin: '1cm' };
//        }
//
//        if (system.args.length > 4) {
//            page.zoomFactor = system.args[4];
//        }
//
//        page.open(url, function (status) {
//        if (status !== 'success') {
//            console.log('Unable to load the url!');
//            phantom.exit();
//        } else {
//            window.setTimeout(function () {
//            page.render(output);
//            phantom.exit();
//            });
//        }
//    });
//
//}