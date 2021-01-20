import os
import subprocess
import datetime
from packaging import version


def check_command_exist(name, cmd):
    try:
        print("%s" % cmd)
        subprocess.check_output(cmd, shell=False, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        raise RuntimeError('Could not run command %s - please make sure it is installed' % name)


def get_current_branch():
    return os.popen('git rev-parse --abbrev-ref HEAD  2>&1').read().strip()


def get_current_version():
    version = {}
    with open("atlassian/_version.py") as fp:
        exec(fp.read(), version)

    return version['__version__']


def bump_version_to(old_version, new_version):

    if version.parse(old_version) < version.parse(new_version):
        f = open('atlassian/_version.py', 'r')
        file_data = f.read()
        f.close()

        new_data = file_data.replace(old_version, new_version)

        f = open('atlassian/_version.py', 'w')
        f.write(new_data)
        f.close()
    else:
        print("The Bump version number {} is less than the current version number {}".format(old_version, new_version))
        exit(1)


def tag_release(new_version):
    os.system('git tag -a v%s -m "Tag release version %s"' % (new_version, new_version))


def build_package():
    print("remove dist build folder if they exists.")
    os.system('rm -rf dist build > /dev/null 2>&1')
    print("build wheel file for release")
    os.system(' python setup.py bdist_wheel')   # add sdist if need


def upload_to_pypi():
    print("start to upload wheel file to PyPI.")
    # os.system('twine upload dist/*')


if __name__ == "__main__":
    env = os.environ
    LOG = env.get('AAP_RELEASE_LOG', 'logs/atlassian-api-py-release.log')

    branch = get_current_branch()
    if branch == 'master':
        print("ready to release")
    else:
        print("could not release on %s branch." % branch)

    old_v = get_current_version()
    print("old version is: " + old_v)

    new_v = input("bump version to (input N to skip): ")
    if new_v in ("n", "N"):
        print("skip bump version")
    else:
        bump_version_to(old_v, new_v)

        curr_v = get_current_version()
        print('new version is: ' + curr_v)

    is_tag = input("ready to create tag?(Y/N): ")
    if is_tag in ('y', 'Y'):
        tag_release(curr_v)
    else:
        print("skip create tag")

    build_package()


