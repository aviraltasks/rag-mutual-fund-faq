"""
Run the backend API. Execute from this directory:
  python run.py
  or: uvicorn api.app:app --host 0.0.0.0 --port 8000
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=False)
