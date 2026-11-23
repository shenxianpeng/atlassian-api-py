"""Method names from other Atlassian libraries, and what replaces them here.

People and coding assistants who know ``atlassian-python-api`` or the ``jira``
package often call this library with those names. The clients use these
tables to say which method to call instead (see
``AtlassianAPI.__getattr__``).

The ``atlassian-python-api`` names are the ones in the mapping tables of
``docs/migration.rst``; a test keeps the two in step. Names that exist here
too are left out, because the attribute lookup succeeds for them.
"""

from __future__ import annotations

MIGRATION_GUIDE = "https://atlassian-api-py.readthedocs.io/en/latest/migration.html"

#: ``atlassian.Jira`` (atlassian-python-api) and ``jira.JIRA`` method names.
JIRA: dict[str, tuple[str, ...]] = {
    "get_issue": ("issue",),
    "issue_create": ("create_issue",),
    "update_issue_field": ("update_issue",),
    "issue_update": ("update_issue",),
    "edit_issue": ("update_issue",),
    "get_issue_transitions": ("get_transitions",),
    "set_issue_status": ("issue_transition",),
    "issue_add_comment": ("add_issue_comment",),
    "issue_edit_comment": ("update_issue_comment",),
    "issue_get_comments": ("get_issue_comments",),
    "jql": ("search_issue_with_jql",),
    "jql_get_list_of_tickets": (
        "search_issue_with_jql",
        "iter_issues",
    ),
    "enhanced_jql": (
        "search_issue_with_jql",
        "iter_issues",
    ),
    "enhanced_jql_get_list_of_tickets": (
        "search_issue_with_jql",
        "iter_issues",
    ),
    "approximate_issue_count": ("count_issues",),
    "add_attachment_object": ("add_attachment",),
    "get_attachment_content": ("download_attachment",),
    "remove_attachment": ("delete_attachment",),
    "issue_worklog": ("add_worklog",),
    "issue_get_worklog": ("get_worklogs",),
    "issue_add_watcher": ("add_issue_watcher",),
    "issue_get_watchers": ("get_issue_watchers",),
    "user_find_by_user_string": ("search_users",),
    "projects": ("get_projects",),
    "get_all_projects": ("get_projects",),
    "project": ("get_project",),
    "get_project_versions": ("get_versions",),
    "add_version": ("create_version",),
    "get_all_fields": ("get_fields",),
    "get_issue_changelog": ("issue_changelog",),
    "create_issue_link": ("link_issue_as",),
    "remove_issue_link": ("delete_issue_link",),
    "get_all_agile_boards": ("get_boards",),
    "get_agile_board": ("get_board",),
    "get_all_sprints_from_board": ("get_board_sprints",),
    "get_all_sprint": ("get_board_sprints",),
    "get_epics": ("get_board_epics",),
    "get_issues_for_board": ("iter_board_issues",),
    "get_issues_for_backlog": ("iter_backlog_issues",),
    "update_partially_sprint": ("update_sprint",),
    "rename_sprint": ("update_sprint",),
    "get_sprint_issues": ("iter_sprint_issues",),
    "get_issues_for_epic": ("iter_epic_issues",),
    "add_issues_to_sprint": ("move_issues_to_sprint",),
    "add_issues_to_backlog": ("move_issues_to_backlog",),
    "add_comment": ("add_issue_comment",),
    "add_issues_to_epic": ("move_issues_to_epic",),
    "add_watcher": ("add_issue_watcher",),
    "attachment": ("get_attachment",),
    "boards": ("get_boards",),
    "comments": ("get_issue_comments",),
    "enhanced_search_issues": (
        "search_issue_with_jql",
        "iter_issues",
    ),
    "fields": ("get_fields",),
    "move_to_backlog": ("move_issues_to_backlog",),
    "project_components": ("get_project_components",),
    "project_versions": ("get_versions",),
    "search_issues": (
        "search_issue_with_jql",
        "iter_issues",
    ),
    "sprint": ("get_sprint",),
    "sprints": ("get_board_sprints",),
    "transition_issue": ("issue_transition",),
    "transitions": ("get_transitions",),
    "watchers": ("get_issue_watchers",),
    "worklogs": ("get_worklogs",),
}

