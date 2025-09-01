#!/usr/bin/env python3
"""
Provision Linear to mirror the Symphony Autonomous Enterprise hierarchy.

Reads the Linear template YAML (from the canvas version or your own file) and
creates/updates Teams, Workflow States, Labels, Custom Fields, Initiatives (Roadmaps),
Projects, and Cycles using Linear's GraphQL API.

Usage:
  export LINEAR_API_KEY=xxxx
  python provision_linear_symphony.py --template ./linear_template.yaml

Notes:
- This script aims to be **idempotent**: it looks up by unique keys/names first.
- Automations and Saved Views are noted as TODOs because Linear's public GraphQL
  coverage for those features can change; you can extend the MUTATIONS section
  if they become available in your workspace.
- The script targets the YAML schema created in the canvas document
  "Linear Master Workspace Template — Symphony Autonomous Enterprise" where the
  root key is `linear_template`. Minimal shims are included to handle a flatter
  schema if needed.
"""

from __future__ import annotations
import os
import sys
import argparse
import time
from typing import Any, Dict, List, Optional

try:
    import yaml  # PyYAML
except Exception as e:
    print("PyYAML is required. pip install pyyaml", file=sys.stderr)
    raise

import requests

GRAPHQL_URL = "https://api.linear.app/graphql"

# -----------------------------
# Helpers: GraphQL client
# -----------------------------
class LinearGQL:
    def __init__(self, api_key: str, url: str = GRAPHQL_URL):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": api_key,
        })
        self.url = url

    def run(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"query": query, "variables": variables or {}}
        r = self.session.post(self.url, json=payload, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"GraphQL HTTP {r.status_code}: {r.text}")
        data = r.json()
        if "errors" in data:
            # Surface first error for brevity
            raise RuntimeError(f"GraphQL error: {data['errors'][0]}")
        return data["data"]

# -----------------------------
# Queries & Mutations
# -----------------------------
QUERIES = {
    "team_by_key": """
        query TeamByKey($key: String!) {
          teams(filter: {key: {eq: $key}}) { nodes { id name key } }
        }
    """,
    "team_by_name": """
        query TeamByName($name: String!) {
          teams(filter: {name: {eq: $name}}) { nodes { id name key } }
        }
    """,
    "team_states": """
        query TeamStates($teamId: String!) {
          team(id: $teamId) {
            id
            states { nodes { id name type color } }
          }
        }
    """,
    "label_by_name": """
        query LabelByName($name: String!) {
          issueLabels(filter: { name: { eq: $name } }) { nodes { id name color } }
        }
    """,
    "custom_fields": """
        query CustomFields {
          customFields { nodes { id name type options { id name } } }
        }
    """,
    "initiatives_by_name": """
        query InitiativesByName($name: String!) {
          initiatives(filter: { name: { eq: $name } }) { nodes { id name } }
        }
    """,
    "project_by_name": """
        query ProjectByName($name: String!) {
          projects(filter: { name: { eq: $name } }) { nodes { id name } }
        }
    """,
}

