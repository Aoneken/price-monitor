#!/usr/bin/env python3
"""
Script para iniciar el servidor web de Price Monitor.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "webapp.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
