# src/verify.py - Static and dynamic verification checks V1 through V8
import os
import re
import sys
import ast
import json
import inspect
import tkinter
import py_compile
import subprocess
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.harness import run_harness


def check_v1_file_presence(run_dir: str | Path, contract: dict) -> list[dict]:
    """V1: Check every file declared in contract['files'] exists in run_dir and is non-empty."""
    run_dir = Path(run_dir)
    errors = []
    files = contract.get("files", [])

    for f in files:
        rel_path = f.get("path")
        if not rel_path:
            continue
        p = run_dir / rel_path
        if not p.exists():
            errors.append({
                "check": "V1",
                "file": rel_path,
                "line": 0,
                "message": f"Required contract file '{rel_path}' does not exist in run directory"
            })
        elif p.stat().st_size == 0:
            errors.append({
                "check": "V1",
                "file": rel_path,
                "line": 0,
                "message": f"Contract file '{rel_path}' is empty (0 bytes)"
            })

    return errors


def check_v2_compilation(run_dir: str | Path) -> list[dict]:
    """V2: py_compile each .py file in run_dir and its subdirectories."""
    run_dir = Path(run_dir)
    errors = []

    for py_file in run_dir.rglob("*.py"):
        rel_path = str(py_file.relative_to(run_dir)).replace("\\", "/")
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append({
                "check": "V2",
                "file": rel_path,
                "line": e.lineno or 0,
                "message": f"Compilation error: {e.msg}"
            })

    return errors


def check_v6_import_boundaries(run_dir: str | Path) -> list[dict]:
    """V6: AST-walk imports; allow only standard library + local project modules."""
    run_dir = Path(run_dir)
    errors = []

    # Standard library module names in Python 3.12
    stdlib_names = set(sys.stdlib_module_names) | {"tkinter"}

    # Local modules in run_dir
    local_names = set()
    for py_file in run_dir.rglob("*.py"):
        local_names.add(py_file.stem)
        # Also relative path without .py
        rel_stem = str(py_file.relative_to(run_dir).with_suffix("")).replace("\\", ".").replace("/", ".")
        local_names.add(rel_stem)
        local_names.add(rel_stem.split(".")[0])

    for py_file in run_dir.rglob("*.py"):
        rel_path = str(py_file.relative_to(run_dir)).replace("\\", "/")
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod not in stdlib_names and root_mod not in local_names:
                        errors.append({
                            "check": "V6",
                            "file": rel_path,
                            "line": node.lineno,
                            "message": f"Disallowed external import '{alias.name}'"
                        })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod not in stdlib_names and root_mod not in local_names:
                        errors.append({
                            "check": "V6",
                            "file": rel_path,
                            "line": node.lineno,
                            "message": f"Disallowed external import '{node.module}'"
                        })

    return errors


