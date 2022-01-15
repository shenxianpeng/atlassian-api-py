import os
import subprocess
import time
import shutil
from packaging import version


def check_command_exist(name, cmd):
    try:
        print("%s" % cmd)
        subprocess.check_output(cmd, shell=False, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"Could not run command {name} - please make sure it is installed"
        )


def get_current_branch():
    return os.popen("git rev-parse --abbrev-ref HEAD  2>&1").read().strip()


def get_current_version():
    version = {}
    with open(version_file) as fp:
        exec(fp.read(), version)

    return version["__version__"]


def bump_version(old_version, new_version):

    if version.parse(old_version) < version.parse(new_version):
        f = open("atlassian/_version.py", "r")
        file_data = f.read()
        f.close()

        new_data = file_data.replace(old_version, new_version)

        f = open("atlassian/_version.py", "w")
        f.write(new_data)
        f.close()
    else:
        print(
            f"The Bump version number {old_version} is less than the current version number {new_version}"
        )
        exit(1)


def git_push(new_version):
    os.system(f"git add {version_file}")
    os.system(f'git commit -m "chore: bump version to {new_version}"')
    os.system("git push -u origin master")


def build_package():
    is_build = input("ready to build? (y/N)")
    if is_build in ("y", "Y"):
        try:
            print("starting remove dist build folders\n")
            if os.path.exists("dist"):
                shutil.rmtree("dist")
            if os.path.exists("build"):
                shutil.rmtree("build")
        except OSError as e:
            print("[x]: remote %s - %s failed." % (e.filename, e.strerror))
            exit(1)

        print("build wheel file for release\n")
        os.system("python setup.py bdist_wheel")  # add sdist if need


def check_wheel_file(curr_version):
    whl_name = f"atlassian_api_py-{curr_version}-py3-none-any.whl"
    if whl_name in os.listdir("dist"):
        return whl_name
    else:
        return False


def upload_to_pypi():
    print("start to upload wheel file to PyPI.")
    os.system("twine upload dist/*")


def check_release_branch():
    branch = get_current_branch()
    if branch == "master":
        print("\n###################################")
        print("# ready to release...             #")
        print("###################################\n")
    else:
        print(f"could not release on {branch} branch.")
        exit(1)


def check_bump_version():
    old_v = get_current_version()
    print("old version is: %s \n" % old_v)

    new_v = input("bump version to? (input n/N to skip): ")
    if new_v in ("n", "N"):
        print("\n[x] skip bump version\n")
    else:
        bump_version(old_v, new_v)

    curr_version = get_current_version()
    print(f"current version is: {curr_version}\n")


def check_git_push(curr_version):
    is_push = input("commit and push _version.py to remote?(y/N) ")
    if is_push in ("y", "Y"):
        git_push(curr_version)
    else:
        print("\n[x] skip commit and push.\n")


def check_git_tag(curr_version):
    is_tag = input("ready to create tag?(Y/N): ")
    if is_tag in ("y", "Y"):
        os.system(f"git tag -d v{curr_version}")
        os.system(
            f'git tag -a v{curr_version} -m "Tag release version {curr_version}"'
        )
        os.system("git push --tags origin")
    else:
        print("[x] skip create tag\n")


def check_twine_upload(wheel_file):
    if wheel_file:
        is_upload = input(f"\nready to upload {wheel_file} to PyPI?(y/N) ")
        if is_upload in ("y", "Y"):
            upload_to_pypi()
        else:
            print(f"[X] skip upload {wheel_file} to PyPI\n")


if __name__ == "__main__":
    env = os.environ
    LOG = env.get("AAP_RELEASE_LOG", "logs/atlassian-api-py-release.log")
    version_file = "atlassian/_version.py"

    check_release_branch()

    check_bump_version()

    cv = get_current_version()

    check_git_push(cv)

    check_git_tag(cv)

    build_package()

    wheel_name = check_wheel_file(cv)

    check_twine_upload(wheel_name)