#: Names in :data:`JIRA` that come from the ``jira`` package only.
JIRA_PACKAGE_ONLY = frozenset(
    {
        "add_comment",
        "add_issues_to_epic",
        "add_watcher",
        "attachment",
        "boards",
        "comments",
        "enhanced_search_issues",
        "fields",
        "move_to_backlog",
        "project_components",
        "project_versions",
        "search_issues",
        "sprint",
        "sprints",
        "transition_issue",
        "transitions",
        "watchers",
        "worklogs",
    }
)

#: ``atlassian.Confluence`` (atlassian-python-api) method names.
CONFLUENCE: dict[str, tuple[str, ...]] = {
    "get_page_by_id": ("get_content_by_id",),
    "get_page_id": ("get_page_by_title",),
    "create_page": ("create_content",),
    "update_page": ("update_content",),
    "update_or_create": ("create_or_update_page",),
    "remove_page": ("delete_content",),
    "remove_content": ("delete_content",),
    "get_page_child_by_type": ("get_child_pages",),
    "get_page_labels": ("get_labels",),
    "set_page_label": ("add_label",),
    "remove_page_label": ("remove_label",),
    "attach_file": ("upload_attachment",),
    "attach_content": ("upload_attachment",),
    "get_attachments_from_content": ("get_attachments",),
    "download_attachments_from_page": ("download_attachment",),
    "cql": ("search_content",),
    "iter_cql": ("iter_search",),
    "cql_all": ("iter_search",),
    "get_all_spaces": ("get_spaces",),
    "get_all_pages_from_space_raw": ("get_content_by_space",),
    "get_page_comments": ("get_comments",),
    "history": ("get_content_history",),
    "get_page_as_pdf": ("export_page_pdf",),
    "export_page": ("export_page_pdf",),
}

#: ``atlassian.Bitbucket`` (atlassian-python-api) method names.
BITBUCKET: dict[str, tuple[str, ...]] = {
    "repo_list": ("get_project_repo",),
    "get_repo": ("get_repo_info",),
    "get_branches": ("get_repo_branch",),
    "get_pull_requests": ("get_pull_request",),
    "open_pull_request": ("create_pull_request",),
    "get_pull_requests_activities": ("get_pull_request_activities",),
    "get_pull_requests_commits": ("get_pull_request_commits",),
    "change_reviewed_status": ("review_pull_request",),
    "update_pull_request": (
        "update_pull_request_title",
        "update_pull_request_description",
        "update_pull_request_reviewers",
        "update_pull_request_destination",
    ),
    "get_commits": (
        "get_branch_commits",
        "get_file_change_history",
    ),
    "get_changelog": ("compare_commits",),
    "get_content_of_file": ("get_file_content",),
    "get_file_list": ("list_files",),
    "set_tag": ("create_tag",),
    "repo_users": ("get_repo_permissions",),
    "repo_groups": ("get_repo_permissions",),
    "repo_grant_user_permissions": ("set_repo_permission",),
    "repo_grant_group_permissions": ("set_repo_permission",),
    "repo_remove_user_permissions": ("revoke_repo_permission",),
    "repo_remove_group_permissions": ("revoke_repo_permission",),
    "get_associated_build_statuses": ("get_build_status",),
}

_BY_CLIENT = {"Jira": JIRA, "Confluence": CONFLUENCE, "Bitbucket": BITBUCKET}


def replacements(client: type, name: str) -> tuple[str, ...]:
    """Return the methods of ``client`` that replace ``name``, if it is known.

    :param client: A client class, or a subclass of one.
    :type client: type
    :param name: A method name used by another library.
    :type name: str
    :return: Method names of this library, or an empty tuple.
    :rtype: tuple[str, ...]
    """
    for cls in client.__mro__:
        found = _BY_CLIENT.get(cls.__name__, {}).get(name)
        if found:
            return found
    return ()


def missing_attribute_message(client: type, name: str) -> str:
    """Return the ``AttributeError`` text for ``name`` on a ``client`` object.

    :param client: The client's class.
    :type client: type
    :param name: The attribute that was not found.
    :type name: str
    :return: Python's usual message, followed by the method to call instead
        when ``name`` is known from another library.
    :rtype: str
    """
    message = f"{client.__name__!r} object has no attribute {name!r}"
    found = replacements(client, name)
    if not found:
        return message
    calls = " or ".join(f"{method}()" for method in found)
    return (
        f"{message}. {name}() is a method of another Atlassian library; "
        f"in atlassian-api-py call {calls} instead. "
        f"Method mapping: {MIGRATION_GUIDE}"
    )
