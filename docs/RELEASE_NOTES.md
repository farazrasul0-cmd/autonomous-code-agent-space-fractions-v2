# DeepSeek Code Agent — Release v1.0

Official standalone binary release of the DeepSeek Code Agent for Task 1 evaluation.

---

## 1. Release Artifacts & SHA256 Checksums

| Artifact | Distribution Type | SHA256 Checksum | Description |
|:---|:---:|:---:|:---|
| **`CodeAgent_onedir.zip`** | **Primary (Recommended)** | `7C62CCAAE420078C0EE386E5467B8F6763BD9964D98A204ED3E565953400A58E` | Complete unpacked folder bundle (`CodeAgent.exe` + `_internal/` runtime). Fastest startup, fully compatible with Windows Sandbox. |
| **`CodeAgentOneFile.exe`** | Secondary (Single-file) | `08FD325334B4B9408A575F722E83645DB5E4D318D206EDCF5C5AA299F376643A` | Standalone portable executable unpacking dynamically into `%TEMP%`. |
| **`CodeAgent.exe`** (internal) | Binary Executable | `FB77230DC28F8CF0047EADBB88485EA68B2283BA9AC0F2B9E61A990529A4D039` | Unpacked executable entrypoint within the onedir bundle. |

---

## 2. Windows SmartScreen Verification Notice

> [!NOTE]
> **Windows SmartScreen Prompt**: Because this standalone binary is built for academic research and evaluation without a paid commercial Authenticode code-signing certificate, Windows Defender SmartScreen may display a blue dialog (*"Windows protected your PC"*).
> 
> **How to Run**:
> 1. Click **"More info"**.
> 2. Click **"Run anyway"**.
> 3. To verify binary integrity before execution, run in PowerShell:
>    ```powershell
>    Get-FileHash .\CodeAgent_onedir.zip -Algorithm SHA256
>    Get-FileHash .\CodeAgentOneFile.exe -Algorithm SHA256
>    ```
>    Ensure the SHA256 hash matches the table above.

---

## 3. Key Capabilities & Highlights

1. **Contract-First Synthesis**:
   - Parses software architecture documents (`.md`) and PlantUML diagrams (`spec.json`).
   - DeepSeek synthesizes a formal architectural contract (`contract.json`) defining exact classes, attributes, methods, topological module orders, and smoke test sequences before code is generated.
2. **Layered Verification Suite (V1–V8)**:
   - **V1**: File Existence
   - **V2**: AST Syntax Compilation
   - **V3**: Contract Conformance
   - **V4**: Cross-File Static Call Resolution
   - **V5**: Tkinter Method Collision Guard
   - **V6**: Import Dependency Confinement
   - **V7**: Automated Unit Test Execution
   - **V8**: Headless UI Screen Walkthrough Harness
3. **Autonomous Multi-Turn Repair Loop**:
   - Diagnostic AST errors and runtime test failures are reinjected as structured observations.
   - The agent tool calling interface (`read_file`, `write_file`, `list_dir`, `run_checks`) autonomously modifies failing files until checks pass.
4. **Sandboxed Environment Resiliency**:
   - **Graceful SSL Fallback**: Automatically degrades to an unverified SSL context if fresh Windows Sandbox environments lack updated root CA certificates.
   - **Temp-Directory Cache**: Uses `%TEMP%\CodeAgent_cache` to support read-only shared folder mounts.
5. **Generality Proven Across Diverse Architectures**:
   - Evaluated on **Space Fractions** (Gaming architecture: `Game`, `Question`, `User`, `Admin`).
   - Evaluated on **Smart To-Do List** (Productivity architecture: `Task`, `TaskManager`).
   - Achieved 100% pass rate after autonomous self-repair across all 4 evaluation runs under a total token spend of **$0.108** (well below the $1.00 budget ceiling).

---

## 4. Quick Start Instructions

1. Extract `CodeAgent_onedir.zip`.
2. Double-click `CodeAgent.exe`.
3. Provide your DeepSeek API Key in the masked field (or ensure `DEEPSEEK_API_KEY` is present in your environment). Click **"Test Key"** to verify.
4. Select the Architecture Documentation and Architecture View files (defaults prefilled to `examples/inputs/`).
5. Click **"Start Synthesis"**.
6. When complete, click **"Launch Game"** to launch the synthesized application in an independent detached process.