def check_v3_contract_conformance(run_dir: str | Path, contract: dict) -> list[dict]:
    """V3: Contract conformance check via AST.

    Tolerates name-mangled private attributes (__attr counts for attr) and extra attributes.
    """
    run_dir = Path(run_dir)
    errors = []

    classes_by_file = {}
    for c in contract.get("classes", []):
        f = c.get("file")
        if f:
            classes_by_file.setdefault(f, []).append(c)

    for rel_path, declared_classes in classes_by_file.items():
        file_path = run_dir / rel_path
        if not file_path.exists():
            continue

        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except Exception as e:
            errors.append({
                "check": "V3",
                "file": rel_path,
                "line": 0,
                "message": f"Could not parse AST for contract conformance: {e}"
            })
            continue

        ast_classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}

        for c in declared_classes:
            cname = c["name"]
            if cname not in ast_classes:
                errors.append({
                    "check": "V3",
                    "file": rel_path,
                    "line": 0,
                    "message": f"Class '{cname}' declared in contract not found in {rel_path}"
                })
                continue

            c_node = ast_classes[cname]

            # 1. Base class check
            if c.get("base"):
                expected_base = c["base"]
                actual_bases = [ast.unparse(b) for b in c_node.bases]
                if not any(expected_base in b for b in actual_bases):
                    errors.append({
                        "check": "V3",
                        "file": rel_path,
                        "line": c_node.lineno,
                        "message": f"Class '{cname}' base mismatch: expected {expected_base}, got {actual_bases}"
                    })

            # 2. Attributes check: gather all self.<attr> assignments in __init__ and properties in class
            init_func = next((n for n in c_node.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
            assigned_attrs = set()
            if init_func:
                for node in ast.walk(init_func):
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                                assigned_attrs.add(t.attr)
                    elif isinstance(node, ast.AnnAssign):
                        t = node.target
                        if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                            assigned_attrs.add(t.attr)

            # Property methods in class
            property_names = {
                n.name for n in c_node.body
                if isinstance(n, ast.FunctionDef) and any(isinstance(d, ast.Name) and d.id == "property" for d in n.decorator_list)
            }

            for a in c.get("attributes", []):
                aname = a["name"] if isinstance(a, dict) else a
                clean_name = aname.lstrip("_")
                # Tolerance rule: self.name, self._name, self.__name, or @property def <name> present in class body
                matched = (
                    any(
                        attr == aname or attr == f"_{clean_name}" or attr == f"__{clean_name}" or attr.lstrip("_") == clean_name
                        for attr in assigned_attrs
                    )
                    or aname in property_names
                    or clean_name in property_names
                )
                if not matched:
                    errors.append({
                        "check": "V3",
                        "file": rel_path,
                        "line": c_node.lineno,
                        "message": f"Attribute '{aname}' of class '{cname}' is not assigned in __init__ or defined as @property"
                    })

            # 3. Methods check
            ast_methods = {n.name: n for n in c_node.body if isinstance(n, ast.FunctionDef)}
            for m in c.get("methods", []):
                mname = m["name"] if isinstance(m, dict) else m
                if mname not in ast_methods:
                    errors.append({
                        "check": "V3",
                        "file": rel_path,
                        "line": c_node.lineno,
                        "message": f"Method '{mname}' of class '{cname}' declared in contract is missing"
                    })
                    continue

                m_node = ast_methods[mname]

                # Param count check
                if isinstance(m, dict) and "params" in m:
                    expected_params = m["params"]
                    actual_params = [arg.arg for arg in m_node.args.args]
                    if len(actual_params) != len(expected_params):
                        errors.append({
                            "check": "V3",
                            "file": rel_path,
                            "line": m_node.lineno,
                            "message": f"Method '{cname}.{mname}' parameter count mismatch: expected {len(expected_params)} ({expected_params}), got {len(actual_params)} ({actual_params})"
                        })

                # Property check
                if isinstance(m, dict) and m.get("kind") == "property":
                    is_prop = any((isinstance(d, ast.Name) and d.id == "property") for d in m_node.decorator_list)
                    if not is_prop:
                        errors.append({
                            "check": "V3",
                            "file": rel_path,
                            "line": m_node.lineno,
                            "message": f"Method '{cname}.{mname}' must be declared as @property"
                        })

                # Staticmethod check
                if isinstance(m, dict) and m.get("kind") == "staticmethod":
                    is_static = any((isinstance(d, ast.Name) and d.id == "staticmethod") for d in m_node.decorator_list)
                    if not is_static:
                        errors.append({
                            "check": "V3",
                            "file": rel_path,
                            "line": m_node.lineno,
                            "message": f"Method '{cname}.{mname}' must be declared as @staticmethod"
                        })

    return errors


def check_v4_call_resolution(run_dir: str | Path) -> list[dict]:
    """V4: Static cross-file call resolution and owner validation.

    Checks:
    - self.attr.method() where attr is assigned to Class: verify method exists on Class.
    - self.attr.method() where attr was NEVER assigned in class: flag unassigned owner (bug3).
    - self.attr() or self.x.attr() where attr is a non-callable property/attribute: flag (bug2).
    - Unresolved receiver: SKIP silently (no noisy false positives).
    """
    run_dir = Path(run_dir)
    errors = []

    # 1. Build symbol table: class_name -> {methods, properties, attrs}
    symbol_table = {}
    ast_trees = {}

    for py_file in run_dir.rglob("*.py"):
        rel_path = str(py_file.relative_to(run_dir)).replace("\\", "/")
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            ast_trees[rel_path] = tree
        except Exception:
            continue

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cname = node.name
                methods = set()
                properties = set()
                attrs = set()

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        is_prop = any((isinstance(d, ast.Name) and d.id == "property") for d in item.decorator_list)
                        if is_prop:
                            properties.add(item.name)
                        else:
                            methods.add(item.name)

                        # Collect self.x assignments
                        for sub in ast.walk(item):
                            if isinstance(sub, ast.Assign):
                                for target in sub.targets:
                                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                        attrs.add(target.attr)
                            elif isinstance(sub, ast.AnnAssign):
                                target = sub.target
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                    attrs.add(target.attr)

                symbol_table[cname] = {
                    "methods": methods,
                    "properties": properties,
                    "attrs": attrs,
                    "file": rel_path
                }

    # 2. Scan class definitions for call sites
    for rel_path, tree in ast_trees.items():
        for class_node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            enclosing_class = class_node.name

            # Map self.x to ClassName assigned in __init__ or class methods
            assigned_owners = {}
            all_self_assigned = set()

            for item in class_node.body:
                if isinstance(item, ast.FunctionDef):
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                    all_self_assigned.add(target.attr)
                                    # If assigning a constructor call e.g. self.engine = Engine()
                                    if isinstance(stmt.value, ast.Call):
                                        if isinstance(stmt.value.func, ast.Name):
                                            assigned_owners[target.attr] = stmt.value.func.id
                        elif isinstance(stmt, ast.AnnAssign):
                            target = stmt.target
                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                all_self_assigned.add(target.attr)
                                # If assigning a constructor call e.g. self.engine: Engine = Engine()
                                if stmt.value and isinstance(stmt.value, ast.Call):
                                    if isinstance(stmt.value.func, ast.Name):
                                        assigned_owners[target.attr] = stmt.value.func.id

            # Scan method calls
            for item in class_node.body:
                if isinstance(item, ast.FunctionDef):
                    for call_node in ast.walk(item):
                        if not isinstance(call_node, ast.Call):
                            continue

                        # Case 1: self.q.prompt() or self.engine.start()
                        # call_node.func is ast.Attribute
                        func_expr = call_node.func
                        if isinstance(func_expr, ast.Attribute):
                            called_name = func_expr.attr
                            receiver = func_expr.value

                            # Subcase 1a: receiver is self.attr (e.g. self.engine.start())
                            if (
                                isinstance(receiver, ast.Attribute)
                                and isinstance(receiver.value, ast.Name)
                                and receiver.value.id == "self"
                            ):
                                attr_name = receiver.attr

                                # Bug 3 check: self.attr was NEVER assigned anywhere in class
                                if attr_name not in all_self_assigned:
                                    errors.append({
                                        "check": "V4",
                                        "file": rel_path,
                                        "line": call_node.lineno,
                                        "message": f"Attribute 'self.{attr_name}' called with method '{called_name}' was never assigned in class '{enclosing_class}'"
                                    })
                                    continue

                                # Bug 1 & Bug 2 check: resolve class of self.attr
                                target_class = assigned_owners.get(attr_name)
                                if target_class:
                                    if target_class == "object":
                                        # object() has no user-defined methods
                                        errors.append({
                                            "check": "V4",
                                            "file": rel_path,
                                            "line": call_node.lineno,
                                            "message": f"Method '{called_name}' called on object of type 'object' with no such method"
                                        })
                                    elif target_class in symbol_table:
                                        cls_info = symbol_table[target_class]
                                        # Bug 2 check: called_name is an attribute or property, not a method
                                        if called_name in cls_info["properties"] or (called_name in cls_info["attrs"] and called_name not in cls_info["methods"]):
                                            errors.append({
                                                "check": "V4",
                                                "file": rel_path,
                                                "line": call_node.lineno,
                                                "message": f"Attribute or property '{called_name}' on class '{target_class}' called as a method"
                                            })
                                        elif called_name not in cls_info["methods"]:
                                            # Bug 1 check: method does not exist on class
                                            errors.append({
                                                "check": "V4",
                                                "file": rel_path,
                                                "line": call_node.lineno,
                                                "message": f"Method '{called_name}' does not exist on class '{target_class}'"
                                            })
                                # If target_class is unresolvable: SKIP silently per directive

                            # Subcase 1b: receiver is self (e.g. self.prompt())
                            elif isinstance(receiver, ast.Name) and receiver.id == "self":
                                if enclosing_class in symbol_table:
                                    cls_info = symbol_table[enclosing_class]
                                    if called_name in cls_info["properties"] or (called_name in cls_info["attrs"] and called_name not in cls_info["methods"]):
                                        errors.append({
                                            "check": "V4",
                                            "file": rel_path,
                                            "line": call_node.lineno,
                                            "message": f"Attribute or property 'self.{called_name}' called as a method"
                                        })

    return errors


def check_v5_tk_collisions(run_dir: str | Path) -> list[dict]:
    """V5: Check method name collisions with Tkinter widgets in GUI subclasses."""
    run_dir = Path(run_dir)
    errors = []
    tk_misc_names = set(dir(tkinter.Misc))

    tk_bases = {"Frame", "Tk", "Toplevel", "Widget", "Misc", "Canvas", "Label", "Button", "Entry"}

    for py_file in run_dir.rglob("*.py"):
        rel_path = str(py_file.relative_to(run_dir)).replace("\\", "/")
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception:
            continue

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # Check if inherits from a Tkinter widget
                is_tk_subclass = False
                for b in node.bases:
                    base_str = ast.unparse(b)
                    if any(t in base_str for t in tk_bases):
                        is_tk_subclass = True
                        break

                if is_tk_subclass:
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            mname = item.name
                            if not mname.startswith("_") and mname in tk_misc_names:
                                errors.append({
                                    "check": "V5",
                                    "file": rel_path,
                                    "line": item.lineno,
                                    "message": f"Method '{mname}' in class '{node.name}' collides with Tkinter widget method"
                                })

    return errors


def check_v7_test_execution(run_dir: str | Path, timeout: int = 60) -> list[dict]:
    """V7: Run unit tests via unittest discover and return structured failure reports."""
    run_dir = Path(run_dir).resolve()
    tests_dir = run_dir / "tests"
    if not tests_dir.exists():
        return []

    # Ensure tests/__init__.py exists so unittest discover can import start_dir cleanly
    init_file = tests_dir / "__init__.py"
    created_temp_init = False
    if not init_file.exists():
        try:
            init_file.touch()
            created_temp_init = True
        except Exception:
            pass

    cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-t", str(run_dir)]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(run_dir),
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return [{
            "check": "V7",
            "file": "tests",
            "line": 0,
            "message": f"Unit test suite timed out after {timeout} seconds"
        }]
    finally:
        if created_temp_init and init_file.exists():
            try:
                init_file.unlink()
            except Exception:
                pass

    if proc.returncode == 0:
        return []

    # Parse failure details
    stderr = proc.stderr or proc.stdout
    errors = [{
        "check": "V7",
        "file": "tests",
        "line": 0,
        "message": f"Unit tests failed (exit code {proc.returncode}):\n{stderr[:500]}"
    }]
    return errors


def check_v8_harness(run_dir: str | Path, contract: dict, timeout: int = 35) -> list[dict]:
    """V8: Execute dynamic UI smoke walkthrough using harness subprocess with watchdog."""
    result = run_harness(run_dir=run_dir, contract=contract, timeout=timeout)
    if result.get("status") in ("pass", "skipped"):
        return []

    return [{
        "check": "V8",
        "file": "harness",
        "line": 0,
        "message": f"UI harness failed: {result.get('error', 'Unknown harness error')}"
    }]


def run_all_checks(run_dir: str | Path, contract: dict, skip_harness: bool = False) -> dict:
    """Run all verification checks V1 through V8 on a generated project directory."""
    results = {
        "V1": check_v1_file_presence(run_dir, contract),
        "V2": check_v2_compilation(run_dir),
        "V3": check_v3_contract_conformance(run_dir, contract),
        "V4": check_v4_call_resolution(run_dir),
        "V5": check_v5_tk_collisions(run_dir),
        "V6": check_v6_import_boundaries(run_dir),
        "V7": check_v7_test_execution(run_dir),
        "V8": [] if skip_harness else check_v8_harness(run_dir, contract)
    }

    all_errors = []
    for check_id, err_list in results.items():
        all_errors.extend(err_list)

    return {
        "all_passed": len(all_errors) == 0,
        "total_errors": len(all_errors),
        "checks": results,
        "errors": all_errors
    }
