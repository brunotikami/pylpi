# coding:utf-8

from fabric.api import cd, env, parallel, run, sudo, put, roles, prefix, local
from fabric.context_managers import settings
from fabric.contrib.files import append, contains, exists
from fabric.decorators import runs_once

env.repository = 'git@github.com:brunotikami/pylpi'
env.project_name = 'pylpi'
env.user = 'deployer'
env.user_home = '/home/%s' %env.user
env.project_path = '%s/%s' %(env.user_home, env.project_name)
env.supervisor_program = env.project_name
env.forward_agent = True
env.venv_path = '%s/.venv' % env.project_path
env.packages_storage_path = '/packages/pypi'

def production():
    
    env.name = 'production'
    env.hosts = [
        #'pypi.essential.aws1a.titansgroup.net',
        '10.0.254.17',
    ]
    env.gateway = 'deployer@ec2-54-232-196-115.sa-east-1.compute.amazonaws.com'

def install_server_os_packages():
    """
    Setup server applications
    """
    # Update the server packages
    sudo('apt-get update')

    # Install build dependencies
    sudo('apt-get install -y --force-yes build-essential git')

    # Python distribute, pip, virtualenv, python headers and needed libs for requirements
    sudo('apt-get install -y --force-yes python-dev libncurses5-dev python-distribute python-pip python-dev libjpeg8-dev libfreetype6-dev liblcms1-dev gettext')
    sudo('pip install virtualenv')

    # NGINX - install from official PPA
    sudo('add-apt-repository -y ppa:nginx/stable')
    sudo('apt-get update && apt-get install -y nginx')

    # NTP
    sudo('apt-get install ntp -y')

    # NTP
    sudo('apt-get install ntp -y')

    # curl
    sudo('apt-get install curl -y')

def deploy(commit='master', force=False):
    """
    Deploy the app in the server
    """
    if not env.name:
        raise Exception(u'You MUST set the environment variable.')

    if env.forward_agent:
        # SSH exclude key checking for github.com
        if not exists('%s/.ssh' % env.user_home):
            run('mkdir %s/.ssh' % env.user_home)

        ssh_config = '%s/.ssh/config' % env.user_home
        if not contains(ssh_config, 'Host github.com'):
            run('echo "Host github.com" >>%s' % ssh_config)
            run('echo "     StrictHostKeyChecking no" >>%s' % ssh_config)
            run('echo "     UserKnownHostsFile /dev/null" >>%s' % ssh_config)

    # clone the repo into the env.project_path
    if not exists(env.project_path):
        run('git clone %s' % env.repository)

    with cd(env.project_path):
        # fetch the changes
        run('git fetch')

        # checkout to the selected commit/tag/branch
        run('git checkout %s' % commit)

        # create virtualenv if needed
        if not exists(env.venv_path):
            python = '/usr/bin/python'
            run('virtualenv --no-site-packages -p %(python)s %(path)s' % {'path': env.venv_path, 'python': python})

        with prefix('source %s/bin/activate' % env.venv_path):
            # install requirements
            run('pip install -r requirements.txt')

        packages_storage_link = '%s/data'% env.project_path
        if not exists(packages_storage_link):
            sudo('mkdir -p %s' %env.packages_storage_path)
            sudo('chown -R %s %s' %(env.user, env.packages_storage_path))
            run('ln -s %s %s' %(env.packages_storage_path, packages_storage_link))

        #run('pep381run %s' %packages_storage_path)
        setup_config_files()

def setup_config_files():

    # nginx
    sudo("cp %s/config/nginx/* /etc/nginx/conf.d/" %env.project_path)
    # supervisor 
    sudo("cp %s/config/supervisor/supervisord.conf /etc/supervisord.conf" %env.project_path)
    # cron
    #sudo("cp %s/config/cron.d/* /etc/cron.d/" %env.project_path)

def start():

    with settings(warn_only=True):
        sudo('pip install supervisor')

    sudo("supervisord")

    # pep381run
    sudo("supervisorctl start %s" %env.supervisor_program)

    # nginx
    sudo('service nginx restart', pty=False)

    # cron
    sudo('service cron restart', pty=False)

def stop():

    with settings(warn_only=True):
        # pep381run
        sudo("supervisorctl stop %s" %env.supervisor_program)

        # nginx
        sudo('service nginx stop', pty=False)

        # cron
        sudo('service cron stop', pty=False)
