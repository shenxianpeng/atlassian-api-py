# TODOS

Deferred work captured during gstack eng review, 2026-03-22.

---

## TODO 1 — Evaluate watcher/restriction methods for v1.0 Confluence scope

**What:** Decide whether `watch_page`, `get_page_watchers`, and `update_content_restrictions` belong in v1.0 or move to v1.1.

**Why:** These 3 methods were accepted in the CEO SELECTIVE EXPANSION review but immediately flagged as Reviewer Concerns. They serve a niche audience (watcher management, content restrictions) that may not align with the core DevOps/CI user who automates page creation and updates.

**Pros of including:** Completes the Confluence v1.0 surface; avoids API churn for users who do need them.
**Cons:** 3 more methods to test, document, and maintain. If the target audience doesn't use them, they're dead weight that dilutes the "quality per endpoint" positioning.

**Context:** No technical blocker — purely a product judgment call. The eng review confirmed no API availability issues (both are in Confluence Server/DC REST API). Decision should be made before Confluence implementation begins.

**Depends on:** Nothing. Can be resolved independently.

---

## TODO 2 — Version matrix: document which Jira/Confluence Server/DC versions are supported

**What:** Create a compatibility table in the README listing the minimum Jira Server/DC and Confluence Server/DC versions tested against each library version.

**Why:** The Agile API, attachment endpoints, content restrictions, and watcher APIs vary by product version. Without a matrix, users hitting version-specific 404s have no way to know if it's a bug or an unsupported version. "Quality per endpoint" needs to define what quality means on which versions.

**Pros:** Reduces support issues; builds trust with DevOps/CI users who care about version guarantees; differentiates on quality.
**Cons:** Requires reading Atlassian release notes to determine minimum versions, and ideally some integration testing.

**Context:** The Jira Software Agile REST API (`/rest/agile/1.0/`) requires a Jira Software license (not Jira Core). Confluence restrictions API availability varies by version. Currently the README mentions no version requirements at all. A starting point: Jira Agile API available since Jira Software 7.x; Confluence REST API since Confluence 5.5.

**Depends on:** v1.0 method list finalized (TODO 1 resolved first).

---

## TODO 3 — Jira Cloud support (v1.1): design correct Basic auth and URL routing

**What:** Implement `cloud=True` with correct auth — `Jira(url=..., cloud=True, email='user@example.com', token='api_token')` using Basic auth: `base64(email:token)`.

**Why:** Cloud was deferred from v1.0 because the existing `token=` parameter creates a Bearer auth header, which Jira Cloud rejects (Cloud API tokens use Basic auth with email as username). Without fixing this, any `cloud=True` implementation would silently fail to authenticate.

**Pros:** Unlocks the Jira Cloud user segment (2,800/month downloads, some must be cloud users); correct Cloud auth from day one differentiates from `atlassian-python-api` which has undocumented Cloud auth caveats.
**Cons:** Requires URL rewriting (all hardcoded `/rest/api/2/` paths must route to `/rest/api/3/` when cloud=True), new auth path in `client.py`, significant test work.

**Context:** Constructor change: add `cloud=False` + `cloud_email=None` params. When `cloud=True`, call `_create_basic_session(cloud_email, token)` instead of Bearer. URL routing: add `_api_version` property to `Jira` that returns `3` when `cloud=True`, `2` otherwise. Update all URL f-strings: `f"/rest/api/{self._api_version}/issue/{key}"`. All existing tests remain green since `cloud=False` is the default. v1.0 read-only constraint is still valid for v1.1 initial Cloud release.

**Depends on:** v1.0 shipped and stable. Do not implement Cloud before v1.0 is finalized.
