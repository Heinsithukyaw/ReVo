# 🌐 External Dependencies

This directory contains external dependencies and integrations for the reVoAgent platform.

## 📦 Available Integrations

### MCP Servers Repository
To add the awesome-mcp-servers repository:

```bash
# Clone as a git submodule
git submodule add https://github.com/modelcontextprotocol/awesome-mcp-servers.git external/awesome-mcp-servers

# Or clone directly
git clone https://github.com/modelcontextprotocol/awesome-mcp-servers.git external/awesome-mcp-servers
```

### Other External Dependencies

Add other external repositories or dependencies here:

```bash
external/
├── awesome-mcp-servers/          # MCP servers collection
├── ai-models/                    # Pre-trained AI models
├── templates/                    # Project templates
└── plugins/                      # Third-party plugins
```

## 🔧 Setup Instructions

1. **Initialize submodules** (if using git submodules):
   ```bash
   git submodule update --init --recursive
   ```

2. **Update external dependencies**:
   ```bash
   git submodule update --remote
   ```

3. **Configure integrations** in `config/integrations/`:
   - Update MCP server configurations
   - Add API keys and credentials
   - Configure external service endpoints

## 📚 Documentation

- [MCP Integration Guide](../docs/guides/mcp-integration.md)
- [External API Configuration](../docs/guides/external-apis.md)
- [Plugin Development](../docs/guides/plugin-development.md)