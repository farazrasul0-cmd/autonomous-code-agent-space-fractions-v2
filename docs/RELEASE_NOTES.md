# DeepSeek Code Agent — Release v1.0

Official standalone binary release of the DeepSeek Code Agent for Task 1 evaluation.

---

## 1. Release Artifacts & SHA256 Checksums

| Artifact | Distribution Type | SHA256 Checksum | Description |
|:---|:---:|:---:|:---|
| **`CodeAgent_onedir.zip`** | **Primary (Recommended)** | `0948CBE181EEEB12F66D7FD99E0A77243001ADE62D8FD28F6F40E79E89A4AC50` | Complete unpacked folder bundle (`CodeAgent.exe` + `_internal/` runtime). Fastest startup, fully compatible with Windows Sandbox. |
| **`CodeAgentOneFile.exe`** | Secondary (Single-file) | `45DB81CB26DE769EF008710273A53322DFC9EE6AA8C2FF69CA62C09607F3137E` | Standalone portable executable unpacking dynamically into `%TEMP%`. |
| **`CodeAgent.exe`** (internal) | Binary Executable | `B771F3F76A8053D8CFD1A26827BE9A558A19486066082B91B7B3D4278B2837A9` | Unpacked executable entrypoint within the onedir bundle. |

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
   - **Opt-In TLS Bypass**: Strict TLS verification by default; explicit GUI checkbox allows bypassing in isolated sandboxes where root certificates are missing.
   - **Temp-Directory Cache**: Uses `%TEMP%\CodeAgent_cache` to support read-only shared folder mounts.
5. **Generality Proven Across Diverse Architectures**:
   - Evaluated on **Space Fractions** (Gaming architecture: `Game`, `Question`, `User`, `Admin`).
   - Evaluated on **Smart To-Do List** (Productivity architecture: `Task`, `TaskManager`).
   - Autonomous self-repair across runs under an authoritative total spend of **~$0.26 USD / ¥1.91 CNY** (well below the $1.00 budget ceiling).

---

## 4. Quick Start Instructions

1. Extract `CodeAgent_onedir.zip`.
2. Double-click `CodeAgent.exe`.
3. Provide your DeepSeek API Key in the masked field (or ensure `DEEPSEEK_API_KEY` is present in your environment). Click **"Test Key"** to verify.
4. Select the Architecture Documentation and Architecture View files (defaults prefilled to `examples/inputs/`).
5. Click **"Start Synthesis"**.
6. When complete, click **"Launch Game"** to launch the synthesized application in an independent detached process.
