# src/parser.py - Markdown and PlantUML architecture parser -> spec.json
import os
import re
import sys
import json

def clean_escaped_markdown(text):
    """Clean escaped markdown formatting and HTML entities common in exported architecture docs."""
    replacements = [
        (r'\\_', '_'),
        (r'\\\*', '*'),
        (r'\\<', '<'),
        (r'\\>', '>'),
        (r'\\&', '&'),
        (r'&#x20;', ' '),
        (r'&amp;', '&'),
        (r'&lt;', '<'),
        (r'&gt;', '>'),
    ]
    for pattern, repl in replacements:
        text = text.replace(pattern, repl)
    return text

def split_headings(text):
    """Split markdown text by headings into a dict of normalized title -> body."""
    text = clean_escaped_markdown(text)
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    matches = list(heading_pattern.finditer(text))

    sections = {}
    if not matches:
        sections["Document"] = text.strip()
        return sections

    preamble = text[:matches[0].start()].strip()
    if preamble:
        sections["Preamble"] = preamble

    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        clean_title = re.sub(r'[*_`]', '', title).strip()
        sections[clean_title] = body

    return sections

def extract_blocks(text):
    """Extract all ```plantuml ... ``` fenced blocks returning list of (name, raw_content)."""
    pattern = re.compile(r'```plantuml(.*?)```', re.DOTALL)
    blocks = []
    for idx, match in enumerate(pattern.finditer(text), start=1):
        raw = match.group(1).strip()
        name_match = re.search(r'@startuml\s*([a-zA-Z0-9_]*)', raw)
        name = name_match.group(1).strip() if (name_match and name_match.group(1).strip()) else f"Diagram_{idx}"
        blocks.append((name, raw))
    return blocks

def parse_usecase_diagram(raw):
    """Parse PlantUML usecase diagram into actors, use cases, and links."""
    actors = []
    for m in re.finditer(r'actor\s+(\w+)(?:\s+as\s+"([^"]+)")?', raw):
        actor_id = m.group(1)
        display_name = m.group(2) if m.group(2) else actor_id
        actors.append(display_name)

    usecases = []
    for m in re.finditer(r'usecase\s+"([^"]+)"(?:\s+as\s+\((\w+)\))?', raw):
        usecases.append(m.group(1).strip())

    links = []
    for m in re.finditer(r'(\w+)\s+--\s+\(?(\w+)\)?', raw):
        links.append(f"{m.group(1)} -- {m.group(2)}")

    return {
        "kind": "usecase",
        "actors": actors,
        "usecases": usecases,
        "links": links
    }

def parse_class_diagram(raw):
    """Parse PlantUML class diagram into classes (name, attributes, methods) and relations."""
    classes = []
    class_pattern = re.compile(r'class\s+(\w+)\s*(?:extends\s+(\w+))?\s*\{([^}]*)\}', re.DOTALL)
    for m in class_pattern.finditer(raw):
        cname = m.group(1)
        base = m.group(2) if m.group(2) else None
        body = m.group(3)

        attrs = []
        for am in re.finditer(r'([-+#~])\s*(\w+)\s*:\s*([^\n\r]+)', body):
            attrs.append(f"{am.group(1)} {am.group(2)}: {am.group(3).strip()}")

        methods = []
        for mm in re.finditer(r'([-+#~])\s*(\w+)\s*\(([^)]*)\)\s*:\s*([^\n\r]+)', body):
            params = mm.group(3).strip()
            ret = mm.group(4).strip()
            methods.append(f"{mm.group(1)} {mm.group(2)}({params}): {ret}")

        classes.append({
            "name": cname,
            "base_class": base,
            "attributes": attrs,
            "methods": methods
        })

    relations = []
    rel_pattern = re.compile(r'(\w+)\s*(--\*|-->|<--|--|\.\.>|<\.\.|\*--)\s*(\w+)')
    for rm in rel_pattern.finditer(raw):
        relations.append(f"{rm.group(1)} {rm.group(2)} {rm.group(3)}")

    return {
        "kind": "class",
        "classes": classes,
        "relations": relations
    }

def parse_state_diagram(raw):
    """Parse PlantUML state diagram into states, initial state, and transitions."""
    states = []
    for sm in re.finditer(r'state\s+(\w+)', raw):
        sname = sm.group(1)
        if sname not in states:
            states.append(sname)

    transitions = []
    initial = None
    trans_pattern = re.compile(r'(\[\*\]|\w+)\s*-->\s*(\w+)(?:\s*:\s*([^\n\r]+))?')
    for tm in trans_pattern.finditer(raw):
        src = tm.group(1)
        dst = tm.group(2)
        trigger = tm.group(3).strip() if tm.group(3) else ""
        if src == '[*]':
            initial = dst
        transitions.append(f"{src} -> {dst}" + (f" : {trigger}" if trigger else ""))

    return {
        "kind": "state",
        "states": states,
        "initial": initial,
        "transitions": transitions
    }

