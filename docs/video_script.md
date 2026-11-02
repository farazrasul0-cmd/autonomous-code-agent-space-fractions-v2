# Video Demonstration Script: DeepSeek Code Agent

**Project**: DeepSeek Code Agent (Autonomous Code Synthesis & Multi-Turn Self-Repair)  
**Target Audience**: Professor Liang / Evaluation Review Committee  
**Total Target Duration**: ~4 minutes 30 seconds  

---

## Breakdown & Timestamps

### 0:00 – 0:30: Introduction & High-Level Pitch
- **Visual**: Camera or screen view showing desktop and repo folder.
- **Narrator**:
  > "This is the DeepSeek Code Agent. It reads software architecture documentation and UML diagrams, writes a formal contract, implements source code modules, verifies them via AST static analysis and headless UI walkthroughs, and autonomously repairs its own bugs. Let's see it work."

### 0:30 – 1:00: Architecture & Claude-Code Reference Mapping
- **Visual**: Show GitHub repository `README.md` and scroll to the **Reference-Repo Mapping Table**.
- **Narrator**:
  > "Following the principles of the open-source Claude-Code architecture, the agent adapts core agentic patterns to a deterministic desktop pipeline:
  > - **Agent Tool Interface**: Implements `read_file`, `write_file`, `list_dir`, and `run_checks` with strict sandbox path containment.
  > - **Observation Reinjection**: Diagnostic AST and runtime failures are reinjected into the model context to drive an autonomous repair loop.
  > - **Context Management via AST Signature Ledger**: Only signatures of previously generated files are passed forward, minimizing prompt tokens by ~70% and preventing context window bloat.
  > - **Multi-Stage Verification (V1–V8)**: Eight layered checks catch compilation, cross-file API mismatches, Tkinter method collisions, unapproved dependencies, unit test errors, and UI screen walkthrough regressions."

### 1:00 – 2:30: Live Demonstration (Autonomous Synthesis Pipeline)
- **Visual**: Double-click `dist\CodeAgent\CodeAgent.exe`. The Tkinter GUI opens.
- **Actions**:
  1. Show API Key field (masked), click "Test Key" to show successful endpoint ping.
  2. Point to the pre-populated Architecture Documentation and Architecture View paths (`examples/inputs/Architecture_Documentation.md` and `examples/inputs/Architecture_View.md`).
  3. Click **"Start Synthesis"**.
- **Narrator**:
  > "Notice the five stage cards updating in real time:
  > 1. **Parse**: Extracts the requirements, class diagrams, use cases, and states into `spec.json`.
  > 2. **Contract**: DeepSeek synthesizes `contract.json` defining exact classes, attributes, methods, topological file orders, and smoke test sequences.
  > 3. **Implement**: Domain modules (`models.py`, `app.py`, `main.py`, and `test_game.py`) are synthesized incrementally using the AST signature ledger.
  > 4. **Verify**: The V1 through V8 verification suite runs.
  > 5. **Repair**: If any check fails, the repair loop engages autonomously.
  > Notice the live budget meter tracking our spend in fractions of a cent, well within our conservative budget ceiling."

### 2:30 – 3:00: Inspecting Generated Run Report & Traceability
- **Visual**: Open `run_report.md` in the output folder.
- **Narrator**:
  > "Here is the synthesized `run_report.md`. We can inspect the verification matrix showing all V1 to V8 checks, the repair log, and the AST traceability matrix linking each UML diagram element to exact source lines in the generated code."

### 3:00 – 4:00: Game Launch & Independent Process Verification
- **Visual**: Click **"Launch Game"** button on the CodeAgent GUI.
- **Actions**:
  1. Play the Space Fractions game window.
  2. Answer a fraction question correctly, demonstrate score increment.
  3. Answer incorrectly to show error handling.
  4. Demonstrate pause and resume.
  5. Open the Admin screen and update question parameters.
  6. Close the main CodeAgent agent GUI, showing that the Space Fractions game remains running completely independently without crashing.
- **Narrator**:
  > "The game runs in a detached independent process. Even when we close the parent CodeAgent window, the game continues seamlessly."

### 4:00 – 4:30: 3+1 Multi-Run Evaluation & Conclusion
- **Visual**: Open `examples/runs/results.md`.
- **Narrator**:
  > "To prove generality and eliminate hardcoding, we conducted a 3+1 multi-run evaluation: 3 runs on Space Fractions, and 1 run on a completely distinct Smart To-Do List application.
  > The agent parsed the To-Do architecture, synthesized a completely independent domain model and GUI, repaired its own unit tests at Round 2, and achieved all 8 verification checks passing.
  > Authoritative project spend verified on the DeepSeek Dashboard was ¥1.91 CNY (~$0.26 USD), well within the $1.00 cap. Thank you."
