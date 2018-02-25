# -*- coding: utf-8 -*-
import os
import errno
import sys
import webbrowser
import json
from invoke import task, run
import boto3
import contextlib
import shutil
# from botocore.errorfactory import ExecutionAlreadyExists
from contextlib import contextmanager
import aws_lambda

docs_dir = 'docs'
build_dir = os.path.join(docs_dir, '_build')
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


@contextmanager
def setenv(**kwargs):
    # Backup
    prev = {}
    for k, v in kwargs.items():
        if k in os.environ:
            prev[k] = os.environ[k]
        os.environ[k] = v

    yield

    # Restore
    for k in kwargs.keys():
        if k in prev:
            os.environ[k] = prev[k]
        else:
            del os.environ[k]


def get_all_core_lambdas():
    return [
            'AlexaSmartHomeAPI_Chameleon',
            ]


@contextlib.contextmanager
def chdir(dirname=None):
    curdir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
            yield
    finally:
        os.chdir(curdir)


def upload(keyname, data, s3bucket, secret=None):

    if secret is None:
        secret = os.environ.get("SECRET")
        if secret is None:
            raise RuntimeError("SECRET should be defined in env")

    s3 = boto3.client('s3')
    s3.put_object(Bucket=s3bucket,
                  Key=keyname,
                  Body=data,
                  SSECustomerKey=secret,
                  SSECustomerAlgorithm='AES256')


@task
def loc(ctx):
    """
    Count lines-of-code.
    """
    excludes = ['/tests/', '/Data_files', 'Submit4DN.egg-info', 'docs', 'htmlcov',
                'README.md', 'README.rst', '.eggs']

    run('find . -iname "*py" | grep -v {} | xargs wc -l | sort -n'.format(
        ' '.join('-e ' + e for e in excludes)))


def copytree(src, dst, symlinks=False, ignore=None):
    skipfiles = ['.coverage', 'dist', 'htmlcov', '__init__.pyc', 'coverage.xml', 'service.pyc']
    for item in os.listdir(src):
        src_file = os.path.join(src, item)
        dst_file = os.path.join(dst, item)
        if src_file.split('/')[-1] in skipfiles:
            print("skipping file %s" % src_file)
            continue
        if os.path.isdir(src_file):
            mkdir(dst_file)
            shutil.copytree(src_file, dst_file, symlinks, ignore)
        else:
            shutil.copy2(src_file, dst_file)


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


@task
def new_lambda(ctx, name, base='create_beanstalk'):
    '''
    create a new lambda by copy from a base one and replacing some core strings.
    '''
    src_dir = './%s' % base
    dest_dir = './%s' % name
    mkdir(dest_dir)
    copytree(src=src_dir, dst=dest_dir)
    chdir(dest_dir)
    # TODO: awk some lines here...


@task(aliases=['tests'])
def test(ctx, watch=False, last_failing=False, no_flake=False, k='',  extra=''):
    """Run the tests.
    Note: --watch requires pytest-xdist to be installed.
    """
    from os import path

    import pytest
    if not no_flake:
        flake(ctx)
    args = ['-rxs', ]
    if k:
        args.append('-k %s' % k)
    args.append(extra)
    if watch:
        args.append('-f')
    if last_failing:
        args.append('--lf')
    retcode = pytest.main(args)
    try:
        home = path.expanduser("~")
        if retcode == 0:
            sndfile = os.path.join(home, "code", "snd", "zenyatta", "You_Have_Done_Well.ogg")
        else:
            sndfile = os.path.join(home, "code", "snd", "zenyatta", "Darkness\ Falls.ogg")
        print(sndfile)
        run("vlc -I rc %s --play-and-exit -q" % (sndfile))
    except:
        pass
    return(retcode)


@task
def flake(ctx):
    """Run flake8 on codebase."""
    run('flake8 .', echo=True)
    print("flake8 passed!!!")


@task
def clean(ctx):
    run("rm -rf build")
    run("rm -rf dist")
    print("Cleaned up.")


@task
def deploy(ctx, name, version=None, no_tests=False):
    print("preparing for deploy...")
    print("make sure tests pass")
    if no_tests is False:
        if test(ctx) != 0:
            print("tests need to pass first before deploy")
            return
    if name == 'all':
        names = get_all_core_lambdas()
        print(names)
    else:
        names = [name, ]

    # dist directores are the enemy, clean the all
    for name in get_all_core_lambdas():
        print("cleaning house before deploying")
        with chdir("./%s" % (name)):
            clean(ctx)

    for name in names:
        print("=" * 20, "Deploying lambda", name, "=" * 20)
        with chdir("./%s" % (name)):
            print("clean up previous builds.")
            clean(ctx)
            print("building lambda package")
            deploy_lambda_package(ctx, name)
            # need to clean up all dist, otherwise, installing local package takes forever
            clean(ctx)
        print("next get version information")
        # version = update_version(ctx, version)
        print("then tag the release in git")
        # git_tag(ctx, version, "new production release %s" % (version))
        # print("Build is now triggered for production deployment of %s "
        #      "check travis for build status" % (version))


@task
def deploy_lambda_package(ctx, name):
    # third part tools, should all be tar
    '''
    tools_dir = os.path.join(ROOT_DIR, "third_party")
    bin_dir = os.path.join(ROOT_DIR, "bin")

    for filename in os.listdir(tools_dir):
        if filename.endswith('.tar'):
            fullpath = os.path.join(tools_dir, filename)
            run("tar -xvf %s -C %s" % (fullpath, bin_dir))
    '''

    aws_lambda.deploy(os.getcwd(), requirements='./requirements.txt')


@task
def git_tag(ctx, tag_name, msg):
    run('git tag -a %s -m "%s"' % (tag_name, msg))
    run('git push --tags')
    run('git push')


@task
def clean_docs(ctx):
    run("rm -rf %s" % build_dir, echo=True)


@task
def browse_docs(ctx):
    path = os.path.join(build_dir, 'index.html')
    webbrowser.open_new_tab(path)


@task
def docs(ctx, clean=False, browse=False, watch=False):
    """Build the docs."""
    if clean:
        clean_docs(ctx)
    run("sphinx-build %s %s" % (docs_dir, build_dir), echo=True)
    if browse:
        browse_docs(ctx)
    if watch:
        watch_docs(ctx)


@task
def watch_docs(ctx):
    """Run build the docs when a file changes."""
    try:
        import sphinx_autobuild  # noqa
    except ImportError:
        print('ERROR: watch task requires the sphinx_autobuild package.')
        print('Install it with:')
        print('    pip install sphinx-autobuild')
        sys.exit(1)
    run('sphinx-autobuild {0} {1} --watch {2}'.format(
        docs_dir, build_dir, '4DNWranglerTools'), echo=True, pty=True)


@task
def readme(ctx, browse=False):
    run('rst2html.py README.rst > README.html')
    if browse:
        webbrowser.open_new_tab('README.html')


@task
def publish(ctx, test=False):
    """Publish to the cheeseshop."""
    clean(ctx)
    if test:
        run('python setup.py register -r test sdist bdist_wheel', echo=True)
        run('twine upload dist/* -r test', echo=True)
    else:
        run('python setup.py register sdist bdist_wheel', echo=True)
        run('twine upload dist/*', echo=True)
