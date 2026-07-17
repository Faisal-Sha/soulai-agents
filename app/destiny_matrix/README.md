# Destiny Matrix (calculation engine)

Pure Python calculator used by the agent tool `calculate_destiny_matrix`.

## Flow (simple)

```text
User asks for a matrix
        │
        ▼
   "my matrix"? ──yes──► get_user_context
        │                     │
        │              exists? ──yes──► use saved_matrices
        │                     │
        │                     no + DOB → calculate → save personal
        │
   friend matrix
        │
        ▼
memory_search (reuse if known)
        │
        no DOB → ask user (HIL)
        │
        ▼
calculate_destiny_matrix (friend)
        │
        ▼
Save to long-term memory:
  person_sarah_relation / _dob / _matrix
        │
        ▼
knowledge_search → final reading
```

## Files in this folder

| File | Role |
|------|------|
| `calculator.py` | Matrix math |
| `parser.py` | DOB parsing / validation |
| `utils.py` | Digit reduction helpers |
| `__init__.py` | Public exports |

LangChain tool: `app/tools/destiny_matrix.py`  
Storage logic: `app/services/matrix_service.py`

## Direct use

```python
from app.destiny_matrix import calculate_matrix

matrix = calculate_matrix("17/01/1993")
print(matrix["center"])  # 8
```

Accepted dates: `DD/MM/YYYY`, `YYYY-MM-DD`, and forms like `11 July 1998`.

## Tests

```bash
python -m unittest tests.test_destiny_matrix -v
```
