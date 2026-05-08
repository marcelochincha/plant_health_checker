# Running the test suite

Step-by-step setup for a fresh machine with **no** Python dependencies installed.
Tested on Python 3.11+ on Linux, macOS and Windows.

## 1. Prerequisites

| Tool | Minimum | Check |
| --- | --- | --- |
| Python | 3.11 | `python --version` |
| git | 2.30 | `git --version` |
| pip | bundled with Python | `python -m pip --version` |

> Python 3.10 or older will not work — `from __future__ import annotations` plus
> the `str | Path` syntax in `inference.py` requires 3.11+.

## 2. Clone the repository

```bash
git clone https://github.com/marcelochincha/plant_health_checker.git
cd plant_health_checker
```

## 3. Create an isolated virtual environment

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows (cmd.exe):

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

## 4. Install dependencies

The shared library and both services use the same set of runtime packages, plus
`pytest` for the test suite:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
```

That installs:

- `numpy>=1.23`
- `opencv-python>=4.8`
- `scikit-image>=0.21`
- `scikit-learn>=1.3`
- `joblib>=1.3`
- `pytest`

No GPU, no PlantVillage download, no environment variables required.

## 5. Run the tests

### 5.1 Service-level tests (added by this milestone — 6 tests)

```bash
python -m pytest services/training/tests services/classifier/tests -v
```

Expected output:

```
services/training/tests/test_evaluate.py::test_evaluate_writes_report PASSED
services/training/tests/test_train.py::test_extract_features_returns_2d_float32 PASSED
services/training/tests/test_train.py::test_train_main_writes_all_artifacts PASSED
services/classifier/tests/test_inference.py::test_predict_returns_expected_keys PASSED
services/classifier/tests/test_inference.py::test_predict_raises_on_invalid_bytes PASSED
services/classifier/tests/test_inference.py::test_init_raises_on_missing_artifacts PASSED

============================== 6 passed in ~2s ==============================
```

These tests are fully synthetic — they generate their own images and dataset
trees inside `pytest`'s `tmp_path`, so nothing on disk is read or modified
outside the temp dir.

### 5.2 Shared-library tests (inherited from the CV prototype — 97 tests)

```bash
python -m pytest tests -v
```

### 5.3 Everything at once

```bash
python -m pytest -v
```

`pyproject.toml` already wires `testpaths = ["tests", "services"]` and
`pythonpath = ["."]`, so a bare `pytest` from the repo root discovers both
suites and resolves the `from pipeline import ...` style imports without any
extra `PYTHONPATH` setup.

## 6. Troubleshooting

**`ModuleNotFoundError: No module named 'pipeline'`**
You are running pytest from outside the repo root, or the virtualenv is not
active. `cd` to the repo root and re-run; `pyproject.toml` adds the root to
`pythonpath` only when pytest is invoked from there.

**`ModuleNotFoundError: No module named 'cv2'`**
`opencv-python` did not install. On minimal Linux images install the system
package providing `libGL.so.1`:

```bash
sudo apt-get install -y libgl1
```

Then reinstall: `pip install --force-reinstall opencv-python`.

**`scikit-image` build errors on Python 3.13**
Use Python 3.11 or 3.12 — the wheels for 3.13 are not yet published for every
platform at the time this was written.

## 7. What the tests do not cover

The suite never touches the real PlantVillage dataset. To exercise the
end-to-end training pipeline against real data, follow the instructions in
[`services/training/README.md`](services/training/README.md) — that flow is
deliberately out of scope for the unit tests.
