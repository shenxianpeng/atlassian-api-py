import nox
import glob
import sys

# Global Nox options
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_missing_interpreters = False


@nox.session
def lint(session):
    """Run linting using pre-commit."""
    session.install("pre-commit")
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
    session.install(".[test]")
    session.run("pytest")


@nox.session
def coverage(session):
    """Run test coverage analysis."""
    session.install(".")
    session.install(".[test]")
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "report", "-m")
    session.run("coverage", "xml")


@nox.session
def docs(session: nox.Session) -> None:
    """Build the documentation."""
    if sys.version_info.major == 3 and sys.version_info.minor == 13:
        session.skip("Skipping docs session on Python 3.13")
    session.install(".[docs]")
    session.run("sphinx-build", "-b", "html", "docs", "docs/build/html")
    session.run("sphinx-apidoc", "-o", "docs", "atlassian")


@nox.session(name="docs-live", default=False)
def docs_live(session: nox.Session) -> None:
    """Serve documentation with live reload."""
    if sys.version_info.major == 3 and sys.version_info.minor == 13:
        session.skip("Skipping docs session on Python 3.13")
    session.install(".[docs]")
    session.run("sphinx-apidoc", "-o", "docs", "atlassian")
    session.run(
        "sphinx-autobuild", "docs", "docs/build/html", "--watch", ".", external=True
    )
