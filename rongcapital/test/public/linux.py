#-*- coding: UTF-8 -*-
import paramiko
from urllib import urlretrieve
import urllib
import sys
reload(sys)
sys.setdefaultencoding('utf8')

def codeMain():
    port = 22
    #cmd = "egrep 'redis缓存中的值' /mydata/website/tomcat-oprsystemDynamic-8145/rkylin-robot-platform-logs/rkylin-robot-platform-web-logs/rkylin-robot-platform-web/robot.log | awk '{printf \"%s\",$6}'"
    cmd = "egrep 'http://123.56.79.58:8145/filesServer/downLoad/temp' /mydata/website/tomcat-oprsystemDynamic-8145/rkylin-robot-platform-logs/rkylin-robot-platform-web-logs/rkylin-robot-platform-web/robot.log | awk '{printf \"%s\",$3}'"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshd = ssh_connect('123.56.79.58','mwnadmin','036K29754D64qgv')
    stdin, stdout, stderr = ssh_exec_cmd(sshd, cmd)
    err_list = stderr.readlines()
    if len(err_list) > 0:
        print 'ERROR:' + err_list[0]
        exit()
    for item in stdout.readlines():
        code = item[-90:-3]
        urllib.urlretrieve(code,'/Users/qinying/PycharmProjects/rongcapital/test/public/a.jpg')
        return code

def ssh_connect(_host, _username, _password):
    try:
        _ssh_fd = paramiko.SSHClient()
        _ssh_fd.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _ssh_fd.connect(_host, username=_username, password=_password)
    except Exception, e:
        print('ssh %s@%s: %s' % (_username, _host, e))
        exit()
    return _ssh_fd

def ssh_exec_cmd(_ssh_fd, _cmd):
    return _ssh_fd.exec_command(_cmd)

def ssh_exec_cmd(_ssh_fd, _cmd):
    return _ssh_fd.exec_command(_cmd)
if __name__ == '__main__':
    codeMain()