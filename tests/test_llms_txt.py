"""The llms.txt and llms-full.txt files generated for AI assistants.

They are written by the Sphinx extension in ``docs/_ext/llms_txt.py``. An
assistant copies what it reads there, so these tests check that the files
describe the code as it is.
"""

import ast
import importlib.util
import inspect
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from atlassian_api import Bitbucket, Confluence, Jira, _hints

EXTENSION = Path(__file__).resolve().parents[1] / "docs" / "_ext" / "llms_txt.py"
CLIENTS = {"jira": Jira, "confluence": Confluence, "bitbucket": Bitbucket}


@pytest.fixture(scope="module")
def ext():
    spec = importlib.util.spec_from_file_location("llms_txt", EXTENSION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def full(ext):
    return ext.llms_full_txt()


def public_methods(cls):
    return [
        name
        for name, member in vars(cls).items()
        if inspect.isfunction(member) and not name.startswith("_")
    ]


class TestIndex:
    def test_follows_the_llms_txt_layout(self, ext):
        lines = ext.llms_txt().splitlines()
        assert lines[0] == "# atlassian-api-py"
        assert lines[2].startswith("> ")
        assert "## Docs" in lines and "## Optional" in lines

    def test_links_are_absolute(self, ext):
        links = re.findall(r"\]\(([^)]+)\)", ext.llms_txt())
        assert len(links) >= 5
        assert all(link.startswith("https://") for link in links)

    def test_states_the_import_name_and_method_counts(self, ext):
        text = ext.llms_txt()
        assert "from atlassian_api import Jira, Confluence, Bitbucket" in text
        for cls in CLIENTS.values():
            assert f"{cls.__name__} {len(public_methods(cls))}" in text


class TestFullReference:
    @pytest.mark.parametrize("cls", CLIENTS.values(), ids=lambda cls: cls.__name__)
    def test_every_public_method_has_an_entry(self, full, cls):
        methods = public_methods(cls)
        assert len(methods) > 20
        missing = [m for m in methods if f"#### `{cls.__name__}.{m}(" not in full]
        assert missing == []

    def test_signatures_are_readable(self, full):
        entry = "#### `Jira.iter_issues(jql: str, fields: list[str] | None = None, page_size: int = 100)"
        assert entry in full
        assert "(self" not in full

    def test_docstring_fields_become_a_list(self, full):
        start = full.index("#### `Jira.count_issues(")
        entry = full[start : full.index("#### ", start + 5)]
        assert "- `jql`: " in entry and "- Returns: " in entry

    def test_no_restructuredtext_is_left(self, full):
        prose = full.replace("```", "")
        for leftover in (":param", ":type", ":rtype", ":return", ":meth:", "``"):
            assert leftover not in prose, leftover
        assert not re.search(r"^\s*\.\. \w", prose, re.M)  # directives

    def test_code_blocks_are_fenced_and_closed(self, full):
        assert full.count("```") % 2 == 0
        assert "```python\nsprint = jira.create_sprint(" in full

    def test_lists_every_hint(self, full):
        for table in (_hints.JIRA, _hints.CONFLUENCE, _hints.BITBUCKET):
            for name, targets in table.items():
                assert f"| `{name}()` | `{targets[0]}()`" in full

    def test_lists_the_error_classes(self, full):
        for name in ("APIError", "NotFoundError", "RateLimitError", "ServerError"):
            assert f"- `{name}`: " in full

    def test_examples_call_methods_that_exist_with_arguments_that_bind(self, ext):
        code = "\n".join(re.findall(r"```python\n(.*?)```", ext.EXAMPLES, re.S))
        calls = [
            node
            for node in ast.walk(ast.parse(code))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in CLIENTS
        ]
        assert len(calls) >= 12
        for call in calls:
            method = getattr(CLIENTS[call.func.value.id], call.func.attr)
            inspect.signature(method).bind(
                None, *call.args, **{kw.arg: None for kw in call.keywords}
            )


class TestSphinxHook:
    def test_writes_both_files_after_an_html_build(self, ext, tmp_path):
        app = SimpleNamespace(builder=SimpleNamespace(format="html"), outdir=tmp_path)
        ext.write_files(app, None)
        assert (tmp_path / "llms.txt").read_text() == ext.llms_txt()
        assert (tmp_path / "llms-full.txt").read_text() == ext.llms_full_txt()

    @pytest.mark.parametrize(
        "builder_format, exception", [("latex", None), ("html", RuntimeError("x"))]
    )
    def test_writes_nothing_for_other_builders_or_failed_builds(
        self, ext, tmp_path, builder_format, exception
    ):
        app = SimpleNamespace(
            builder=SimpleNamespace(format=builder_format), outdir=tmp_path
        )
        ext.write_files(app, exception)
        assert list(tmp_path.iterdir()) == []

    def test_setup_connects_the_hook(self, ext):
        connected = {}
        app = SimpleNamespace(connect=lambda event, func: connected.update({event: func}))
        assert ext.setup(app)["parallel_read_safe"] is True
        assert connected == {"build-finished": ext.write_files}