MUTATIONS = {
    "team_create": """
        mutation TeamCreate($input: TeamCreateInput!) {
          teamCreate(input: $input) { success team { id name key } }
        }
    """,
    "workflow_state_create": """
        mutation WorkflowStateCreate($input: WorkflowStateCreateInput!) {
          workflowStateCreate(input: $input) { success workflowState { id name type color } }
        }
    """,
    "label_create": """
        mutation IssueLabelCreate($input: IssueLabelCreateInput!) {
          issueLabelCreate(input: $input) { success issueLabel { id name color } }
        }
    """,
    "custom_field_create": """
        mutation CustomFieldCreate($input: CustomFieldCreateInput!) {
          customFieldCreate(input: $input) { success customField { id name type } }
        }
    """,
    "custom_field_update": """
        mutation CustomFieldUpdate($id: String!, $input: CustomFieldUpdateInput!) {
          customFieldUpdate(id: $id, input: $input) { success }
        }
    """,
    "custom_field_option_create": """
        mutation CustomFieldOptionCreate($input: CustomFieldOptionCreateInput!) {
          customFieldOptionCreate(input: $input) { success customFieldOption { id name } }
        }
    """,
    "initiative_create": """
        mutation InitiativeCreate($input: InitiativeCreateInput!) {
          initiativeCreate(input: $input) { success initiative { id name identifier } }
        }
    """,
    "initiative_update": """
        mutation InitiativeUpdate($id: String!, $input: InitiativeUpdateInput!) {
          initiativeUpdate(id: $id, input: $input) { success }
        }
    """,
    "project_create": """
        mutation ProjectCreate($input: ProjectCreateInput!) {
          projectCreate(input: $input) { success project { id name identifier } }
        }
    """,
    "project_update": """
        mutation ProjectUpdate($id: String!, $input: ProjectUpdateInput!) {
          projectUpdate(id: $id, input: $input) { success }
        }
    """,
    "cycle_create": """
        mutation CycleCreate($input: CycleCreateInput!) {
          cycleCreate(input: $input) { success cycle { id name } }
        }
    """,
}

# -----------------------------
# Provisioning functions
# -----------------------------

def ensure_team(client: LinearGQL, name: str, key: Optional[str] = None, description: Optional[str] = None) -> str:
    if key:
        res = client.run(QUERIES["team_by_key"], {"key": key})
        nodes = res["teams"]["nodes"]
        if nodes:
            return nodes[0]["id"]
    res = client.run(QUERIES["team_by_name"], {"name": name})
    nodes = res["teams"]["nodes"]
    if nodes:
        return nodes[0]["id"]

    payload = {"name": name}
    if key:
        payload["key"] = key
    if description:
        payload["description"] = description
    out = client.run(MUTATIONS["team_create"], {"input": payload})
    return out["teamCreate"]["team"]["id"]


def ensure_workflow_states(client: LinearGQL, team_id: str, states: List[Dict[str, Any]]):
    """Create any missing workflow states by name/type/color.
    Linear requires a color (String!) and expects lowercase state types:
    backlog | unstarted | started | completed | canceled
    We also map any 'triage' usage to 'backlog'.
    """
    current = client.run(QUERIES["team_states"], {"teamId": team_id})
    existing = {(s["name"], str(s["type"]).lower()): s for s in current["team"]["states"]["nodes"]}

    def _default_state_color(state_type: str, name: str) -> str:
        t = (state_type or "unstarted").lower()
        name_l = (name or "").lower()
        if t in ("backlog", "unstarted"):
            return "#9CA3AF"  # gray-400
        if t == "started":
            if "security" in name_l:
                return "#EF4444"  # red-500
            if "testing" in name_l or "validation" in name_l:
                return "#F59E0B"  # amber-500
            return "#3B82F6"  # blue-500
        if t == "completed":
            return "#10B981"  # green-500
        if t == "canceled":
            return "#6B7280"  # gray-500
        return "#64748B"  # slate-500

    for st in states:
        st_name = st.get("name")
        st_type_raw = st.get("type", "unstarted")
        st_type_norm = str(st_type_raw).lower()
        if st_type_norm == "triage":
            st_type_norm = "backlog"
        key = (st_name, st_type_norm)
        if key in existing:
            continue
        color = st.get("color") or _default_state_color(st_type_norm, st_name)
        inp = {
            "teamId": team_id,
            "name": st_name,
            "type": st_type_norm,
            "color": color,
        }
        client.run(MUTATIONS["workflow_state_create"], {"input": inp})
        time.sleep(0.2)


