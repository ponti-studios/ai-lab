from dotenv import load_dotenv

load_dotenv()

from src.data.db import connect_to_db  # noqa: E402
from src.server import app  # noqa: E402

connect_to_db()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
