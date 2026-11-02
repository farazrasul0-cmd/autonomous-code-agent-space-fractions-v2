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
        '  "entrypoints": [{"name": "launch", "signature": "launch() -> None", "purpose": "Start App"}],\n'
        '  "smoke_steps": [{"call": "launch", "args": [], "purpose": "Smoke test app"}],\n'
        '  "traceability": [{"diagram_element": "ClassDiagram.Calculator", "code_symbol": "Calculator"}]\n'
        '}'
    )

    prompt = f"""You are an expert software architect designing an implementation contract for a desktop application.

### DESIGN GUIDELINES & CONSTRAINTS:
1. Target Platform: Standalone desktop application on Windows using Python 3.12 and Tkinter.
2. Dependencies: Python Standard Library ONLY (e.g. tkinter, json, math, random, datetime, pathlib, unittest). No 3rd-party pip packages.
3. Architecture Fidelity: Retain every class name, attribute, and method signature specified in the architecture specification.
4. Method Kinds: Each method must have kind 'method', 'property', or 'staticmethod'.
5. File Dependencies: Define files in strictly topological dependency order (a file must only import files with lower order indices).
6. Coverage Mandate: Include every class from the class diagram and every usecase from the use case diagram. Every use case requires a designated callable entry point and at least one corresponding smoke step.
7. Administrative Flow: If the specification contains an Admin actor or Update Questions usecase, you MUST include a dedicated smoke step whose purpose or call name contains 'admin' or 'update'.

### REQUIRED JSON SCHEMA FORMAT:
{schema_example}

### ARCHITECTURE SPECIFICATION:
{json.dumps(architecture_summary, indent=2)}

Output ONLY the complete, valid JSON contract object matching the schema above."""

    # Sanity check: verify no game-specific brand names leaked into the prompt
    assert "Space Fractions" not in prompt, "Contract prompt must not contain game-specific name!"
    return prompt


def validate_contract(contract, spec):
    """Validate contract against schema rules, architectural spec completeness, and admin smoke step mandate."""
    problems = []

    if not isinstance(contract, dict):
        return ["Contract must be a JSON dictionary."]

    # 1. Top-level required keys
    required_keys = ["files", "classes", "entrypoints", "smoke_steps", "traceability"]
    for key in required_keys:
        if key not in contract:
            problems.append(f"Missing required top-level key: '{key}'")

    if problems:
        return problems

    # 2. Validate files list
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

    # 3. Validate classes against spec
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

    # 4. Validate entrypoints against spec usecases
    entrypoints = contract.get("entrypoints", [])
    entrypoint_names = set()
    entrypoint_text_corpus = ""

    for idx, ep in enumerate(entrypoints):
        if not isinstance(ep, dict):
            problems.append(f"Entrypoint at index {idx} must be a dict.")
            continue
        name = ep.get("name")
        sig = ep.get("signature")
        purp = ep.get("purpose", "")
        if not name or not sig:
            problems.append(f"Entrypoint at index {idx} missing 'name' or 'signature'.")
            continue
        entrypoint_names.add(name)
        entrypoint_text_corpus += f" {name} {purp}".lower()

    spec_usecases = spec.get("diagrams", {}).get("UseCaseDiagram", {}).get("usecases", [])
    for uc in spec_usecases:
        uc_clean = re.sub(r'[^a-zA-Z0-9]', '', uc).lower()
        # Check if use case words or clean token are covered in entrypoints
        tokens = [t.lower() for t in uc.split() if len(t) > 2]
        covered = (uc_clean in entrypoint_text_corpus.replace("_", "").replace(" ", "") or
                   all(t in entrypoint_text_corpus for t in tokens))
        if not covered:
            problems.append(f"Missing entrypoint covering spec usecase: '{uc}'")

    # 5. Validate smoke steps
    smoke_steps = contract.get("smoke_steps", [])
    all_callable_targets = entrypoint_names | contract_method_names
    # Add standalone function names if any
    for ep in entrypoint_names:
        all_callable_targets.add(ep)

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
            # Check call target is declared
            base_call = call.split("(")[0].strip()
            if base_call not in all_callable_targets:
                problems.append(f"Smoke step calls undeclared function or method: '{base_call}'")

    # 6. MISSING ADMIN SMOKE STEP validation
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
