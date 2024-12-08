import nox
import glob

nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_missing_interpreters = False


@nox.session
def lint(session):
    session.install("-r", "requirements-dev.txt")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def mypy(session):
    session.install("-r", "requirements-dev.txt")
    session.run("mypy", "atlassian")


@nox.session
def build(session):
    session.run("python3", "-m", "pip", "wheel", "-w", "dist", "--no-deps", ".")


@nox.session
def install(session):
    whl_file = glob.glob("dist/atlassian_api_py*.whl")
    session.install(*whl_file)


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"])
def test(session):
    session.install(".")
    session.install("-r", "requirements-dev.txt")
    session.run("pytest")


@nox.session()
def coverage(session):
    session.install(".")
    session.install("-r", "requirements-dev.txt")
    session.run("coverage", "run", "-m", "unittest")
    session.run("coverage", "report", "-m")
    session.run("coverage", "html")
