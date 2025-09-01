#!/usr/bin/env python3
"""
Provision Linear to mirror the Symphony Autonomous Enterprise hierarchy — **robust to plan/schema differences**.

Key hardening:
- Teams: plan-limit safe fallback already supported in v1? (Optional: reuse an existing team)
- Workflow states: always provide hex color; normalize type to lowercase; map 'triage'→'backlog'
- Labels: normalize named colors (e.g., 'purple') to hex
- Custom fields: auto-detect absence of Custom Fields API and skip
- Initiatives (a.k.a. Roadmaps/Initiatives): query by **name** (no `identifier`); if the API isn't available, skip
- Projects: query by **name**; do **not** pass `identifier` in create input

Usage:
  export LINEAR_API_KEY=xxxx
  python provision_linear_symphony_v2.py --template ./linear_template_single_team.yaml \
    [--fallback-team-name "Symphony"] [--team-map STRAT=SYMPHONY,PLAT=SYMPHONY]

Dependencies: pip install pyyaml requests
"""

from __future__ import annotations
import os
import sys
import argparse
import time
from typing import Any, Dict, List, Optional

try:
    import yaml  # PyYAML
except Exception:
    print("PyYAML is required. pip install pyyaml", file=sys.stderr)
    raise

import requests

GRAPHQL_URL = "https://api.linear.app/graphql"

# -----------------------------
# GraphQL client
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
            raise RuntimeError(f"GraphQL error: {data['errors'][0]}")
        return data["data"]

# -----------------------------
# Queries & Mutations (schema-tolerant)
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
    "teams_all": """
        query TeamsAll($first: Int!) {
          teams(first: $first) { nodes { id name key } }
        }
    """,
    "team_states": """
        query TeamStates($teamId: String!) {
          team(id: $teamId) { id states { nodes { id name type color } } }
        }
    """,
    "label_by_name": """
        query LabelByName($name: String!) {
          issueLabels(filter: { name: { eq: $name } }) { nodes { id name color } }
        }
    """,
    # May not exist on some plans; handled in code
    "custom_fields": """
        query CustomFields { customFields { nodes { id name type options { id name } } } }
    """,
    # Initiatives: query by NAME only (no identifier); may be entirely unavailable on some schemas
    "initiatives_by_name": """
        query InitiativesByName($name: String!) {
          initiatives(filter: { name: { eq: $name } }) { nodes { id name } }
        }
    """,
    # Projects: query by NAME only
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
    "custom_field_option_create": """
        mutation CustomFieldOptionCreate($input: CustomFieldOptionCreateInput!) {
          customFieldOptionCreate(input: $input) { success customFieldOption { id name } }
        }
    """,
    # Initiatives
    "initiative_create": """
        mutation InitiativeCreate($input: InitiativeCreateInput!) {
          initiativeCreate(input: $input) { success initiative { id name } }
        }
    """,
    "initiative_update": """
        mutation InitiativeUpdate($id: String!, $input: InitiativeUpdateInput!) {
          initiativeUpdate(id: $id, input: $input) { success }
        }
    """,
    # Projects
    "project_create": """
        mutation ProjectCreate($input: ProjectCreateInput!) {
          projectCreate(input: $input) { success project { id name } }
        }
    """,
    "project_update": """
        mutation ProjectUpdate($id: String!, $input: ProjectUpdateInput!) {
          projectUpdate(id: $id, input: $input) { success }
        }
    """,
    # Cycles (might require plan support)
    "cycle_create": """
        mutation CycleCreate($input: CycleCreateInput!) {
          cycleCreate(input: $input) { success cycle { id name } }
        }
    """,
}

# -----------------------------
# Helper lookups
# -----------------------------

def _resolve_team_id(client: LinearGQL, *, key: Optional[str] = None, name: Optional[str] = None) -> Optional[str]:
    if key:
        res = client.run(QUERIES["team_by_key"], {"key": key})
        nodes = res["teams"]["nodes"]
        if nodes:
            return nodes[0]["id"]
    if name:
        res = client.run(QUERIES["team_by_name"], {"name": name})
        nodes = res["teams"]["nodes"]
        if nodes:
            return nodes[0]["id"]
    return None


def get_any_team_id(client: LinearGQL) -> Optional[str]:
    try:
        res = client.run(QUERIES["teams_all"], {"first": 50})
        nodes = res.get("teams", {}).get("nodes", [])
        if nodes:
            return nodes[0]["id"]
    except Exception:
        pass
    return None

# -----------------------------
# Ensurers
# -----------------------------

