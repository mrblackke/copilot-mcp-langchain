import mcp.types as types
import os
import json
import base64
import requests
from collections import defaultdict

ROLES = ["frontend", "backend", "qa", "ba", "other"]

# ---------------------------------------------------------------------------
# Role detection — matches summary keywords to FE / BE / QA / BA / other
# Extend ROLE_KEYWORDS to match your team's naming conventions.
# ---------------------------------------------------------------------------
ROLE_KEYWORDS = {
    "frontend": ["fe:", "fe ", "[fe]", "(fe)", "frontend", "front-end", "ui:", "ui ", "[ui]", "(ui)", "react", "vue", "angular", "css", "html"],
    "backend":  ["be:", "be ", "[be]", "(be)", "backend", "back-end", "api:", "api ", "[api]", "(api)", "server:", "service:", "db:", "database"],
    "qa":       ["qa:", "qa ", "[qa]", "(qa)", "qc:", "qc ", "[qc]", "(qc)", "test:", "testing", "autotests", "e2e:", "manual:"],
    "ba":       ["ba:", "ba ", "[ba]", "(ba)", "analyst", "analysis", "requirement", "requirements", "business analysis", "grooming", "backlog", "acceptance criteria"],
}

# ---------------------------------------------------------------------------
# Person-to-role overrides — people always assigned to a role regardless of
# issue tags. Useful for BAs, PMs, DevOps who work across all issue types.
# Keys are substrings of displayName (case-insensitive).
# ---------------------------------------------------------------------------
PERSON_ROLE_OVERRIDES: dict[str, str] = {
    "darya strogonova": "ba",
    "elvina": "ba",
}


def _detect_role(summary: str, author_name: str = "") -> str:
    # Person override takes priority
    if author_name:
        name_lower = author_name.lower()
        for person_substr, role in PERSON_ROLE_OVERRIDES.items():
            if person_substr in name_lower:
                return role
    s = summary.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(k in s for k in keywords):
            return role
    return "other"


async def tool_info() -> dict:
    """Returns information about the lng_jira_worklog_report tool."""
    return {
        "description": """Reads Jira worklogs from sprints and calculates team and individual performance.

Handles inconsistent worklog tracking: collects worklogs from ALL hierarchy levels
(Story-level, Sub-task level, Bug/Task level) and flags potential double-counting
when both a story and its sub-tasks have worklogs logged.

Role breakdown (FE/BE/QA/BA/other) is detected automatically from issue summary keywords.
Extend ROLE_KEYWORDS in tool.py to match your team's naming conventions.

**Parameters:**
- `project` (string, required): Jira project key (e.g., "PROJ")
- `sprint_state` (string, optional): "closed", "active", or "closed,active" (default: "closed,active")
- `last_n_sprints` (int, optional): Number of last closed sprints to analyze (default: 6)
- `sprint_name` (string, optional): Filter by sprint name substring — overrides last_n_sprints
- `output_file` (string, optional): Path to save the JSON output
- `env_file` (string, optional): Path to .env file (default: ".env")

**Environment Variables Required:**
- `JIRA_URL`: Base URL of your Jira instance (e.g., "https://jiraeu.epam.com")

Auth options (first match wins):
1. `JIRA_SESSION` — browser session cookie value (recommended for SSO/Microsoft login).
   Get it: F12 → Network → any Jira request → Request Headers → copy `Cookie:` value.
2. `JIRA_USERNAME` + `JIRA_PASSWORD` — Basic auth (works only if Jira handles login itself).
3. `JIRA_AUTH` — Bearer/Personal Access Token.

**Returns:**
- Per-sprint: total hours, hours by person, breakdown by role (FE/BE/QA/other)
- Data quality warnings: issues with potential double-counting (story + subtasks both logged)
- Capacity summary: avg/min/max hours per person and per role across analyzed sprints
- Sprint list with state (active/closed/future) for backlog vs closed sprint distinction

**Example Usage:**
- Last 6 closed sprints: `{"project": "PROJ"}`
- Active sprint only:    `{"project": "PROJ", "sprint_state": "active"}`
- Specific sprint:       `{"project": "PROJ", "sprint_name": "Sprint 15"}`
- Save results:          `{"project": "PROJ", "output_file": "worklog_report.json"}`""",
        "schema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Jira project key (e.g., PROJ)"
                },
                "sprint_state": {
                    "type": "string",
                    "description": "Sprint filter: 'closed', 'active', or 'closed,active' (default: 'closed,active')"
                },
                "last_n_sprints": {
                    "type": "integer",
                    "description": "Number of last closed sprints to analyze (default: 6)"
                },
                "sprint_name": {
                    "type": "string",
                    "description": "Filter by exact sprint name — overrides last_n_sprints"
                },
                "output_file": {
                    "type": "string",
                    "description": "Optional: Path to save the JSON output"
                },
                "env_file": {
                    "type": "string",
                    "description": "Optional: Path to .env file (default: .env)"
                },
                "board_id": {
                    "type": "integer",
                    "description": "Optional: Jira board ID to use directly (skips board auto-discovery). Use when project has multiple boards."
                }
            },
            "required": ["project"]
        }
    }


