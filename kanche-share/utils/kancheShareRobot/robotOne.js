require('shelljs/global');
var fs = require('fs');
var path = require('path');
var mongojs = require('mongojs');

var db = mongojs('kanche');
var share_job = db.collection('share_job');

var workList = new Array();
var sendTarget;
var limit = 2;
var siteName = '58.com';
var NOW_PATH = "";

function tailWatch(){


	// 监控文件
	Tail = require('tail').Tail;
	tail = new Tail(NOW_PATH+"/log/share_log.txt");
	tail.on("line", function(data) {

		var resSuccess = data.match(/\"message\": \"http:\/\//); //没有使用g选项   
		var resError = data.match(/ERROR/);

		if (resSuccess) {
			console.log(resSuccess)
			var datetime = new Date();
			var logString = "====================\n";
			logString += siteName + " NO." + limit + " " + datetime.toISOString() +"\n";
			logString += sendTarget._id + "\n";
			logString += sendTarget.vehicle.spec.brand +" " + sendTarget.vehicle.spec.series 
			+" " + sendTarget.vehicle.spec.sale_name + "\n";
			logString += data + "\n";
			logString += "====================\n\n";
			// write to file

			fs.appendFile(NOW_PATH+"/utils/kancheShareRobot/report.txt", logString, function(err) {
	    	if(err) {
	        console.log(err);
	    	} else {
	        console.log("==============");
	        console.log("send vehicle success");
	        console.log("==============");

	        randRunSomeOne();

	    	}
			}); 
		};

		if (resError) {
			console.log(resError);
			var datetime = new Date();
			var logString = "=========ERROR===========\n";
			logString += siteName + " NO." + limit + " " + datetime.toISOString() +"\n";
			logString += sendTarget._id + "\n";
			logString += sendTarget.vehicle.spec.brand +" " + sendTarget.vehicle.spec.series +" " + sendTarget.vehicle.spec.sale_name + "\n";
			logString += data + "\n";
			logString += "==========ERROR==========\n\n";
			// write to file
		};

	  console.log(data);
	});

}


function process_args_build(){
	// process 处理参数
	process.stdin.resume();
	process.stdin.setEncoding('utf8');

	NOW_PATH = process.cwd();

	tailWatch();
	
	process.argv.forEach(function(val, index, array) {
	  console.log(index + ': ' + val);
	});


	var args = process.argv;

	siteName = args[2];
	limit = args[3]

	share_job
	.find({'share_account.website':siteName, external_vehicle_spec: { $exists: true }},function(err, docs){
		for (var i = 0; i < docs.length; i++) {
			var oneJob = docs[i];
			workList.push(oneJob);
		};
		// console.log(workList);

		randRunSomeOne();
	});
}

function randRunSomeOne(){
	// run next
	if (limit > 0) {
		sendTarget = workList[Math.floor(Math.random() * workList.length)];
		console.log("sendTarget._id");
		console.log(sendTarget._id);
		sendVehicle(sendTarget);
		limit = limit - 1;
	}else{
		process.exit(0);
	}
}

function sendVehicle(shareJobItem){
	share_job.findAndModify({
	  query: { _id: mongojs.ObjectId(shareJobItem._id) },
	  update: { $set: { status:'pending' } },
	  new: true
	}, function(err, doc, lastErrorObject) {
	    // doc.tag === 'maintainer'
	});
}


process_args_build();
