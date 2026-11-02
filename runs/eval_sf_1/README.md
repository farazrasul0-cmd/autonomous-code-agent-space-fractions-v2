# Space Fractions

Desktop application implementation synthesized by DeepSeek Code Agent.

## Architecture Overview
- **Target Platform**: Windows Standalone Desktop Application (Python 3.12 & Tkinter).
- **Dependencies**: Python Standard Library ONLY (zero external pip packages).
- **Modules**:
- `models.py`: Domain model classes: Game, Question, User, Admin
- `app.py`: Application class with UI and game logic
- `main.py`: Entry point: create_app function and main guard

## Running the Application
```bash
python main.py
```

## Running the Test Suite
```bash
python -m unittest discover -s tests -v
```