def _make_headers(jira_session: str = "", jira_username: str = "",
                  jira_password: str = "", jira_auth: str = "") -> dict:
    """
    Build auth headers. Priority: session cookie > Basic auth > Bearer token.
    """
    headers = {"Accept": "application/json"}
    if jira_session:
        # Browser session cookie — works with SSO/Microsoft login
        headers["Cookie"] = jira_session
    elif jira_username and jira_password:
        token = base64.b64encode(f"{jira_username}:{jira_password}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    elif jira_auth:
        headers["Authorization"] = f"Bearer {jira_auth}"
    return headers


def _get_board_id(session: requests.Session, jira_url: str, project: str) -> int | None:
    """Find the first Scrum board for the given project key (falls back to any board)."""
    resp = session.get(
        f"{jira_url}/rest/agile/1.0/board",
        params={"projectKeyOrId": project, "maxResults": 50},
        timeout=30,
    )
    resp.raise_for_status()
    values = resp.json().get("values", [])
    if not values:
        return None
    # Prefer scrum boards — they support sprints
    scrum = [b for b in values if b.get("type", "").lower() == "scrum"]
    return scrum[0]["id"] if scrum else values[0]["id"]


def _get_sprints(session: requests.Session, jira_url: str, board_id: int, sprint_state: str) -> list:
    """Get all sprints for a board filtered by state (paginated)."""
    sprints = []
    start = 0
    while True:
        resp = session.get(
            f"{jira_url}/rest/agile/1.0/board/{board_id}/sprint",
            params={"state": sprint_state, "startAt": start, "maxResults": 50},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("values", [])
        sprints.extend(batch)
        if data.get("isLast", True) or len(batch) < 50:
            break
        start += 50
    return sprints


def _get_sprint_issues(session: requests.Session, jira_url: str, sprint_id: int) -> list:
    """Get all issues in a sprint with relevant fields (paginated)."""
    issues = []
    start = 0
    fields = "summary,issuetype,subtasks,worklog,parent,status"
    while True:
        resp = session.get(
            f"{jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue",
            params={"startAt": start, "maxResults": 100, "fields": fields},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("issues", [])
        issues.extend(batch)
        if start + 100 >= data.get("total", 0):
            break
        start += 100
    return issues


def _fetch_subtasks_bulk(session: requests.Session, jira_url: str,
                          story_keys: list[str]) -> dict[str, list]:
    """
    Fetch all subtasks for a list of story keys in one JQL query.
    Returns {story_key: [subtask_issue_dict, ...]}
    """
    if not story_keys:
        return {}

    # Jira JQL IN clause can handle many keys; chunk at 100 to be safe
    chunk_size = 100
    result: dict[str, list] = defaultdict(list)

    for i in range(0, len(story_keys), chunk_size):
        chunk = story_keys[i:i + chunk_size]
        keys_str = ", ".join(chunk)
        start = 0
        while True:
            resp = session.get(
                f"{jira_url}/rest/api/2/search",
                params={
                    "jql": f"parent IN ({keys_str})",
                    "fields": "summary,issuetype,worklog,parent",
                    "startAt": start,
                    "maxResults": 100,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for issue in data.get("issues", []):
                parent_key = issue.get("fields", {}).get("parent", {}).get("key", "")
                if parent_key:
                    result[parent_key].append(issue)
            total = data.get("total", 0)
            start += 100
            if start >= total:
                break

    return result


def _get_full_worklogs(session: requests.Session, jira_url: str,
                        issue_key: str, inline_worklog: dict) -> list:
    """Return all worklogs — uses inline data when complete, paginates otherwise."""
    total = inline_worklog.get("total", 0)
    if total == 0:
        return []
    # If inline payload is complete (total fits within what was returned)
    if total <= len(inline_worklog.get("worklogs", [])):
        return inline_worklog["worklogs"]
    # Need to paginate via dedicated endpoint
    worklogs = []
    start = 0
    while True:
        resp = session.get(
            f"{jira_url}/rest/api/2/issue/{issue_key}/worklog",
            params={"startAt": start, "maxResults": 100},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("worklogs", [])
        worklogs.extend(batch)
        if start + 100 >= data.get("total", 0):
            break
        start += 100
    return worklogs


def _extract_entries(worklogs: list, issue_key: str, issue_summary: str,
                     issue_type: str, source_level: str) -> list:
    """Normalize raw Jira worklog list into entry dicts (using raw seconds)."""
    entries = []
    for wl in worklogs:
        author = wl.get("author", {}).get("displayName", "Unknown")
        role = _detect_role(issue_summary, author)
        entries.append({
            "author": author,
            "seconds": wl.get("timeSpentSeconds", 0),
            "issue_key": issue_key,
            "issue_summary": issue_summary,
            "issue_type": issue_type,
            "source_level": source_level,
            "role": role,
            "date": wl.get("started", "")[:10],
        })
    return entries


def _process_sprint(session: requests.Session, jira_url: str, sprint: dict) -> dict:
    """
    Collect worklogs from ALL hierarchy levels in one sprint.

    Double-count prevention:
    - Stories AND their sub-tasks are both fetched.
    - Sub-tasks that appear directly in the sprint issue list are skipped
      (they're already covered via the story → subtasks batch fetch).
    - If a story AND its sub-tasks BOTH have worklogs, a data_quality_warning is emitted.
    """
    sprint_id = sprint["id"]
    issues = _get_sprint_issues(session, jira_url, sprint_id)

    # Separate stories, bugs/tasks, and raw subtask keys present in sprint list
    story_issues = []
    direct_issues = []   # bugs, tasks, etc.
    sprint_subtask_keys: set[str] = set()  # subtasks returned by sprint endpoint directly

    for issue in issues:
        issue_type_lower = issue.get("fields", {}).get("issuetype", {}).get("name", "").lower()
        if issue_type_lower in ("story", "user story"):
            story_issues.append(issue)
        elif issue_type_lower in ("sub-task", "subtask"):
            # Will be processed via parent story → skip direct processing
            sprint_subtask_keys.add(issue["key"])
        else:
            direct_issues.append(issue)

    # Batch-fetch all subtasks of stories in one JQL query
    story_keys = [s["key"] for s in story_issues]
    subtasks_by_story = _fetch_subtasks_bulk(session, jira_url, story_keys)

    all_entries: list[dict] = []
    data_quality_warnings: list[dict] = []

    # --- Process stories + their subtasks ---
    for issue in story_issues:
        key = issue["key"]
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        issue_type = fields.get("issuetype", {}).get("name", "Story")

        story_worklogs = _get_full_worklogs(session, jira_url, key, fields.get("worklog", {}))
        story_entries = _extract_entries(story_worklogs, key, summary, issue_type, "story")
        story_seconds = sum(e["seconds"] for e in story_entries)

        subtask_entries: list[dict] = []
        for st in subtasks_by_story.get(key, []):
            st_key = st["key"]
            st_fields = st.get("fields", {})
            st_summary = st_fields.get("summary", st_key)
            st_type = st_fields.get("issuetype", {}).get("name", "Sub-task")
            st_worklogs = _get_full_worklogs(session, jira_url, st_key, st_fields.get("worklog", {}))
            subtask_entries.extend(_extract_entries(st_worklogs, st_key, st_summary, st_type, "subtask"))

        subtask_seconds = sum(e["seconds"] for e in subtask_entries)

        if story_seconds > 0 and subtask_seconds > 0:
            data_quality_warnings.append({
                "issue": key,
                "summary": summary,
                "warning": "potential_double_count",
                "story_hours": round(story_seconds / 3600, 2),
                "subtask_hours": round(subtask_seconds / 3600, 2),
                "advice": "Worklogs on both Story and Sub-tasks — move all to Sub-tasks for consistency.",
            })

        all_entries.extend(story_entries)
        all_entries.extend(subtask_entries)

    # --- Process bugs, tasks, etc. ---
    for issue in direct_issues:
        key = issue["key"]
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        issue_type = fields.get("issuetype", {}).get("name", "")
        worklogs = _get_full_worklogs(session, jira_url, key, fields.get("worklog", {}))
        all_entries.extend(_extract_entries(worklogs, key, summary, issue_type, issue_type.lower()))

    # --- Aggregate by person (accumulate raw seconds, convert once at the end) ---
    by_person: dict[str, dict] = defaultdict(lambda: {
        "seconds": 0,
        "by_role": defaultdict(int),
        "issues": set(),
    })
    team_seconds = 0
    team_by_role_seconds: dict[str, int] = defaultdict(int)

    for e in all_entries:
        p = e["author"]
        by_person[p]["seconds"] += e["seconds"]
        by_person[p]["by_role"][e["role"]] += e["seconds"]
        by_person[p]["issues"].add(e["issue_key"])
        team_seconds += e["seconds"]
        team_by_role_seconds[e["role"]] += e["seconds"]

    def _secs_to_h(s: int) -> float:
        return round(s / 3600, 2)

    by_person_list = [
        {
            "name": name,
            "total_hours": _secs_to_h(data["seconds"]),
            "by_role": {
                r: _secs_to_h(data["by_role"][r])
                for r in ROLES
                if data["by_role"].get(r, 0) > 0
            },
            "issues_count": len(data["issues"]),
            "issues": sorted(data["issues"]),
        }
        for name, data in sorted(by_person.items(), key=lambda x: x[1]["seconds"], reverse=True)
    ]

    return {
        "id": sprint["id"],
        "name": sprint["name"],
        "state": sprint["state"],
        "start_date": (sprint.get("startDate") or "")[:10],
        "end_date": (sprint.get("endDate") or "")[:10],
        "team_total_hours": _secs_to_h(team_seconds),
        "team_by_role": {r: _secs_to_h(team_by_role_seconds[r]) for r in ROLES if team_by_role_seconds.get(r, 0) > 0},
        "members_count": len(by_person_list),
        "by_person": by_person_list,
        "data_quality_warnings": data_quality_warnings,
        "raw_entries_count": len(all_entries),
    }


def _build_capacity_summary(sprints_data: list) -> dict:
    """Capacity summary across closed sprints — avg/min/max per person and per role."""
    closed = [s for s in sprints_data if s["state"] == "closed"]
    if not closed:
        return {}

    person_data: dict[str, dict] = defaultdict(lambda: {"hours": [], "by_role": defaultdict(list)})

    for sprint in closed:
        for person in sprint["by_person"]:
            name = person["name"]
            person_data[name]["hours"].append(person["total_hours"])
            for role in ROLES:
                person_data[name]["by_role"][role].append(person["by_role"].get(role, 0.0))

    team_hours = [s["team_total_hours"] for s in closed]
    team_by_role_avg = {
        r: round(sum(s["team_by_role"].get(r, 0.0) for s in closed) / len(closed), 1)
        for r in ROLES
        if any(s["team_by_role"].get(r, 0.0) > 0 for s in closed)
    }

    by_person_capacity = []
    for name, data in sorted(person_data.items()):
        h = data["hours"]
        avg_by_role = {
            r: round(sum(data["by_role"][r]) / len(data["by_role"][r]), 1)
            for r in ROLES
            if sum(data["by_role"].get(r, [])) > 0
        }
        by_person_capacity.append({
            "name": name,
            "sprints_worked": len(h),
            "avg_hours_per_sprint": round(sum(h) / len(h), 1),
            "min_hours": min(h),
            "max_hours": max(h),
            "total_hours_all_sprints": round(sum(h), 1),
            "avg_by_role": avg_by_role,
        })

    by_person_capacity.sort(key=lambda x: x["avg_hours_per_sprint"], reverse=True)

    return {
        "sprints_analyzed": len(closed),
        "sprint_names": [s["name"] for s in closed],
        "avg_team_hours_per_sprint": round(sum(team_hours) / len(team_hours), 1),
        "min_team_hours": min(team_hours),
        "max_team_hours": max(team_hours),
        "avg_team_by_role": team_by_role_avg,
        "by_person": by_person_capacity,
    }


async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Reads Jira worklogs from sprints and calculates team and individual performance."""
    try:
        try:
            from dotenv import load_dotenv
        except ImportError:
            return [types.TextContent(type="text", text=json.dumps({
                "success": False,
                "error": "Required dependency not available: python-dotenv"
            }, indent=2))]

        project = parameters.get("project", "").strip()
        if not project:
            return [types.TextContent(type="text", text=json.dumps({
                "success": False, "error": "project parameter is required"
            }, indent=2))]

        sprint_state = parameters.get("sprint_state", "closed,active").strip()
        last_n_sprints = int(parameters.get("last_n_sprints", 6))
        sprint_name_filter = parameters.get("sprint_name", "").strip()
        output_file = parameters.get("output_file")
        env_file = parameters.get("env_file", ".env")

        # Load .env
        env_path = os.path.expanduser(env_file)
        if not os.path.isabs(env_path):
            env_path = os.path.abspath(env_path)
        if not os.path.exists(env_path):
            return [types.TextContent(type="text", text=json.dumps({
                "success": False, "error": f".env file not found at {env_path}"
            }, indent=2))]
        load_dotenv(env_path)

        jira_url = os.getenv("JIRA_URL", "").rstrip("/")
        jira_session = os.getenv("JIRA_SESSION", "")
        jira_username = os.getenv("JIRA_USERNAME", "")
        jira_password = os.getenv("JIRA_PASSWORD", "")
        jira_auth = os.getenv("JIRA_AUTH", "")

        if not jira_url:
            return [types.TextContent(type="text", text=json.dumps({
                "success": False, "error": "JIRA_URL not found in environment variables"
            }, indent=2))]
        if not jira_session and not (jira_username and jira_password) and not jira_auth:
            return [types.TextContent(type="text", text=json.dumps({
                "success": False,
                "error": (
                    "No Jira credentials found. Options:\n"
                    "1. JIRA_SESSION — browser cookie (for SSO/Microsoft login)\n"
                    "2. JIRA_USERNAME + JIRA_PASSWORD — Basic auth\n"
                    "3. JIRA_AUTH — Bearer/PAT token"
                )
            }, indent=2))]

        with requests.Session() as session:
            session.headers.update(_make_headers(jira_session, jira_username, jira_password, jira_auth))

            # Step 1: Find board
            board_id = parameters.get("board_id")
            if board_id:
                board_id = int(board_id)
            else:
                board_id = _get_board_id(session, jira_url, project)
            if board_id is None:
                return [types.TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": f"No board found for project '{project}'. Check the project key."
                }, indent=2))]

            # Step 2: Get sprints
            sprints = _get_sprints(session, jira_url, board_id, sprint_state)
            if not sprints:
                return [types.TextContent(type="text", text=json.dumps({
                    "success": False,
                    "error": f"No sprints found for board {board_id} with state '{sprint_state}'"
                }, indent=2))]

            # Step 3: Filter sprints
            if sprint_name_filter:
                sprints = [s for s in sprints if sprint_name_filter.lower() in s["name"].lower()]
            else:
                active_sprints = [s for s in sprints if s["state"] == "active"]
                closed_sprints = [s for s in sprints if s["state"] == "closed"]
                sprints = closed_sprints[-last_n_sprints:] + active_sprints

            if not sprints:
                return [types.TextContent(type="text", text=json.dumps({
                    "success": False, "error": "No sprints matched the filter criteria"
                }, indent=2))]

            # Step 4: Process each sprint
            sprints_data = [_process_sprint(session, jira_url, sprint) for sprint in sprints]

        # Step 5: Build capacity summary (closed sprints only)
        capacity_summary = _build_capacity_summary(sprints_data)

        # Step 6: Flatten data quality warnings with sprint context
        all_warnings = [
            {"sprint": sd["name"], **w}
            for sd in sprints_data
            for w in sd.get("data_quality_warnings", [])
        ]

        result = {
            "success": True,
            "operation": "jira_worklog_report",
            "project": project,
            "board_id": board_id,
            "sprints_processed": len(sprints_data),
            "sprints": sprints_data,
            "capacity_summary": capacity_summary,
            "data_quality_warnings": all_warnings,
            "role_detection_note": (
                "Roles auto-detected from issue summary keywords. "
                "Edit ROLE_KEYWORDS in tool.py to match your team's naming conventions."
            ),
        }

        if output_file:
            out_path = os.path.expanduser(output_file)
            if not os.path.isabs(out_path):
                out_path = os.path.abspath(out_path)
            dir_name = os.path.dirname(out_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            result["output_file"] = out_path

        return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except requests.exceptions.HTTPError as e:
        return [types.TextContent(type="text", text=json.dumps({
            "success": False,
            "error": f"Jira API error: {e.response.status_code} {e.response.text[:500]}"
        }, indent=2))]
    except requests.exceptions.ConnectionError:
        return [types.TextContent(type="text", text=json.dumps({
            "success": False,
            "error": "Cannot connect to Jira. Check JIRA_URL and network/VPN."
        }, indent=2))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({
            "success": False,
            "error": f"Unexpected error: {type(e).__name__}: {str(e)}"
        }, indent=2))]
