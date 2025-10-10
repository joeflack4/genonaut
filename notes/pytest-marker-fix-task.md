# 🧪 Pytest Unknown Mark Warnings — Fix Task Prompt

## 📝 Background: Original Warning

```
test/integrations/comfyui/test_comfyui_mock_server_files.py:117
  /Users/joeflack4/projects/genonaut/test/integrations/comfyui/test_comfyui_mock_server_files.py:117: PytestUnknownMarkWarning: Unknown pytest.mark.comfyui_poll - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.comfyui_poll
```

This warning appears because `comfyui_poll` (and other markers like `slow` / `longrunning`) haven’t been **registered** in the project’s pytest configuration.

---

## 🧭 Goal

Register all custom pytest markers so that:
- `pytest` recognizes them,
- `PytestUnknownMarkWarning` disappears,
- marker-based selection (`-m "markername"`) works cleanly,
- the codebase stays consistent and discoverable via `pytest --markers`.

---

## 🛠️ Step-by-Step Instructions

### 1. Identify All Custom Markers
Search for any `@pytest.mark.<something>` in the codebase:
```bash
grep -R "@pytest.mark." test/
```
Examples found:
- `comfyui_poll`
- `slow`
- `longrunning`

---

### 2. Add Marker Declarations

#### Option A — `pytest.ini` (recommended)
```ini
# pytest.ini
[pytest]
markers =
    comfyui_poll: poll ComfyUI mock server
    slow: long/expensive tests
    longrunning: alias of slow
```

#### Option B — `pyproject.toml`
```toml
[tool.pytest.ini_options]
markers = [
  "comfyui_poll: poll ComfyUI mock server",
  "slow: long/expensive tests",
  "longrunning: alias of slow"
]
```

#### Option C — `conftest.py` (fallback)
```python
def pytest_configure(config):
    config.addinivalue_line("markers", "comfyui_poll: poll ComfyUI mock server")
    config.addinivalue_line("markers", "slow: long/expensive tests")
    config.addinivalue_line("markers", "longrunning: alias of slow")
```

---

### 3. Verify the Fix
```bash
pytest --markers
pytest -m "comfyui_poll" -v
```
✅ Expected:  
- Markers appear in the list.  
- No more warnings.  
- Marked tests are discoverable and runnable.

---

## 🚨 Optional Strictness (Nice to Have)

Enable strict marker checking to catch typos:
```ini
# pytest.ini
[pytest]
addopts = -o strict_markers=true
```

---

## ✅ Deliverable

- [ ] All custom markers registered
- [ ] Warnings gone
- [ ] `pytest --markers` lists them
- [ ] PR with changes to `pytest.ini` or equivalent config file

---

**References:**  
- [pytest docs: How to mark test functions](https://docs.pytest.org/en/stable/how-to/mark.html)