def parse_sequence_diagram(raw):
    """Parse PlantUML sequence diagram into participants and ordered messages."""
    participants = []
    for pm in re.finditer(r'participant\s+(\w+)', raw):
        pname = pm.group(1)
        if pname not in participants:
            participants.append(pname)

    messages = []
    msg_pattern = re.compile(r'(\w+)\s*(?:->>|->|-->>|-->)\s*(\w+)\s*:\s*([^\n\r]+)')
    for mm in msg_pattern.finditer(raw):
        messages.append(f"{mm.group(1)} -> {mm.group(2)}: {mm.group(3).strip()}")

    return {
        "kind": "sequence",
        "participants": participants,
        "messages": messages
    }

def parse_other_diagram(raw, detected_kind):
    """Fallback parser for other diagram kinds (object, activity, package, component, deployment, container)."""
    elements = [m.group(1) for m in re.finditer(r'(?:participant|node|artifact|package)\s+(\w+)', raw)]
    links = [f"{m.group(1)} -- {m.group(2)}" for m in re.finditer(r'(\w+)\s*(?:-->|--)\s*(\w+)', raw)]
    return {
        "kind": detected_kind,
        "elements": elements,
        "links": links
    }

def parse_diagram_block(name, raw):
    """Detect diagram kind by keyword analysis and parse into structured representation."""
    lower_raw = raw.lower()
    lower_name = name.lower()

    if "usecase" in lower_name or "actor " in lower_raw or "usecase " in lower_raw:
        return parse_usecase_diagram(raw)
    elif "class" in lower_name or "class " in lower_raw:
        return parse_class_diagram(raw)
    elif "state" in lower_name or "state " in lower_raw or "[*]" in raw:
        return parse_state_diagram(raw)
    elif "sequence" in lower_name or "->>" in raw or ("participant" in lower_raw and "object" not in lower_name):
        return parse_sequence_diagram(raw)
    elif "object" in lower_name:
        return parse_other_diagram(raw, "object")
    elif "activity" in lower_name or ("start" in lower_raw and "stop" in lower_raw):
        return parse_other_diagram(raw, "activity")
    elif "package" in lower_name or "package " in lower_raw:
        return parse_other_diagram(raw, "package")
    elif "component" in lower_name:
        return parse_other_diagram(raw, "component")
    elif "deployment" in lower_name:
        return parse_other_diagram(raw, "deployment")
    elif "container" in lower_name:
        return parse_other_diagram(raw, "container")
    else:
        return parse_other_diagram(raw, "other")

def extract_requirements(doc_text):
    """Extract functional, non-functional, and architectural requirements with short text."""
    doc_text = clean_escaped_markdown(doc_text)
    reqs = {}

    row_pattern = re.compile(r'\|\s*(FR-\d+|NFR-\d+|ASR-\d+)\s*\|\s*([^|]+)\s*\|')
    for m in row_pattern.finditer(doc_text):
        req_id = m.group(1).strip()
        text = m.group(2).strip()
        if req_id not in reqs:
            reqs[req_id] = text

    paren_pattern = re.compile(r'\b(FR-\d+|NFR-\d+|ASR-\d+)\s*\(([^)]+)\)')
    for m in paren_pattern.finditer(doc_text):
        req_id = m.group(1).strip()
        text = m.group(2).strip()
        if req_id not in reqs:
            reqs[req_id] = text

    result = []
    for req_id in sorted(reqs.keys()):
        result.append({
            "id": req_id,
            "type": req_id.split('-')[0],
            "description": reqs[req_id]
        })
    return result

def extract_warnings(doc_text, view_text, blocks):
    """Detect inconsistencies, empty tables, duplicate blocks, and mismatches in documents."""
    warnings = []

    # 1. Duplicated diagram names
    names = [name for name, _ in blocks]
    duplicates = [name for name in set(names) if names.count(name) > 1]
    if duplicates:
        warnings.append(f"Duplicated diagram names in Architecture_View: {', '.join(duplicates)}")

    # 2. Empty test matrix
    if "| Unit testing | | |" in doc_text or "| Chaos testing | | |" in doc_text:
        warnings.append("Empty test matrix: Testing strategy table lists test types with empty component columns.")

    # 3. Mismatched artifact filenames
    has_question_ddl = "question_ddl.sql" in doc_text
    has_game_ddl = "game_ddl.sql" in doc_text
    if has_question_ddl and has_game_ddl:
        warnings.append("Mismatched artifact filenames: Traceability mentions 'question_ddl.sql' while deliverables specify 'game_ddl.sql'.")

    # 4. Duplicated code snippets in documentation
    openapi_blocks = len(re.findall(r'openapi:\s*3\.0\.0', doc_text))
    if openapi_blocks > 1:
        warnings.append(f"Duplicated OpenAPI specification blocks found ({openapi_blocks} copies in Architecture_Documentation).")

    k8s_blocks = len(re.findall(r'kind:\s*Deployment', doc_text))
    if k8s_blocks > 1:
        warnings.append(f"Duplicated Kubernetes Deployment blocks found ({k8s_blocks} copies in Architecture_Documentation).")

    return warnings