def ensure_label(client: LinearGQL, name: str, color: Optional[str] = None, team_id: Optional[str] = None) -> str:
    def _norm_hex(c: Optional[str]) -> Optional[str]:
        if not c:
            return None
        c = str(c).strip().lower()
        if c.startswith("#") and (len(c) in (4, 7)):
            return c
        mapping = {
            "purple": "#A855F7",
            "blue": "#3B82F6",
            "green": "#10B981",
            "teal": "#14B8A6",
            "orange": "#F59E0B",
            "red": "#EF4444",
            "gray": "#9CA3AF",
            "indigo": "#6366F1",
            "yellow": "#EAB308",
            "black": "#000000",
        }
        return mapping.get(c, "#64748B")

    res = client.run(QUERIES["label_by_name"], {"name": name})
    nodes = res["issueLabels"]["nodes"]
    if nodes:
        return nodes[0]["id"]
    inp = {"name": name}
    nx = _norm_hex(color)
    if nx:
        inp["color"] = nx
    if team_id:
        inp["teamId"] = team_id
    out = client.run(MUTATIONS["label_create"], {"input": inp})
    return out["issueLabelCreate"]["issueLabel"]["id"]


def sync_custom_fields(client: LinearGQL, fields: List[Dict[str, Any]]):
    """Create missing custom fields and options. Matches by name + type.
    If the workspace/plan doesn't support Custom Fields, we detect the schema error and skip gracefully.
    """
    try:
        current = client.run(QUERIES["custom_fields"])  # may not exist in some schemas/plans
    except RuntimeError as e:
        msg = str(e)
        if "Cannot query field \"customFields\"" in msg or "GRAPHQL_VALIDATION_FAILED" in msg:
            print("[info] Custom Fields API not available for this workspace/plan. Skipping custom field provisioning.")
            return
        raise

    existing = {}
    for cf in current["customFields"]["nodes"]:
        existing[(cf["name"], cf["type"])] = cf

    type_map = {
        "text": "Text",
        "number": "Number",
        "date": "Date",
        "select": "SingleSelect",
        "single_select": "SingleSelect",
        "singleSelect": "SingleSelect",
        "multi_select": "MultiSelect",
        "multiSelect": "MultiSelect",
        "multi": "MultiSelect",
    }

    for f in fields:
        raw_type = f.get("type")
        t = type_map.get(str(raw_type), str(raw_type))
        key = (f.get("name"), t)
        if key in existing:
            cf_id = existing[key]["id"]
            # Ensure options for selects
            if t in ("SingleSelect", "MultiSelect") and f.get("options"):
                have = {o["name"] for o in existing[key].get("options", [])}
                for opt in f["options"]:
                    if opt not in have:
                        client.run(MUTATIONS["custom_field_option_create"], {
                            "input": {"customFieldId": cf_id, "name": opt}
                        })
                        time.sleep(0.1)
            continue
        # Create
        inp = {"name": f.get("name"), "type": t}
        if f.get("description"):
            inp["description"] = f["description"]
        out = client.run(MUTATIONS["custom_field_create"], {"input": inp})
        cf_id = out["customFieldCreate"]["customField"]["id"]
        if t in ("SingleSelect", "MultiSelect") and f.get("options"):
            for opt in f["options"]:
                client.run(MUTATIONS["custom_field_option_create"], {
                    "input": {"customFieldId": cf_id, "name": opt}
                })
                time.sleep(0.1)
        time.sleep(0.2)


def ensure_initiative(client: LinearGQL, key: str, name: str, description: Optional[str] = None, parent_id: Optional[str] = None) -> str:
    """Ensure an initiative exists by NAME. If Initiatives API is unavailable, skip gracefully."""
    try:
        res = client.run(QUERIES["initiatives_by_name"], {"name": name})
        nodes = res["initiatives"]["nodes"]
    except RuntimeError as e:
        msg = str(e)
        if "Cannot query field \"initiatives\"" in msg or "GRAPHQL_VALIDATION_FAILED" in msg:
            print("[info] Initiatives API not available. Skipping initiative provisioning.")
            return ""
        raise

    if nodes:
        init_id = nodes[0]["id"]
        update_input = {"name": name}
        if description:
            update_input["description"] = description
        if parent_id:
            update_input["parentId"] = parent_id
        try:
            client.run(MUTATIONS["initiative_update"], {"id": init_id, "input": update_input})
        except RuntimeError:
            pass
        return init_id

    inp = {"name": name}
    if description:
        inp["description"] = description
    if parent_id:
        inp["parentId"] = parent_id
    try:
        out = client.run(MUTATIONS["initiative_create"], {"input": inp})
        return out["initiativeCreate"]["initiative"]["id"]
    except RuntimeError as e:
        msg = str(e)
        if "Cannot query field" in msg or "invalid" in msg:
            print("[info] Initiative creation not supported. Skipping.")
            return ""
        raise


