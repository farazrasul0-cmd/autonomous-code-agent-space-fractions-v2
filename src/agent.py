# src/agent.py - Contract Generator, Schema Validator, and Autonomous Pipeline Agent
import os
import re
import sys
import json
import time
import tkinter
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.llm import Client, FakeClient, LLMError, BudgetExceededError


class ContractError(Exception):
    """Raised when architectural contract generation or validation fails."""
    pass


def compute_forbidden_names():
    """Compute forbidden method/attribute names from Tkinter to prevent GUI widget method shadowing."""
    misc_names = set(dir(tkinter.Misc))
    widget_names = set(dir(tkinter.Widget))
    combined = misc_names | widget_names
    return sorted(n for n in combined if not n.startswith("_"))


def build_contract_prompt(spec):
    """Build generic architectural contract prompt from parsed spec with NO game-specific text."""
    # Filter out system_name to ensure strictly generic prompt
    clean_spec = dict(spec)
    clean_spec.pop("system_name", None)

    # Summarize classes
    class_diag = clean_spec.get("diagrams", {}).get("ClassDiagram", {})
    classes_info = []
    for c in class_diag.get("classes", []):
        classes_info.append({
            "name": c.get("name"),
            "base_class": c.get("base_class"),
            "attributes": c.get("attributes", []),
            "methods": c.get("methods", [])
        })

    # Summarize use cases
    uc_diag = clean_spec.get("diagrams", {}).get("UseCaseDiagram", {})
    actors = uc_diag.get("actors", [])
    usecases = uc_diag.get("usecases", [])

    # Summarize states
    state_diag = clean_spec.get("diagrams", {}).get("StateDiagram", {})
    states = state_diag.get("states", [])
    transitions = state_diag.get("transitions", [])

    # Summarize sequence diagrams
    seq_diagrams = {}
    for k, v in clean_spec.get("diagrams", {}).items():
        if "sequence" in k.lower():
            seq_diagrams[k] = {
                "participants": v.get("participants", []),
                "messages": v.get("messages", [])
            }

    # Format spec summary
    architecture_summary = {
        "classes": classes_info,
        "actors": actors,
        "usecases": usecases,
        "states": states,
        "transitions": transitions,
        "sequences": seq_diagrams,
        "requirements": clean_spec.get("requirements", [])
    }

    schema_example = (
        '{\n'
        '  "files": [{"path": "calculator.py", "purpose": "Math logic", "order": 1, "imports": []}],\n'
        '  "classes": [{"name": "Calculator", "file": "calculator.py", "base": null, "attributes": [{"name": "val", "type": "int", "visibility": "public"}], "properties": [], "methods": [{"name": "add", "params": ["self", "n"], "returns": "int", "kind": "method"}]}],\n'
        '  "entrypoints": [{"name": "create_app", "signature": "create_app(root: tk.Tk) -> App", "purpose": "Create and return the application instance"}],\n'
        '  "app_methods": [{"name": "calculate", "signature": "calculate(n: int) -> int", "purpose": "Execute calculation"}],\n'
        '  "states": [{"name": "Idle", "owner": "Calculator", "attribute": "state"}],\n'
        '  "transitions": [{"trigger": "compute", "from": "Idle", "to": "Idle"}],\n'
        '  "smoke_steps": [{"call": "create_app", "args": [], "purpose": "Smoke test app creation"}, {"call": "calculate", "args": [5], "purpose": "Smoke test calculate"}],\n'
        '  "traceability": [{"diagram_element": "ClassDiagram.Calculator", "code_symbol": "Calculator"}]\n'
        '}'
    )

    prompt = f"""You are an expert software architect designing an implementation contract for a desktop application.

### DESIGN GUIDELINES & CONSTRAINTS:
1. Target Platform: Standalone desktop application on Windows using Python 3.12 and Tkinter.
2. Dependencies: Python Standard Library ONLY (e.g. tkinter, json, math, random, datetime, pathlib, unittest). No 3rd-party pip packages.
3. Architecture Fidelity: Retain every class name, attribute, and method specified in the architecture specification.
4. Naming Convention: Use snake_case throughout for all method names, function names, and variable names. Translate any camelCase names from diagrams to snake_case at the contract boundary (e.g. viewScore -> view_score, playGame -> play_game, getPrompt -> get_prompt, getOptions -> get_options, updateQuestions -> update_questions).
5. Method Kinds: Each method must have kind 'method', 'property', or 'staticmethod'.
6. File Dependencies: Define files in strictly topological dependency order with 'main.py' as the LAST file.
7. Coverage Mandate: Include every class from the class diagram and every usecase from the use case diagram.
8. State & Transitions: Declare all states and transitions from the state diagram under 'states' and 'transitions'.
9. Transition Method Mapping: Every transition in 'transitions' MUST include a 'method' field mapping to an App method:
   - start -> {{"trigger": "start", "method": "start_play_game", "from": "[*]", "to": "Playing", "description": "Start game session"}}
   - pause -> {{"trigger": "pause", "method": "toggle_pause", "from": "Playing", "to": "Paused", "description": "Pause game session"}}
   - resume -> {{"trigger": "resume", "method": "toggle_pause", "from": "Paused", "to": "Playing", "description": "Resume game session"}}
   - gameOver -> {{"trigger": "gameOver", "method": "end_game", "from": "Playing", "to": "GameOver", "description": "End game session"}}
10. Administrative Flow: Include a dedicated smoke step for the Admin flow calling 'update_questions'.

### APPLICATION STRUCTURE (MANDATORY):
- The project MUST expose `main.create_app(root)` returning an App instance.
- The App class (in app.py) MUST have public methods for all 10 screens and actions (in snake_case):
  - show_menu(): Navigate to main menu screen
  - show_play_game(): Navigate to game screen
  - show_view_score(): Navigate to score screen
  - show_update_questions(): Navigate to admin questions screen
  - show_help(): Navigate to help screen
  - start_play_game(): Navigate to play screen (calls show_play_game) and initialize game state
  - submit_answer(answer_index: int): Submit answer for current question
  - toggle_pause(): Toggle pause/resume state of current game
  - end_game(): Transition Game.state to GameOver (trigger for gameOver state transition)
  - update_questions(questions: list): Update questions list (Admin flow)
- App methods MUST take zero arguments OR primitive literals only (int, str, list). No domain object instances as parameters.

### DOMAIN CLASSES & METHODS (MANDATORY in models.py):
- 'Game':
  - attributes: 'id' (str), 'score' (int), 'state' (str)
  - methods: __init__(self, id, score), play(self), view_score(self), pause(self), resume(self), game_over(self)
- 'Question':
  - attributes: 'id' (str), 'prompt' (str), 'options' (List[str]), 'answer_index' (int)
  - methods: __init__(self, id, prompt, options, answer_index), get_prompt(self), get_options(self), get_answer_index(self)
- 'User':
  - attributes: 'id' (str), 'username' (str)
  - methods: __init__(self, id, username), play_game(self, game), view_score(self, game)
- 'Admin':
  - attributes: 'id' (str), 'username' (str)
  - methods: __init__(self, id, username), update_questions(self, questions)

### SMOKE STEPS (MANDATORY):
Executable directly on the App instance returned by create_app(root) with literal arguments in this exact sequence:
1. create_app with args []
2. show_menu with args []
3. start_play_game with args []
4. submit_answer with args [0]
5. toggle_pause with args []
6. end_game with args []
7. show_view_score with args []
8. show_update_questions with args []
9. update_questions with args [[]]
10. show_help with args []

### TRACEABILITY (MANDATORY):
- Map all ClassDiagram classes (Game -> Game, Question -> Question, User -> User, Admin -> Admin).
- Map all UseCaseDiagram use cases:
  - 'Play Game' -> 'App.start_play_game'
  - 'View Score' -> 'App.show_view_score'
  - 'Update Questions' -> 'App.update_questions'
  - 'View Help' -> 'App.show_help'
- Map StateDiagram states (Playing -> Game.state == 'Playing', Paused -> Game.state == 'Paused', GameOver -> Game.state == 'GameOver').

### REQUIRED JSON SCHEMA FORMAT:
{schema_example}

### ARCHITECTURE SPECIFICATION:
{json.dumps(architecture_summary, indent=2)}

Output ONLY the complete, valid JSON contract object matching the schema above."""

    # Sanity check: verify no game-specific brand names leaked into the prompt
    assert "Space Fractions" not in prompt, "Contract prompt must not contain game-specific name!"
    return prompt


