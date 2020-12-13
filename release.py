import os
import re
import subprocess
import datetime

env = os.environ

# console colors
OKGREEN = '\033[92m'
ENDC = '\033[0m'
FAIL = '\033[91m'

LOG = env.get('AAP_RELEASE_LOG', 'atlassian-api-py-release.log')
SETUP_FILE = 'setup.py'


def log(msg):
    log_plain('\n%s' % msg)


def log_plain(msg):
    f = open(LOG, mode='ab')
    f.write(msg.encode('utf-8'))
    f.close()


def check_command_exists(name, cmd):
    try:
        print('%s' % cmd)
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        raise RuntimeError('Could not run command %s - please make sure it is installed' % name)


def run_and_print(text, run_function):
    try:
        print(text, end='')
        run_function()
        print(OKGREEN + 'OK' + ENDC)
    except RuntimeError:
        print(FAIL + 'NOT OK' + ENDC)


def check_environment_and_commandline_tools():
    check_command_exists('python', 'python --version')


def git_checkout(branch):
    run('git checkout %s' % branch)


def get_current_branch():
    return os.popen('git rev-parse --abbrev-ref HEAD  2>&1').read().strip()


def get_head_hash():
    return os.popen('git rev-parse --verify HEAD 2>&1').read().strip()


def find_release_version(src_branch):
    with open(SETUP_FILE, encoding='utf-8') as file:
        for line in file.readlines():
            match = re.search(r'\d.\d.\d', line)
            if match:
                return match.group(0)
        raise RuntimeError('Could not find release version in %s branch' % src_branch)


def run(command, quiet=False):
    log('%s: RUN: %s\n' % (datetime.datetime.now(), command))
    if os.system('%s >> %s 2>&1' % (command, LOG)):
        msg = '    FAILED: %s [see log %s]' % (command, LOG)
        if not quiet:
            print(msg)
        raise RuntimeError(msg)


def run_coverage_unit_test():
    run('coverage run -m unittest discover')


def commit_master(release):
    run('git commit -m "update for release %s"' % release)


def tag_release(release):
    run('git tag -a v%s -m "Tag release version %s"' % (release, release))


def check_exec_result():
    pass


def bump_version_to(current_version=None, release_type=None):
    # major.minor.micro
    match = re.match(r'(\d).(\d).(\d)', current_version)
    major = match.group(1)
    minor = match.group(2)
    micro = match.group(3)

    if release_type == 'major':
        major += 1
    elif release_type == 'minor':
        minor += 1
    elif release_type == 'micro':
        micro += 1
    else:
        raise('Release type %s not support' % release_type)

    new_version = '{0}.{1}.{2}'.format(major, minor, micro)
    return new_version


def update_version(new_version):
    with open(SETUP_FILE, encoding='utf-8') as file:
        for line in file.readlines():
            match = re.search(r'\d.\d.\d', line)
            if match:
                line.replace(match.group(0), new_version)
                print('Update release version to %s' % new_version)
        raise RuntimeError('Update release version to %s failed' % new_version)


def git_push():
    pass


def upload_to_pypi(prod_env=None, test_env=None):
    if prod_env:
        pass
    if test_env:
        pass


if __name__ == '__main__':

        src_branch = get_current_branch()

        run_coverage_unit_test()

        check_environment_and_commandline_tools()

        if src_branch != 'master':
            raise RuntimeError('Need release from master branch.')

        # input('Press Enter to continue...')

        current_version = find_release_version('master')

        print('Current release version: [%s]' % current_version)

        success = False

        try:
            git_checkout('master')
            master_hash = get_head_hash()
            input('Input what type of this release')
            
            new_version = bump_version_to(current_version, release_type='micro')
            update_version()
            # input('Press Enter to continue...')
            print('  tag')
            tag_release(current_version)
            git_push(src_branch, current_version)
            success = True
        except Exception as e:
            print(e)
        finally:
            if not success:
                print('Logs:')
                with open(LOG, 'r') as log_file:
                    print(log_file.read())
                git_checkout('master')
                run('git reset --hard %s' % master_hash)
                try:
                    run('git tag -d v%s' % current_version)
                except RuntimeError:
                    pass