var system = require('system');
if(system.args.length>1){
    eval(system.args[1])
    console.log(eval(system.args[2]));
}
else{
    console.log(0);
}
phantom.exit();
