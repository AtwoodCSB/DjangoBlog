from fabric.contrib.files import append, exists, sed
from fabric.api import env, run, local
import random

env.port = 26801
REPO_URL = 'https://github.com/AtwoodCSB/DjangoBlog.git'


def deploy():
    site_folder = '/home/%s/sites/%s' % (env.user, env.host)
    source_folder = site_folder + '/source'
    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)


def _create_directory_structure_if_necessary(site_folder):
    run('mkdir -p %s/%s' % (site_folder, 'env'))
    run('mkdir -p %s/%s' % (site_folder, 'source'))


def _get_latest_source(source_folder):
    if exists(source_folder + '/.git'):
        run('cd %s && git checkout blog-tutorial' % source_folder)
        run('cd %s && git fetch' % (source_folder,))
    else:
        run('git clone %s %s' % (REPO_URL, source_folder))
        run('cd %s && git checkout blog-tutorial' % source_folder)
    current_commit = local('git log -n 1 --format=%H', capture=True)
    run('cd %s && git reset --hard %s' % (source_folder, current_commit))
    for sub_folder in (
            'weblog/database', 'weblog/static', 'weblog/media'):
        run('mkdir -p %s/%s' % (source_folder, sub_folder))


def _update_virtualenv(source_folder):
    virtualenv_folder = source_folder + '/../env'
    if not exists(virtualenv_folder + '/bin/pip'):
        run('virtualenv --python=python3 %s' % (virtualenv_folder,))
    run('%s/bin/pip install -r %s/requirements.txt' %
        (virtualenv_folder, source_folder))


def _update_static_files(source_folder):
    run('cd %s && ../env/bin/python3 manage.py collectstatic --noinput' %
        (source_folder,))


def _update_database(source_folder):
    run('cd %s && ../env/bin/python3 manage.py makemigrations' %
        (source_folder,))
    run('cd %s && ../env/bin/python3 manage.py migrate --noinput' %
        (source_folder,))


def _update_settings(source_folder, site_name):
    setting_path = source_folder + '/weblog/config/settings.py'
    # sed(setting_path, "DEBUG = True", "DEBUG = False")
    sed(
        setting_path,
        'ALLOWED_HOSTS =.+$',
        'ALLOWED_HOSTS = ["%s"]' % site_name
    )
    secret_key_file = source_folder + '/weblog/config/secret_key.py'
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, "SECRET_KEY = '%s'" % key)
    append(setting_path, '\nfrom .secret_key import SECRET_KEY')
