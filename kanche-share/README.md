kanche-share
============

kanche sharer

curl 'http://localhost:3011/login/check?site=58.com&username=13717832817&password=asasas'  
// mac osx install  
// OSX 10.9.2 with xcode  

1. sudo easy_install pip
2. sudo pip install virtualenv
3. sh install.sh

// if you install xcode  
3.x CPATH=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.9.sdk/usr/include/libxml2 CFLAGS=-Qunused-arguments CPPFLAGS=-Qunused-arguments sh install.sh

4. brew install mongo
5. brew services start mongodb

// phantomjs for 58.com  
6. brew install phantomjs

Make a virtual environment
--------------------------
first time:

    pip install virtualenvwrapper
    mkvirtualenv kanche-share
    workon kanche-share
    pip install -r requirements.txt

exit the virtual env:

    deactivate

work on the virtual env:

    workon kanche-share


Auto Deploy
------------
run every 10 minutes

    export SHARE_PASS=
    crontab -e
    */10 * * * * cd /full-path/project-dir && /virtualenvpython/bin/python auto_deploy.py >> cron_auto_deploy.log 2>&1