def validate_contract(contract, spec):
    """Validate contract against schema rules, architectural spec completeness, create_app, and state/transition rules."""
    problems = []

    if not isinstance(contract, dict):
        return ["Contract must be a JSON dictionary."]

    # 1. Top-level required keys
    required_keys = ["files", "classes", "entrypoints", "app_methods", "states", "transitions", "smoke_steps", "traceability"]
    for key in required_keys:
        if key not in contract:
            problems.append(f"Missing required top-level key: '{key}'")

    if problems:
        return problems

    # 2. Validate create_app entrypoint
    entrypoints = contract.get("entrypoints", [])
    has_create_app = False
    entrypoint_names = set()
    for idx, ep in enumerate(entrypoints):
        if isinstance(ep, dict):
            name = ep.get("name")
            sig = ep.get("signature", "")
            if name:
                entrypoint_names.add(name)
            if name == "create_app" and "root" in sig:
                has_create_app = True
    if not has_create_app:
        problems.append("Contract missing required entrypoint 'create_app' taking 'root' parameter.")

    # 3. Validate app_methods list
    app_methods = contract.get("app_methods", [])
    app_method_names = set()
    if not isinstance(app_methods, list) or len(app_methods) == 0:
        problems.append("Contract missing required non-empty 'app_methods' list.")
    else:
        for idx, m in enumerate(app_methods):
            if not isinstance(m, dict) or not m.get("name"):
                problems.append(f"app_methods entry at index {idx} must be a dict with 'name'.")
            else:
                app_method_names.add(m.get("name"))

        # Required App methods
        required_app_methods = [
            "show_menu", "show_play_game", "show_view_score", "show_update_questions",
            "show_help", "start_play_game", "submit_answer", "toggle_pause",
            "end_game", "update_questions"
        ]
        for ram in required_app_methods:
            if ram not in app_method_names:
                problems.append(f"Contract missing required App method: '{ram}'")

    # 4. Validate states section against spec
    states = contract.get("states")
    spec_states = spec.get("diagrams", {}).get("StateDiagram", {}).get("states", [])
    if not isinstance(states, list):
        problems.append("Contract missing required 'states' list.")
    elif len(states) < len(spec_states):
        problems.append(
            f"Contract 'states' count ({len(states)}) is less than spec StateDiagram states count ({len(spec_states)})."
        )

    # 5. Validate transitions section against spec
    transitions = contract.get("transitions")
    spec_transitions = spec.get("diagrams", {}).get("StateDiagram", {}).get("transitions", [])
    if not isinstance(transitions, list):
        problems.append("Contract missing required 'transitions' list.")
    else:
        spec_triggers = []
        for t in spec_transitions:
            if ":" in t:
                trig = t.split(":")[-1].replace("()", "").strip()
                if trig:
                    spec_triggers.append(trig)

        contract_triggers = {
            str(t.get("trigger", "")).replace("()", "").strip().lower()
            for t in transitions if isinstance(t, dict)
        }
        for trig in spec_triggers:
            if trig.lower() not in contract_triggers:
                problems.append(f"Contract missing state transition trigger from spec: '{trig}'")

        # Step 2: Validate transition triggers map to callables
        app_callables = set(app_method_names) | entrypoint_names | {"create_app"}
        norm_app_callables = {re.sub(r'[^a-zA-Z0-9]', '', str(m)).lower() for m in app_callables}

        game_callables = set()
        for c in contract.get("classes", []):
            if isinstance(c, dict) and c.get("name") == "Game":
                for m in c.get("methods", []):
                    if isinstance(m, dict) and m.get("name"):
                        game_callables.add(m["name"])
        norm_game_callables = {re.sub(r'[^a-zA-Z0-9]', '', str(m)).lower() for m in game_callables}

        for t in transitions:
            if isinstance(t, dict):
                trig = t.get("trigger", "")
                method = t.get("method")
                has_app_method = False
                if method:
                    norm_method = re.sub(r'[^a-zA-Z0-9]', '', str(method)).lower()
                    if method in app_callables or norm_method in norm_app_callables:
                        has_app_method = True

                norm_trig = re.sub(r'[^a-zA-Z0-9]', '', str(trig)).lower()
                trigger_matches = (norm_trig in norm_app_callables) or (norm_trig in norm_game_callables)

                if not (has_app_method or trigger_matches):
                    problems.append(f"Transition {trig} has no callable method")

    # 6. Validate files list
    files = contract.get("files", [])
    if not isinstance(files, list) or len(files) == 0:
        problems.append("'files' must be a non-empty list.")
    else:
        file_paths = set()
        file_order_map = {}
        for idx, f in enumerate(files):
            if not isinstance(f, dict):
                problems.append(f"File entry at index {idx} must be a dict.")
                continue
            path = f.get("path")
            order = f.get("order")
            purpose = f.get("purpose")
            if not path or order is None or not purpose:
                problems.append(f"File entry at index {idx} missing 'path', 'order', or 'purpose'.")
                continue
            file_paths.add(path)
            file_order_map[path] = order

        # Check file dependency order: imported files must have lower order
        for f in files:
            if isinstance(f, dict):
                f_path = f.get("path")
                f_order = f.get("order", 0)
                imports = f.get("imports", [])
                for imp in imports:
                    if imp in file_order_map:
                        imp_order = file_order_map[imp]
                        if imp_order >= f_order:
                            problems.append(
                                f"File order violation: '{f_path}' (order {f_order}) imports '{imp}' "
                                f"(order {imp_order}) which is not strictly earlier."
                            )

    # 7. Validate classes against spec
    classes = contract.get("classes", [])
    contract_class_names = set()
    contract_method_names = set()

    for idx, c in enumerate(classes):
        if not isinstance(c, dict):
            problems.append(f"Class entry at index {idx} must be a dict.")
            continue
        cname = c.get("name")
        cfile = c.get("file")
        if not cname:
            problems.append(f"Class entry at index {idx} missing 'name'.")
            continue
        contract_class_names.add(cname)

        if not cfile:
            problems.append(f"Class '{cname}' has no 'file' assigned.")
        elif files and cfile not in file_paths:
            problems.append(f"Class '{cname}' assigned to undeclared file '{cfile}'.")

        # Validate methods
        methods = c.get("methods", [])
        for m in methods:
            if isinstance(m, dict):
                mname = m.get("name")
                if mname:
                    contract_method_names.add(mname)
                    contract_method_names.add(f"{cname}.{mname}")
                mkind = m.get("kind", "method")
                if mkind not in ("method", "property", "staticmethod"):
                    problems.append(f"Method '{mname}' in class '{cname}' has invalid kind '{mkind}'.")

    # Missing class check from spec
    spec_classes = spec.get("diagrams", {}).get("ClassDiagram", {}).get("classes", [])
    for sc in spec_classes:
        sc_name = sc.get("name")
        if sc_name and sc_name not in contract_class_names:
            problems.append(f"Missing required class from spec: '{sc_name}'")

    # 8. Validate smoke steps and literal args
    smoke_steps = contract.get("smoke_steps", [])
    allowed_smoke_calls = app_method_names | entrypoint_names | {"create_app"}
    identifier_pattern = re.compile(r'^(user|game|admin|questions)$', re.IGNORECASE)

    if not isinstance(smoke_steps, list) or len(smoke_steps) == 0:
        problems.append("'smoke_steps' must be a non-empty list.")
    else:
        for idx, step in enumerate(smoke_steps):
            if not isinstance(step, dict):
                problems.append(f"Smoke step at index {idx} must be a dict.")
                continue
            call = step.get("call")
            args = step.get("args")
            purp = step.get("purpose")
            if not call or args is None or not purp:
                problems.append(f"Smoke step at index {idx} missing 'call', 'args', or 'purpose'.")
                continue
            if not isinstance(args, list):
                problems.append(f"Smoke step '{call}' args must be a list.")
            else:
                for arg_idx, arg in enumerate(args):
                    if isinstance(arg, str) and identifier_pattern.match(arg.strip()):
                        problems.append(
                            f"Smoke step '{call}' arg #{arg_idx+1} is bare identifier '{arg}'; "
                            f"arguments must be primitive literals (e.g. [], 0, '') or zero arguments."
                        )

            # Check call target is declared in app_methods, entrypoints, or create_app
            base_call = call.split("(")[0].strip()
            if base_call not in allowed_smoke_calls and base_call not in contract_method_names:
                problems.append(f"Smoke step calls undeclared method: '{base_call}'")

    # 9. MISSING ADMIN SMOKE STEP validation
    uc_diag = spec.get("diagrams", {}).get("UseCaseDiagram", {})
    actors = [str(a).lower() for a in uc_diag.get("actors", [])]
    usecases = [str(u).lower() for u in uc_diag.get("usecases", [])]
    has_admin_actor = "admin" in actors
    has_update_uc = any("update" in u for u in usecases)

    if has_admin_actor or has_update_uc:
        admin_smoke_found = False
        for step in smoke_steps:
            if isinstance(step, dict):
                call_str = str(step.get("call", "")).lower()
                purp_str = str(step.get("purpose", "")).lower()
                if "admin" in call_str or "admin" in purp_str or "update" in call_str or "update" in purp_str:
                    admin_smoke_found = True
                    break
        if not admin_smoke_found:
            problems.append(
                "Missing Admin flow smoke step: spec defines Admin actor / Update Questions usecase, "
                "but no smoke step covers 'admin' or 'update'."
            )

    # 10. Specific attribute & method requirements for Game and Question classes
    camel_pattern = re.compile(r'^[a-z]+[A-Z]')
    for c in classes:
        if isinstance(c, dict):
            cname = c.get("name")
            # Check methods for snake_case
            for m in c.get("methods", []):
                if isinstance(m, dict):
                    mname = m.get("name", "")
                    if camel_pattern.match(mname):
                        problems.append(f"Method '{mname}' in class '{cname}' violates snake_case convention.")

            if cname == "Game":
                attrs = [a.get("name") if isinstance(a, dict) else str(a) for a in c.get("attributes", [])]
                for req_attr in ("id", "score", "state"):
                    if req_attr not in attrs:
                        problems.append(f"Class 'Game' missing required attribute '{req_attr}'.")
                g_methods = {m.get("name") for m in c.get("methods", []) if isinstance(m, dict)}
                for rgm in ("__init__", "play", "view_score", "pause", "resume", "game_over"):
                    if rgm not in g_methods:
                        problems.append(f"Class 'Game' missing required method '{rgm}'.")

            elif cname == "Question":
                attrs = [a.get("name") if isinstance(a, dict) else str(a) for a in c.get("attributes", [])]
                for req_attr in ("id", "prompt", "options", "answer_index"):
                    if req_attr not in attrs:
                        problems.append(f"Class 'Question' missing required attribute '{req_attr}'.")
                q_methods = {m.get("name") for m in c.get("methods", []) if isinstance(m, dict)}
                for rqm in ("__init__", "get_prompt", "get_options", "get_answer_index"):
                    if rqm not in q_methods:
                        problems.append(f"Class 'Question' missing required method '{rqm}'.")

    # 11. Ensure main.py is the LAST file in files list
    if files and isinstance(files, list):
        last_file = files[-1].get("path", "") if isinstance(files[-1], dict) else ""
        if not (last_file == "main.py" or last_file.endswith("/main.py") or last_file.endswith("\\main.py")):
            problems.append(f"The last file in 'files' must be 'main.py', but got '{last_file}'.")

    # 12. Ensure traceability covers all ClassDiagram classes and UseCaseDiagram use cases
    traceability = contract.get("traceability", [])
    if isinstance(traceability, list):
        trace_elems = {str(t.get("diagram_element", "")) for t in traceability if isinstance(t, dict)}
        for sc in spec_classes:
            sc_name = sc.get("name")
            if sc_name and not any(sc_name in te for te in trace_elems):
                problems.append(f"Traceability missing ClassDiagram class '{sc_name}'.")
        for uc in spec.get("diagrams", {}).get("UseCaseDiagram", {}).get("usecases", []):
            if not any(uc.lower() in te.lower() for te in trace_elems):
                problems.append(f"Traceability missing UseCaseDiagram usecase '{uc}'.")

    # 13. Ensure end_game is present in app_methods and smoke_steps (after toggle_pause, before show_view_score)
    if "end_game" not in app_method_names:
        problems.append("Contract missing required 'end_game' in app_methods.")

    has_end_game_smoke = False
    for step in smoke_steps:
        if isinstance(step, dict) and step.get("call") == "end_game":
            has_end_game_smoke = True
            break
    if not has_end_game_smoke:
        problems.append("Contract missing required 'end_game' smoke step.")

    smoke_calls = [s.get("call") for s in smoke_steps if isinstance(s, dict)]
    if "end_game" in smoke_calls and "toggle_pause" in smoke_calls:
        if smoke_calls.index("end_game") < smoke_calls.index("toggle_pause"):
            problems.append("'end_game' smoke step must be placed after 'toggle_pause'.")
    if "end_game" in smoke_calls and "show_view_score" in smoke_calls:
        if smoke_calls.index("end_game") > smoke_calls.index("show_view_score"):
            problems.append("'end_game' smoke step must be placed before 'show_view_score'.")

    # 14. Ensure gameOver transition maps to end_game
    for t in contract.get("transitions", []):
        if isinstance(t, dict) and t.get("trigger", "").lower() == "gameover":
            method = t.get("method", "") or t.get("trigger", "")
            if "end_game" not in method and "gameover" not in method.lower():
                problems.append("gameOver transition must map to 'end_game' method.")

    return problems


