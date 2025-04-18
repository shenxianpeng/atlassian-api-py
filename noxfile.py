import nox
import glob

# Global Nox options
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_missing_interpreters = False


@nox.session
def lint(session):
    """Run linting using pre-commit."""
    session.install("-r", "requirements-dev.txt")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def build(session):
    """Build the project wheel."""
    session.run("python3", "-m", "pip", "wheel", "-w", "dist", "--no-deps", ".")


@nox.session
def install(session):
    """Install the built wheel."""
    whl_files = glob.glob("dist/atlassian_api_py*.whl")
    if not whl_files:
        session.error("No wheel files found in 'dist'. Run the 'build' session first.")
    session.install(*whl_files)


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
def test(session):
    """Run tests across multiple Python versions."""
    session.install(".")
    session.install("-r", "requirements-dev.txt")
    session.run("pytest")


@nox.session(python=["3.10"])
def coverage(session):
    """Run test coverage analysis."""
    session.install(".")
    session.install("-r", "requirements-dev.txt")
    session.run("coverage", "run", "-m", "unittest")
    session.run("coverage", "report", "-m")
    session.run("coverage", "html")


@nox.session(python=["3.9", "3.10", "3.11", "3.12"]) # 3.13 removed imghdr module
def docs(session: nox.Session) -> None:
    """Build the documentation."""
    session.install("--upgrade", "pip")
    session.install(".")
    session.install("-r", "docs/requirements.txt")
    session.run("sphinx-build", "-b", "html", "docs", "docs/build/html")
    session.run("sphinx-apidoc", "-f", "-o", "docs", "atlassian")


@nox.session(name="docs-live", default=False)
def docs_live(session: nox.Session) -> None:
    """Serve documentation with live reload."""
    session.install("-r", "docs/requirements.txt", "sphinx-autobuild")
    session.run("sphinx-apidoc", "-f", "-o", "docs", "atlassian")
    session.run("sphinx-autobuild", "docs", "docs/build/html", external=True)
