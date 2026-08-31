# Open-BikeFit Claude Model Context Protocol (MCP) Guide

The **Open-BikeFit MCP Server** enables Anthropic Claude (Claude Desktop, Claude Code, and MCP-compatible agents) to directly interact with your dynamic bike fitting studio.

---

## Capabilities Provided to Claude

When connected, Claude can:
1. **`openbikefit_analyze_video`**: Run 33-landmark BlazePose tracking + 1€ filtering + 4-phase crank decomposition on any video file and retrieve joint angle telemetry.
2. **`openbikefit_get_fit_targets`**: Fetch scientific target angle envelopes for Road, Gravel, Triathlon/TT, and MTB.
3. **`openbikefit_generate_report`**: Compute millimeter hardware wrench adjustments (saddle height $\pm$mm, fore/aft $\pm$mm, stack spacers $\pm$mm, stem length) cross-referenced against rider pain points.
4. **`openbikefit_compile_pdf`**: Compile high-resolution PDF studio fit reports with embedded 4-phase stills.
5. **`openbikefit_list_sample_datasets`**: Inspect available trainer test videos.
6. **Biomechanical Resources**: Read Holmes knee angle protocols and target tables via `openbikefit://targets/all`.

---

## Claude Desktop Configuration

To connect Open-BikeFit to Claude Desktop:

1. Open your Claude Desktop configuration file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. Add the `open-bikefit` server entry:

```json
{
  "mcpServers": {
    "open-bikefit": {
      "command": "/Users/pruthviomkargeedh/ Enpire hand/NintAi-The-AI-Powered-Bike-Fit-Studio/.venv/bin/python",
      "args": [
        "/Users/pruthviomkargeedh/ Enpire hand/NintAi-The-AI-Powered-Bike-Fit-Studio/mcp_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

3. Restart Claude Desktop. You will see the hammer icon with all Open-BikeFit tools available.

---

## Example Prompts to Ask Claude

- *"Analyze the sample video `inputs/videos/sample_road_endurance.mp4` for a Road bike fit."*
- *"What are the recommended knee extension and closed hip angles for a Triathlon / TT position?"*
- *"I have a knee extension of 134° at BDC and I am feeling pain in the front of my patella. What saddle adjustment should I make?"*
- *"Generate a complete bike fit report and export a PDF for rider Alex Chen."*