def generate_contract(client, spec, max_tokens=8192, runs_dir="runs"):
    """Generate, validate, and return architectural contract. Retries once on validation failure."""
    prompt = build_contract_prompt(spec)
    messages = [
        {"role": "system", "content": "You are a software architect producing complete, valid JSON implementation contracts."},
        {"role": "user", "content": prompt}
    ]

    # Attempt 1
    resp = client.chat(messages, json_mode=True, max_tokens=max_tokens, thinking=False)
    content = resp.get("content", "")

    try:
        contract = json.loads(content)
    except json.JSONDecodeError as e:
        contract = None
        problems = [f"Initial model response is not valid JSON: {str(e)}"]

    if contract is not None:
        contract["forbidden_names"] = compute_forbidden_names()
        problems = validate_contract(contract, spec)
        if not problems:
            return contract, resp

    # Retry ONCE with validation errors appended
    retry_prompt = (
        "The previously generated contract failed validation with the following problems:\n"
        + "\n".join(f"- {p}" for p in problems)
        + "\n\nPlease fix all issues and return the complete, corrected JSON contract matching the required schema."
    )
    messages.append({"role": "assistant", "content": content})
    messages.append({"role": "user", "content": retry_prompt})

    resp2 = client.chat(messages, json_mode=True, max_tokens=max_tokens, thinking=False)
    content2 = resp2.get("content", "")

    try:
        contract2 = json.loads(content2)
    except json.JSONDecodeError as e:
        contract2 = None
        problems2 = [f"Retry model response is not valid JSON: {str(e)}"]

    if contract2 is not None:
        contract2["forbidden_names"] = compute_forbidden_names()
        problems2 = validate_contract(contract2, spec)
        if not problems2:
            return contract2, resp2

    # Still invalid: persist bad contract and raise
    os.makedirs(runs_dir, exist_ok=True)
    ts = int(time.time())
    bad_contract_path = os.path.join(runs_dir, f"bad_contract_{ts}.json")
    with open(bad_contract_path, "w", encoding="utf-8") as f:
        f.write(content2 if content2 else content)

    raise ContractError(f"Contract validation failed after retry. Problems: {problems2}. Saved to {bad_contract_path}")
