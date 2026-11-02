# Architectural Decisions

## Platform Resolution
- **Platform**: Standalone Desktop Application (Windows Tkinter).
- **Conflict Resolution**: desktop requirement wins; cloud/container/microservice infrastructure is out of scope.

## Naming Convention Standard
- Naming convention: snake_case throughout; architecture diagram camelCase names are translated at model boundary (parser -> contract).
