from fabric.api import *
from fabric.contrib.console import confirm

appengine_dir='appengine-web/src'
goldquest_dir='src'

def update():
    # update to latest code from repo
    local('git pull') 

def test():
    local("nosetests -m 'Test|test_' -w %(path)s" % dict(path=goldquest_dir))
    # jslint
    # pychecker
    # run jasmine tests

def compile():
    # Minimize javascript using google closure.
    local("java -jar ~/bin/compiler.jar --js %(path)s/javascript/game.js --js_output_file %(path)s/javascript/game.min.js" % dict(path=appengine_dir))

def deploy_appengine():
    local("appcfg.py update " + appengine_dir)

def prepare_deploy():
    test()
    compile()

def deploy():
    update()
    prepare_deploy()
    deploy_appengine()
    # tweet about release