def ensure_team(client: LinearGQL, name: str, key: Optional[str] = None, description: Optional[str] = None, *, fallback_team_id: Optional[str] = None) -> str:
    # Lookup existing by key or name
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

    try:
        out = client.run(MUTATIONS["team_create"], {"input": payload})
        return out["teamCreate"]["team"]["id"]
    except RuntimeError as e:
        msg = str(e)
        if "FORBIDDEN" in msg or "limit of teams" in msg or "Access denied" in msg:
            if fallback_team_id:
                print(f"[info] Team creation blocked. Reusing fallback team for '{name}'.")
                return fallback_team_id
            any_id = get_any_team_id(client)
            if any_id:
                print(f"[info] Team creation blocked. Reusing first existing team for '{name}'.")
                return any_id
        raise


def ensure_workflow_states(client: LinearGQL, team_id: str, states: List[Dict[str, Any]]):
    """Create missing workflow states by name/type/color.
    Linear requires `color` and expects `type` in lowercase: backlog|unstarted|started|completed|canceled.
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
                return "#EF4444"
            if "testing" in name_l or "validation" in name_l:
                return "#F59E0B"
            return "#3B82F6"
        if t == "completed":
            return "#10B981"
        if t == "canceled":
            return "#6B7280"
        return "#64748B"

    for st in states:
        st_name = st.get("name")
        st_type_norm = str(st.get("type", "unstarted")).lower()
        if st_type_norm == "triage":
            st_type_norm = "backlog"
        key = (st_name, st_type_norm)
        if key in existing:
            continue
        color = st.get("color") or _default_state_color(st_type_norm, st_name)
        inp = {"teamId": team_id, "name": st_name, "type": st_type_norm, "color": color}
        client.run(MUTATIONS["workflow_state_create"], {"input": inp})
        time.sleep(0.15)


def ensure_label(client: LinearGQL, name: str, color: Optional[str] = None, team_id: Optional[str] = None) -> str:
    def _norm_hex(c: Optional[str]) -> Optional[str]:
        if not c:
            return None
        c = str(c).strip().lower()
        if c.startswith("#") and (len(c) in (4, 7)):
            return c
        mapping = {
            "purple": "#A855F7", "blue": "#3B82F6", "green": "#10B981", "teal": "#14B8A6",
            "orange": "#F59E0B", "red": "#EF4444", "gray": "#9CA3AF", "indigo": "#6366F1",
            "yellow": "#EAB308", "black": "#000000",
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
    """Create missing custom fields and options; skip entirely if API absent."""
    try:
        current = client.run(QUERIES["custom_fields"])  # may fail on some schemas/plans
    except RuntimeError as e:
        msg = str(e)
        if "Cannot query field \"customFields\"" in msg or "GRAPHQL_VALIDATION_FAILED" in msg:
            print("[info] Custom Fields API not available. Skipping custom field provisioning.")
            return
        raise

    existing = {}
    for cf in current["customFields"]["nodes"]:
        existing[(cf["name"], cf["type"])] = cf

    type_map = {
        "text": "Text", "number": "Number", "date": "Date",
        "select": "SingleSelect", "single_select": "SingleSelect", "singleSelect": "SingleSelect",
        "multi_select": "MultiSelect", "multiSelect": "MultiSelect", "multi": "MultiSelect",
    }

    for f in fields:
        raw_type = f.get("type")
        t = type_map.get(str(raw_type), str(raw_type))
        key = (f.get("name"), t)
        if key in existing:
            cf_id = existing[key]["id"]
            if t in ("SingleSelect", "MultiSelect") and f.get("options"):
                have = {o["name"] for o in existing[key].get("options", [])}
                for opt in f["options"]:
                    if opt not in have:
                        client.run(MUTATIONS["custom_field_option_create"], {"input": {"customFieldId": cf_id, "name": opt}})
                        time.sleep(0.05)
            continue
        # Create new CF
        inp = {"name": f.get("name"), "type": t}
        if f.get("description"):
            inp["description"] = f["description"]
        out = client.run(MUTATIONS["custom_field_create"], {"input": inp})
        cf_id = out["customFieldCreate"]["customField"]["id"]
        if t in ("SingleSelect", "MultiSelect") and f.get("options"):
            for opt in f["options"]:
                client.run(MUTATIONS["custom_field_option_create"], {"input": {"customFieldId": cf_id, "name": opt}})
                time.sleep(0.05)
        time.sleep(0.1)


def ensure_initiative(client: LinearGQL, key: str, name: str, description: Optional[str] = None, parent_id: Optional[str] = None) -> str:
    """Ensure an initiative exists by NAME. Skip cleanly if Initiatives API is unavailable."""
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


def ensure_project(client: LinearGQL, key: str, name: str, team_id: str,
                   initiative_id: Optional[str] = None,
                   description: Optional[str] = None) -> str:
    # Minimal lookup (schema-safe)
    res = client.run(QUERIES["project_by_name"], {"name": name})
    nodes = res["projects"]["nodes"]
    if nodes:
        proj_id = nodes[0]["id"]
        upd: Dict[str, Any] = {"name": name}
        if description:
            upd["description"] = description
        if initiative_id:
            # Try with initiative link first; fall back if the schema rejects it
            try:
                upd_with_init = dict(upd)
                upd_with_init["initiativeId"] = initiative_id
                client.run(MUTATIONS["project_update"], {"id": proj_id, "input": upd_with_init})
            except RuntimeError:
                client.run(MUTATIONS["project_update"], {"id": proj_id, "input": upd})
        else:
            client.run(MUTATIONS["project_update"], {"id": proj_id, "input": upd})
        return proj_id

    # Create
    inp = {"name": name, "teamId": team_id}
    if description:
        inp["description"] = description
    if initiative_id:
        try:
            inp_with_init = dict(inp)
            inp_with_init["initiativeId"] = initiative_id
            out = client.run(MUTATIONS["project_create"], {"input": inp_with_init})
            return out["projectCreate"]["project"]["id"]
        except RuntimeError:
            pass  # retry without initiative link
    out = client.run(MUTATIONS["project_create"], {"input": inp})
    return out["projectCreate"]["project"]["id"]


def create_cycle(client: LinearGQL, team_id: str, name: str, start_date: str, end_date: str):
    inp = {"teamId": team_id, "name": name, "startsAt": start_date, "endsAt": end_date}
    try:
        client.run(MUTATIONS["cycle_create"], {"input": inp})
    except Exception as e:
        print(f"[warn] cycleCreate failed for team {team_id} ({name}): {e}")

# -----------------------------
# Template utilities
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
    return template.get("linear_template", template)

# -----------------------------
# Provision
# -----------------------------

def provision(template: Dict[str, Any], client: LinearGQL, *, fallback_team_id: Optional[str] = None, team_map_overrides: Optional[Dict[str, str]] = None):
    t = normalize_template(template)

    # 1) Teams
    team_defs = _get(t, ["teams"], [])
    team_map: Dict[str, str] = {}
    for team in team_defs:
        source_key = team.get("key", team["name"])
        if team_map_overrides and source_key in team_map_overrides:
            tid = team_map_overrides[source_key]
        else:
            tid = ensure_team(client, name=team["name"], key=team.get("key"), description=team.get("description"), fallback_team_id=fallback_team_id)
        team_map[source_key] = tid
    print(f"✔ Teams ensured: {len(team_map)}")

    # 2) Workflow states
    for team in team_defs:
        states = _get(team, ["workflow", "states"], [])
        if states:
            ensure_workflow_states(client, team_id=team_map.get(team.get("key", team["name"])), states=states)
    print("✔ Workflow states ensured")

    # 3) Labels
    for label in _get(t, ["labels"], []) or []:
        ensure_label(client, name=label.get("name"), color=label.get("color"))
    print("✔ Labels ensured")

    # 4) Custom fields (skip if API absent)
    cf_defs = _get(t, ["custom_fields", "global"], []) or t.get("customFields", [])
    norm_cf: List[Dict[str, Any]] = []
    for c in cf_defs:
        opts = None
        if isinstance(c.get("options"), list):
            opts = [o if isinstance(o, str) else o.get("name") for o in c["options"]]
        norm_cf.append({"name": c.get("name") or c.get("key"), "type": c.get("type"), "description": c.get("description"), "options": opts})
    if norm_cf:
        sync_custom_fields(client, norm_cf)
    print("✔ Custom fields synced or skipped")

    # 5) Initiatives (parents + children) — skip cleanly if API absent
    init_defs = _get(t, ["roadmaps"], [])
    initiative_id_by_key: Dict[str, str] = {}
    initiatives_enabled = True
    try:
        client.run(QUERIES["initiatives_by_name"], {"name": "__probe__"})
    except RuntimeError as e:
        if "Cannot query field \"initiatives\"" in str(e) or "GRAPHQL_VALIDATION_FAILED" in str(e):
            initiatives_enabled = False
            print("[info] Initiatives API not available. Skipping all initiative provisioning.")
    if initiatives_enabled:
        for r in init_defs:
            key = r.get("key");  name = r.get("name", key)
            if not key:
                continue
            init_id = ensure_initiative(client, key=key, name=name, description=r.get("description"))
            if init_id:
                initiative_id_by_key[key] = init_id
        for r in init_defs:
            for child in r.get("children", []) or []:
                ckey = child.get("key"); cname = child.get("name", ckey)
                parent_id = initiative_id_by_key.get(r.get("key"))
                cid = ensure_initiative(client, key=ckey, name=cname, description=child.get("description"), parent_id=parent_id)
                if cid:
                    initiative_id_by_key[ckey] = cid
        print(f"✔ Initiatives ensured: {len(initiative_id_by_key)}")
    else:
        print("✔ Initiatives skipped (unsupported)")

    # 6) Projects
    for p in _get(t, ["projects"], []) or []:
        key = p.get("key"); name = p.get("name", key)
        team_key = (p.get("owner_team") or p.get("team") or (p.get("team_keys") or p.get("teamKeys") or [None])[0] or p.get("team_key") or p.get("teamKey"))
        if isinstance(team_key, list):
            team_key = team_key[0]
        team_id = team_map.get(team_key) if team_key else next(iter(team_map.values()))
        initiative_key = p.get("initiative_key") or p.get("initiativeKey")
        initiative_id = initiative_id_by_key.get(initiative_key) if initiative_key else None
        ensure_project(client, key=key, name=name, team_id=team_id, initiative_id=initiative_id, description=p.get("description"))
    print("✔ Projects ensured")

    # 7) Cycles (best-effort)
    for c in _get(t, ["cycles", "team_cycles"], []) or _get(t, ["cycles"], []):
        team_key = c.get("team_key") or c.get("teamKey")
        name = c.get("name"); start = c.get("start") or c.get("start_date") or c.get("startDate"); end = c.get("end") or c.get("end_date") or c.get("endDate")
        if not (team_key and name and start and end):
            continue
        team_id = team_map.get(team_key)
        if team_id:
            create_cycle(client, team_id=team_id, name=name, start_date=start, end_date=end)
    print("✔ Cycles created where dates provided (or skipped if unsupported)")

    if _get(t, ["default_issue_templates"], []) or _get(t, ["views"], []) or _get(t, ["automations"], []):
        print("ℹ Templates/Views/Automations may require plan features. Extend MUTATIONS if available in your workspace.")

# -----------------------------
# CLI
# -----------------------------

def _parse_team_map(map_str: str) -> Dict[str, str]:
    mapping = {}
    for pair in map_str.split(","):
        if not pair or "=" not in pair:
            continue
        src, dst = pair.split("=", 1)
        mapping[src.strip()] = dst.strip()
    return mapping


def main():
    parser = argparse.ArgumentParser(description="Provision Linear from Symphony template YAML (robust)")
    parser.add_argument("--template", required=True, help="Path to YAML template (e.g., the single-team Linear YAML)")
    parser.add_argument("--fallback-team-key", help="Existing team KEY to reuse if creation is blocked")
    parser.add_argument("--fallback-team-name", help="Existing team NAME to reuse if creation is blocked")
    parser.add_argument("--team-map", help="Map Symphony team keys to existing team keys/names: STRAT=SYMPHONY,PLAT=SYMPHONY")
    args = parser.parse_args()

    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Set LINEAR_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    with open(args.template, "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    client = LinearGQL(api_key)

    fallback_team_id = None
    if args.fallback_team_key or args.fallback_team_name:
        fallback_team_id = _resolve_team_id(client, key=args.fallback_team_key, name=args.fallback_team_name)
        if not fallback_team_id:
            print("[warn] Could not resolve fallback team; will try standard creation, then reuse first existing team if blocked.")

    team_map_overrides: Optional[Dict[str, str]] = None
    if args.team_map:
        user_map = _parse_team_map(args.team_map)
        team_map_overrides = {}
        for src, dst in user_map.items():
            dst_id = _resolve_team_id(client, key=dst) or _resolve_team_id(client, name=dst)
            if not dst_id:
                print(f"[warn] Could not resolve destination team '{dst}' for mapping {src}; skipping this mapping.")
                continue
            team_map_overrides[src] = dst_id

    provision(template, client, fallback_team_id=fallback_team_id, team_map_overrides=team_map_overrides)


if __name__ == "__main__":
    main()
