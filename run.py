import os
import uvicorn

if __name__ == "__main__":
    port_env = os.environ.get("PORT", "10000")
    try:
        port = int(port_env)
    except ValueError:
        port = 10000

    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
