# Install
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
cd ..\frontend
corepack enable
pnpm install
cd ..

# Run all tests
py -m unittest discover -s tests -v
py qa\triage_noisedoselab.py
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -v
cd frontend
pnpm test
pnpm build
cd ..

# Terminal 1 — backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
pnpm dev
