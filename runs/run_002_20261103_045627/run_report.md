# Run Report: run_002_20261103_045627

- **Timestamp**: 20261103_045627
- **Elapsed Time**: 48.00 seconds
- **Total Run Cost**: $0.021155
- **Cumulative Spend**: $0.058404
- **All Passed**: NO

## First-Attempt Verification Summary (V1–V8)

| Check | Name | First-Attempt Status | Errors |
|:---|:---|:---|:---|
| V1 | File Presence | **PASS** | None |
| V2 | AST Compilation | **PASS** | None |
| V3 | Contract Conformance | **PASS** | None |
| V4 | Static Call Resolution | **FAIL** | Attribute 'self._status_var' called with method 'set' was never assigned in class 'App' |
| V5 | Tkinter Method Collisions | **PASS** | None |
| V6 | Import Boundaries | **PASS** | None |
| V7 | Test Execution | **PASS** | None |
| V8 | UI Smoke Walkthrough Harness | **PASS** | None |

## Generated Files

- `models.py`
- `app.py`
- `main.py`
- `tests/test_game.py`
- `requirements.txt`
- `README.md`
- `DECISIONS.md`

## Diagnostic Error Details

1. **[V4]** `app.py`: Attribute 'self._status_var' called with method 'set' was never assigned in class 'App'
