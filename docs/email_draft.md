# Email Draft to Professor Liang

**Subject**: Task 1 Submission - DeepSeek Code Agent - Faraz (Sichuan University)

---

Dear Professor Liang,

Thank you for the opportunity to take the evaluation. I have completed the implementation of the simplified Code Agent based on the Claude-Code mechanisms.

What changed in the architecture: 
1. Contract-First Generation: The agent parses the UML docs and writes a strict contract before a single line of app code is generated.
2. Verification & Repair Loop: It uses AST static analysis to check for cross-file API mismatches (your bug examples), runs unit tests, and performs a headless UI walkthrough to catch runtime crashes, autonomously repairing them.
3. Generality: To prove it is not hardcoded, I evaluated it on the Space Fractions input and a completely different To-Do list input. Space Fractions: 5 runs passed (after autonomous repair). Smart To-Do List: 1 CLI run passed, 1 GUI Sandbox run failed.

Evaluation Results & Cost:
- Pass/Fail Status: Space Fractions: 5 runs passed (after autonomous repair). Smart To-Do List: 1 CLI run passed, 1 GUI Sandbox run failed.
- Total Spend: ~$0.26 USD (¥1.91 CNY verified directly on the DeepSeek Dashboard, covering all development, probing, and evaluation runs—well under the $1.00 limit).
- Raw logs and evaluation tables are available in the repository at `examples/runs/results.md`.

Links:
- GitHub Repository: https://github.com/farazrasul0-cmd/autonomous-code-agent-space-fractions-v2
- Release Executable (.exe): https://github.com/farazrasul0-cmd/autonomous-code-agent-space-fractions-v2/releases
- YouTube Video: <YOUTUBE_LINK_HERE>

One honest limitation: The agent is ~3,679 lines of Python because I chose to build a rigorous V1-V8 static analyzer, AST checker, and headless Tkinter UI verification layer to guarantee it catches the specific bugs you mentioned. The build is unsigned, so Windows SmartScreen may prompt, but the README explains the SHA256 verification.

Thank you for your time and consideration.

Sincerely,  
MD Mayenaz Rasul Faraz  
College of Software Engineering, Sichuan University
