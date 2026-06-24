# Aruuz Nigar MCP

## Dev inspector startup

Run these commands from the project root in your virtual environment. Each command runs in its own terminal.

### Startup order

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

### Notes

- Keep all three processes running while testing tools in the inspector.
- MCP server endpoint is served over SSE at `http://127.0.0.1:8765/sse`.

## Claude Desktop bundle (`.mcpb`)

The `Aruuz-Nigar.mcpb` bundle connects Claude Desktop to the running SSE server. Users must start Aruuz Nigar first (for example via `aruuznigar.exe` or `launcher.py`) before installing or using the extension.

To rebuild the bundle after changing `manifest.json`:

```powershell
npx @anthropic-ai/mcpb pack mcp Aruuz-Nigar.mcpb
```

## Bundled third-party binary

The `.mcpb` includes **`mcp-claude-bridge.exe`**, a stdio-to-SSE bridge so Claude Desktop can talk to the HTTP MCP server without Node.js or `npx`.

| | |
|---|---|
| **Project** | [mcp-claude-bridge](https://github.com/LennardGeissler/mcp-claude-bridge) |
| **Author** | Lennard Geissler |
| **Version** | v0.1.0 (`mcp-claude-bridge-v0.1.0-windows-amd64.exe`) |
| **License** | [MIT](https://github.com/LennardGeissler/mcp-claude-bridge/blob/main/LICENSE) |
| **Releases** | https://github.com/LennardGeissler/mcp-claude-bridge/releases |

