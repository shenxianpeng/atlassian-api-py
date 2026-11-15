"""Hints for method names that belong to other Atlassian libraries."""

import copy
import inspect
import re
from pathlib import Path

import pytest

from atlassian_api import Bitbucket, Confluence, Jira, _hints

MIGRATION_PAGE = Path(__file__).resolve().parents[1] / "docs" / "migration.rst"
CLIENTS = {"Jira": Jira, "Confluence": Confluence, "Bitbucket": Bitbucket}
TABLES = {
    "Jira": ("jira-methods", _hints.JIRA),
    "Confluence": ("confluence-methods", _hints.CONFLUENCE),
    "Bitbucket": ("bitbucket-methods", _hints.BITBUCKET),
}
ALL_HINTS = [
    (client, name, targets)
    for client, (_, table) in TABLES.items()
    for name, targets in table.items()
]


def documented_mapping(table_name):
    """Return ``{their name: [our names]}`` from a table in the migration page."""
    text = MIGRATION_PAGE.read_text()
    block = text[text.index(f":name: {table_name}") :]
    next_heading = re.search(r"\n\S[^\n]*\n[~=-]{4,}\n", block)
    rows = re.split(r"\n   \* - ", block[: next_heading.start()])[2:]
    mapping = {}
    for row in rows:
        left, right = re.split(r"\n     - ?", row)[:2]
        for name in re.findall(r"``(\w+)\(\)``", left):
            targets = mapping.setdefault(name, [])
            targets += [
                t for t in re.findall(r"``(\w+)\(\)``", right) if t not in targets
            ]
    return mapping


def client(name):
    return CLIENTS[name](url="https://server.company.com", token="t")


class TestTables:
    @pytest.mark.parametrize("client_name, name, targets", ALL_HINTS)
    def test_replacement_exists_and_old_name_does_not(self, client_name, name, targets):
        cls = CLIENTS[client_name]
        assert targets, name
        for target in targets:
            assert inspect.isfunction(getattr(cls, target)), target
        # A name that exists here never reaches the hint.
        assert name not in dir(cls)

    @pytest.mark.parametrize("client_name", TABLES)
    def test_tables_match_the_migration_page(self, client_name):
        table_name, hints = TABLES[client_name]
        cls = CLIENTS[client_name]
        documented = {
            name: tuple(targets)
            for name, targets in documented_mapping(table_name).items()
            if name not in dir(cls)
        }
        assert len(documented) > 15  # the page was parsed, not skipped
        other_sources = _hints.JIRA_PACKAGE_ONLY if client_name == "Jira" else set()
        from_page = {n: t for n, t in hints.items() if n not in other_sources}
        assert from_page == documented

    def test_jira_package_names_are_all_in_the_jira_table(self):
        assert _hints.JIRA_PACKAGE_ONLY <= set(_hints.JIRA)
        assert len(_hints.JIRA_PACKAGE_ONLY) > 10


class TestOtherLibraries:
    """The old names are real. Skipped unless the other library is installed."""

    def test_atlassian_python_api_names(self):
        atlassian = pytest.importorskip("atlassian")
        theirs = {
            "Jira": atlassian.Jira,
            "Confluence": atlassian.ConfluenceServer,
            "Bitbucket": atlassian.Bitbucket,
        }
        missing = [
            f"{client_name}.{name}"
            for client_name, name, _ in ALL_HINTS
            if name not in _hints.JIRA_PACKAGE_ONLY
            and not hasattr(theirs[client_name], name)
        ]
        assert missing == []

    def test_jira_package_names(self):
        jira = pytest.importorskip("jira")
        missing = [n for n in _hints.JIRA_PACKAGE_ONLY if not hasattr(jira.JIRA, n)]
        assert missing == []


class TestMissingAttribute:
    def test_known_name_says_what_to_call(self):
        with pytest.raises(AttributeError) as exc:
            client("Jira").jql("project = TEST")
        message = str(exc.value)
        assert message.startswith("'Jira' object has no attribute 'jql'. ")
        assert "call search_issue_with_jql() instead" in message
        assert message.endswith(f"Method mapping: {_hints.MIGRATION_GUIDE}")

    def test_several_replacements_are_all_named(self):
        with pytest.raises(AttributeError, match=r"call search_issue_with_jql\(\) or "):
            client("Jira").search_issues("project = TEST")

    @pytest.mark.parametrize(
        "client_name, name, replacement",
        [
            ("Confluence", "get_page_by_id", "get_content_by_id()"),
            ("Bitbucket", "repo_list", "get_project_repo()"),
        ],
    )
    def test_each_client_uses_its_own_table(self, client_name, name, replacement):
        with pytest.raises(AttributeError, match=re.escape(replacement)):
            getattr(client(client_name), name)

    def test_name_from_another_client_gets_no_hint(self):
        with pytest.raises(AttributeError) as exc:
            client("Confluence").jql
        assert str(exc.value) == "'Confluence' object has no attribute 'jql'"

    def test_unknown_name_keeps_the_plain_message(self):
        with pytest.raises(AttributeError) as exc:
            client("Jira").nonsense
        assert str(exc.value) == "'Jira' object has no attribute 'nonsense'"

    def test_error_carries_name_and_object_for_did_you_mean(self):
        jira = client("Jira")
        with pytest.raises(AttributeError) as exc:
            jira.isue
        assert (exc.value.name, exc.value.obj) == ("isue", jira)

    def test_subclass_gets_hints_under_its_own_name(self):
        class TeamJira(Jira):
            pass

        with pytest.raises(AttributeError) as exc:
            TeamJira(url="https://jira.company.com", token="t").get_issue("T-1")
        assert str(exc.value).startswith("'TeamJira' object has no attribute")
        assert "call issue() instead" in str(exc.value)

    def test_hasattr_getattr_default_and_copy_still_work(self):
        jira = client("Jira")
        assert not hasattr(jira, "jql")
        assert getattr(jira, "jql", None) is None
        assert copy.copy(jira).url == jira.url

    def test_existing_methods_are_untouched(self):
        assert client("Jira").issue.__name__ == "issue"