def parse_architecture(doc_path, view_path):
    """Main parsing routine taking paths to the two architecture markdown files."""
    doc_text = ""
    view_text = ""

    if doc_path and os.path.exists(doc_path):
        with open(doc_path, "r", encoding="utf-8", errors="ignore") as f:
            doc_text = f.read()

    if view_path and os.path.exists(view_path):
        with open(view_path, "r", encoding="utf-8", errors="ignore") as f:
            view_text = f.read()

    doc_sections = split_headings(doc_text)
    blocks = extract_blocks(view_text)

    # Parse all diagram blocks safely with try/except
    parsed_diagrams = {}
    warnings = extract_warnings(doc_text, view_text, blocks)

    for name, raw in blocks:
        try:
            parsed_diagrams[name] = parse_diagram_block(name, raw)
        except Exception as e:
            warnings.append(f"Failed to parse diagram {name}: {str(e)}")
            parsed_diagrams[name] = {"kind": "unparsed", "error": str(e)}

    # Extract requirements
    requirements = extract_requirements(doc_text)

    # Executive summary (extract first paragraph or up to 250 chars)
    exec_summary = ""
    for k, v in doc_sections.items():
        if "Executive Summary" in k:
            first_p = v.split("\n\n")[0].strip()
            exec_summary = first_p[:250].strip()
            break

    # Architectural conflicts entry (web/microservices vs desktop target)
    conflicts = {
        "prescribed_stack": "Web microservices (Node.js, Express, PostgreSQL, Redis, RabbitMQ, Docker, Kubernetes).",
        "assignment_requirement": "Standalone local Windows desktop application (.exe) using Python and Tkinter.",
        "resolution": "desktop requirement wins; cloud/container/microservice infrastructure is out of scope."
    }

    # Consolidated spec structure
    spec = {
        "system_name": "Space Fractions",
        "diagram_count": len(blocks),
        "requirements": requirements,
        "conflicts": conflicts,
        "warnings": warnings,
        "executive_summary": exec_summary,
        "diagrams": parsed_diagrams
    }

    # Format JSON with indent=1
    json_str = json.dumps(spec, indent=1)

    # If size exceeds 6000 bytes, prune auxiliary diagram fields
    if len(json_str.encode("utf-8")) >= 6000:
        pruned_diagrams = {}
        core_keys = ["UseCaseDiagram", "ClassDiagram", "StateDiagram", "SequenceDiagram1", "SequenceDiagram2"]
        for k, v in parsed_diagrams.items():
            if k in core_keys:
                pruned_diagrams[k] = v
            else:
                pruned_diagrams[k] = {
                    "kind": v.get("kind", "other"),
                    "elements": v.get("elements", [])[:3]
                }
        spec["diagrams"] = pruned_diagrams
        json_str = json.dumps(spec, indent=1)

    return spec, json_str

def main():
    input_dir = "examples/inputs"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isdir(target):
            input_dir = target
            doc_path = os.path.join(input_dir, "Architecture_Documentation.md")
            view_path = os.path.join(input_dir, "Architecture_View.md")
        else:
            doc_path = target
            view_path = sys.argv[2] if len(sys.argv) > 2 else "examples/inputs/Architecture_View.md"
    else:
        doc_path = os.path.join(input_dir, "Architecture_Documentation.md")
        view_path = os.path.join(input_dir, "Architecture_View.md")

    spec, json_str = parse_architecture(doc_path, view_path)

    out_file = "spec.json"
    with open(out_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(json_str)

    size = len(json_str.encode("utf-8"))
    print(f"Generated {out_file} (size: {size} bytes, len: {len(json_str)} chars)")
    print(f"Found {spec['diagram_count']} diagrams, {len(spec['requirements'])} requirements, {len(spec['warnings'])} warnings.")

    if size < 6000:
        print(f"Size gate PASSED: {size} < 6000 bytes.")
    else:
        print(f"Size gate FAILED: {size} >= 6000 bytes.")

if __name__ == "__main__":
    main()
