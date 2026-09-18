# Manual scripts

Ad-hoc scripts run by hand against a live server or a local checkout. They are
**not** part of the pytest suite — they are `__main__` entry points that print
to stdout for eyeballing.

They live here, and are named `check_*` rather than `test_*`, because pytest
collected them by filename and their basenames collided with real modules in
`tests/` -- which broke `pytest` from the source root.

Run one directly:

```bash
python scripts/manual/check_api.py
```

The real suite is `pytest tests` (and `pytest tests_ui` for the browser smoke
tests).