def ensure_project(client: LinearGQL, key: str, name: str, team_id: str, initiative_id: Optional[str] = None, description: Optional[str] = None) -> str:
    # Lookup by name for schema compatibility
    res = client.run(QUERIES["project_by_name"], {"name": name})
    nodes = res["projects"]["nodes"]
    if nodes:
        proj_id = nodes[0]["id"]
        upd: Dict[str, Any] = {"name": name}
        if description:
            upd["description"] = description
        if initiative_id:
            # Try to link initiative; if schema rejects, retry without
            try:
                upd_with_init = dict(upd)
                upd_with_init["initiativeId"] = initiative_id
                client.run(MUTATIONS["project_update"], {"id": proj_id, "input": upd_with_init})
            except RuntimeError:
                client.run(MUTATIONS["project_update"], {"id": proj_id, "input": upd})
        else:
            client.run(MUTATIONS["project_update"], {"id": proj_id, "input": upd})
        return proj_id

    # Create: prefer teamIds (list) for newer schemas; fall back to teamId if needed
    base_inp: Dict[str, Any] = {"name": name}
    if description:
        base_inp["description"] = description

    # First attempt with teamIds
    inp_teamids = dict(base_inp)
    inp_teamids["teamIds"] = [team_id]
    if initiative_id:
        inp_teamids["initiativeId"] = initiative_id
    try:
        out = client.run(MUTATIONS["project_create"], {"input": inp_teamids})
        return out["projectCreate"]["project"]["id"]
    except RuntimeError:
        # Fallback to legacy single teamId if supported in your workspace
        inp_teamid = dict(base_inp)
        inp_teamid["teamId"] = team_id
        if initiative_id:
            inp_teamid["initiativeId"] = initiative_id
        out = client.run(MUTATIONS["project_create"], {"input": inp_teamid})
        return out["projectCreate"]["project"]["id"]


def create_cycle(client: LinearGQL, team_id: str, name: str, start_date: str, end_date: str):
    inp = {"teamId": team_id, "name": name, "startsAt": start_date, "endsAt": end_date}
    try:
        client.run(MUTATIONS["cycle_create"], {"input": inp})
    except Exception as e:
        print(f"[warn] cycleCreate failed for team {team_id} ({name}): {e}")

# -----------------------------
# Template parsing helpers
# -----------------------------

