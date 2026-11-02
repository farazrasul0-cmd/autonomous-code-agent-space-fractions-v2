# Email Draft to Professor Liang

**Subject**: Task 1 Submission - DeepSeek Code Agent - Faraz (Sichuan University)

---

Dear Professor Liang,

Thank you for the opportunity to take the evaluation. I have completed the implementation of the simplified Code Agent based on the Claude-Code mechanisms.

What changed in the architecture: 
1. Contract-First Generation: The agent parses the UML docs and writes a strict contract before a single line of app code is generated.
2. Verification & Repair Loop: It uses AST static analysis to check for cross-file API mismatches (your bug examples), runs unit tests, and performs a headless UI walkthrough to catch runtime crashes, autonomously repairing them.
3. Generality: To prove it is not hardcoded, I evaluated it on the Space Fractions input (3 runs) and a completely different To-Do list input (1 run). All 4 runs passed.

Evaluation Results & Cost:
- Pass Rate: 100% after autonomous repair.
- Total Token Spend: $0.108 (Well under the $1.00 limit).
- Raw logs and evaluation tables are available in the repository at `examples/runs/results.md`.

Links:
- GitHub Repository: https://github.com/farazrasul0-cmd/autonomous-code-agent-space-fractions-v2
- Release Executable (.exe): https://github.com/farazrasul0-cmd/autonomous-code-agent-space-fractions-v2/releases
- YouTube Video: <YOUTUBE_LINK_HERE>

One honest limitation: The agent is ~2,200 lines of Python (larger than the ~900 planned) because I chose to build a rigorous V1-V8 static analyzer and AST checker to guarantee it catches the specific bugs you mentioned. The build is unsigned, so Windows SmartScreen may prompt, but the README explains the SHA256 verification.

Thank you for your time and consideration.

Sincerely,  
MD Mayenaz Rasul Faraz  
College of Software Engineering, Sichuan University
