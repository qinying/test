# -*- coding: utf-8 -*-
import os
import shelve
import subprocess
from git import Repo
import pymongo
from app import config


password = os.environ.get("SHARE_PASS", "")


class Deploy(object):
    def __init__(self):
        current_dir = os.path.dirname(__file__)
        self.deploy_file = os.path.abspath(
            os.path.join(current_dir, "deploy.db"))
        self.stop_script = "sh " + os.path.abspath(
            os.path.join(current_dir, "stop_restarter.sh"))
        self.start_script = "sh " + os.path.abspath(
            os.path.join(current_dir, "start_restarter.sh"))
        self.test_script = "sh " + os.path.abspath(
            os.path.join(current_dir, "test.sh"))
        self.repo = Repo(current_dir)
        assert not self.repo.bare

    def pull(self):
        self.repo.remotes.origin.pull()

    def is_master(self):
        return self.repo.head.ref == self.repo.heads.master

    def current_hexsha(self):
        return self.repo.head.ref.commit.hexsha

    def write_hexsha(self):
        s = shelve.open(self.deploy_file)
        try:
            s["hexsha"] = self.current_hexsha()
        finally:
            s.close()

    def get_hexsha(self):
        s = shelve.open(self.deploy_file)
        try:
            return s["hexsha"]
        except Exception:
            return ""
        finally:
            s.close()

    def handing_data_2_pending(self):
        try:
            conn = pymongo.Connection(config.mongoServer, tz_aware=True)
            db = conn["kanche"]
            collection = db["share_job"]
            collection.update({"status": "handling"},
                              {"$set": {"status": "pending"}},
                              multi=True)
        except Exception as e:
            print e
        finally:
            conn.close()

    def sudo_execute(self, command, password):
        proc = subprocess.Popen(["sudo", "-p", "", "-S"] + command.split(),
                                stdin=subprocess.PIPE)
        proc.stdin.write(password + "\n")
        proc.stdin.close()
        proc.wait()

    def restart_service(self):
        os.popen(self.stop_script, "w")
        self.sudo_execute(self.start_script, password)
        # self.sudo_execute(self.test_script, password)

    def deploy(self):
        if self.is_master():
            self.pull()
            if not self.get_hexsha():
                self.write_hexsha()
            else:
                if self.get_hexsha() != self.current_hexsha():
                    print "Deploy start."
                    self.restart_service()
                    self.handing_data_2_pending()
                    self.write_hexsha()
                    print "Deploy done."
                else:
                    print "No pull from master found."
        else:
            print "Not in master branch."


if __name__ == "__main__":
    d = Deploy()
    d.deploy()