def _get(template: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    cur = template
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def normalize_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """Accept either root or `linear_template` wrapper; return unified dict."""
    if "linear_template" in template:
        return template["linear_template"]
    return template

# -----------------------------
# Main Orchestration
# -----------------------------

def provision(template: Dict[str, Any], client: LinearGQL):
    t = normalize_template(template)

    # 1) Teams
    team_defs = _get(t, ["teams"], [])
    team_map: Dict[str, str] = {}
    for team in team_defs:
        tid = ensure_team(client, name=team["name"], key=team.get("key"), description=team.get("description"))
        team_map[team.get("key", team["name"]) ] = tid
    print(f"✔ Teams ensured: {len(team_map)}")

    # 2) States per team
    for team in team_defs:
        states = _get(team, ["workflow", "states"], [])
        if states:
            ensure_workflow_states(client, team_id=team_map.get(team.get("key", team["name"])), states=states)
    print("✔ Workflow states ensured")

    # 3) Labels (workspace-scoped)
    for label in _get(t, ["labels"], []) or []:
        ensure_label(client, name=label.get("name"), color=label.get("color"))
    print("✔ Labels ensured")

    # 4) Custom fields
    # Accept both `custom_fields.global` (as in the canvas template) and flat `customFields`
    cf_defs = _get(t, ["custom_fields", "global"], []) or t.get("customFields", [])
    norm_cf: List[Dict[str, Any]] = []
    for c in cf_defs:
        if "options" in c and isinstance(c["options"], list):
            opts = [o if isinstance(o, str) else o.get("name") for o in c["options"]]
        else:
            opts = None
        norm_cf.append({
            "name": c.get("name") or c.get("key"),
            "type": c.get("type"),
            "description": c.get("description"),
            "options": opts,
        })
    if norm_cf:
        sync_custom_fields(client, norm_cf)
    print("✔ Custom fields synced")

    # 5) Initiatives (Roadmaps Level 1/2)
    init_defs = _get(t, ["roadmaps"], [])
    initiative_id_by_key: Dict[str, str] = {}
    # First pass create parents
    for r in init_defs:
        key = r.get("key")
        if not key:
            continue
        name = r.get("name", key)
        init_id = ensure_initiative(client, key=key, name=name, description=r.get("description"))
        if init_id:
            initiative_id_by_key[key] = init_id
    # Children
    for r in init_defs:
        for child in r.get("children", []) or []:
            ckey = child.get("key")
            if not ckey:
                continue
            cname = child.get("name", ckey)
            parent_id = initiative_id_by_key.get(r.get("key"))
            cid = ensure_initiative(client, key=ckey, name=cname, description=child.get("description"), parent_id=parent_id)
            if cid:
                initiative_id_by_key[ckey] = cid
    print(f"✔ Initiatives ensured: {len(initiative_id_by_key)}")

    # 6) Projects
    for p in _get(t, ["projects"], []) or []:
        key = p.get("key")
        name = p.get("name", key)
        team_key = (p.get("owner_team") or p.get("team") or (p.get("team_keys") or p.get("teamKeys") or [None])[0] or p.get("team_key") or p.get("teamKey"))
        if isinstance(team_key, list):
            team_key = team_key[0]  # assign primary team; you can extend to create multiple projects per team
        team_id = team_map.get(team_key) if team_key else None
        if not team_id:
            # Fallback: put under first available team
            team_id = next(iter(team_map.values()))
        initiative_key = p.get("initiative_key") or p.get("initiativeKey")
        initiative_id = initiative_id_by_key.get(initiative_key) if initiative_key else None
        ensure_project(client, key=key, name=name, team_id=team_id, initiative_id=initiative_id, description=p.get("description"))
    print("✔ Projects ensured")

    # 7) Cycles (optional)
    for c in _get(t, ["cycles", "team_cycles"], []) or _get(t, ["cycles"], []):
        team_key = c.get("team_key") or c.get("teamKey")
        name = c.get("name")
        start = c.get("start") or c.get("start_date") or c.get("startDate")
        end = c.get("end") or c.get("end_date") or c.get("endDate")
        if not (team_key and name and start and end):
            continue
        team_id = team_map.get(team_key)
        if team_id:
            create_cycle(client, team_id=team_id, name=name, start_date=start, end_date=end)
    print("✔ Cycles (best-effort) created when provided with dates")

    # 8) TODOs: issue templates, saved views, automations
    if _get(t, ["default_issue_templates"], []) or _get(t, ["views"], []) or _get(t, ["automations"], []):
        print("ℹ Some features such as Templates/Views/Automations may need workspace feature flags. Extend MUTATIONS as supported by your Linear plan.")


# -----------------------------
# CLI
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Provision Linear from Symphony template YAML")
    parser.add_argument("--template", required=True, help="Path to YAML template (e.g., the canvas-exported Linear YAML)")
    args = parser.parse_args()

    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Set LINEAR_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    with open(args.template, "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    client = LinearGQL(api_key)
    provision(template, client)


if __name__ == "__main__":
    main()
