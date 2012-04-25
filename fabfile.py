from fabric.api import *
from fabric.contrib.console import confirm

cfg = dict(
    appengine_dir='appengine-web/src',
    goldquest_dir='src',
    appengine_token='',
)

def update():
    # update to latest code from repo
    local('git pull') 

def test():
    local("nosetests -m 'Test|test_' -w %(goldquest_dir)s" % cfg)
    # jslint
    # pychecker
    # run jasmine tests

def compile():
    # Minimize javascript using google closure.
    local("java -jar ~/bin/compiler.jar --js %(appengine_dir)s/javascript/game.js --js_output_file %(appengine_dir)s/javascript/game.min.js" % cfg)

def deploy_appengine():
    local("appcfg.py --oauth2_refresh_token=%(appengine_token)s update %(appengine_dir)s" % cfg)

def prepare_deploy():
    test()
    compile()

def deploy():
    update()
    prepare_deploy()
    deploy_appengine()
    # tweet about release
