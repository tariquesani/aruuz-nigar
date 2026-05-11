# Aruuz Nigar MCP: Dev Inspector Startup

Run these commands from the `python/` folder in your virtual environment. Each of these commands are to be run in a terminal of its own. 

## Startup order

1. Start the Aruuz Nigar web server and API:

   ```powershell
   python .\app.py
   ```

2. Start the MCP server:

   ```powershell
   python .\mcp\aruuznigar.py
   ```

3. Start the FastMCP dev inspector:

   ```powershell
   fastmcp dev inspector .\mcp\aruuznigar.py:mcp
   ```

## Notes

- Keep all three processes running while testing tools in the inspector.
- MCP server endpoint is served over SSE at `http://127.0.0.1:8765/sse`.
