# TestSprite MCP Setup

TestSprite has been successfully installed and configured for your Cursor IDE.

## Installation Status

✅ **TestSprite MCP Server**: Installed globally via npm
- Package: `@testsprite/testsprite-mcp@0.0.18`
- Location: `C:\Users\sanvi\AppData\Roaming\npm\node_modules\@testsprite\testsprite-mcp`

✅ **API Key**: Configured in `.cursor/mcp.json`

## Configuration

The MCP server is configured in `.cursor/mcp.json` with your API key. Cursor should automatically detect this configuration.

## Manual Configuration (if needed)

If Cursor doesn't automatically detect the configuration, you can manually add it:

1. Open Cursor Settings
2. Navigate to `Features > MCP` or `Settings > MCP`
3. Click "+ Add New MCP Server"
4. Use the following configuration:
   - **Name**: testsprite
   - **Command**: `node`
   - **Args**: `C:\Users\sanvi\AppData\Roaming\npm\node_modules\@testsprite\testsprite-mcp\dist\index.js`
   - **Environment Variables**:
     - `API_KEY`: `sk-user-3Bxngiwtmgeyc-p2sygjUgHHPWm_n1Jbsl6DrjZ0KWtgogaj9yrtlEFLZalilxuxwunR2KWXPRQVEhsdU2xsVAh27j4kNJGS2QqZr-mams7McOA-6tgBZB-RJeVuUhyT7-w`

## Usage

Once configured, you can use TestSprite by asking your AI assistant:

```
Can you test this project with TestSprite?
```

or

```
Help me test this project with TestSprite.
```

## Verification

To verify the installation:
1. Restart Cursor IDE
2. Check if TestSprite MCP tools are available in your AI assistant
3. Try asking: "Help me test this project with TestSprite"

## Troubleshooting

If you encounter issues:
- Ensure Node.js version 22+ is installed (you have v22.19.0 ✅)
- Restart Cursor after configuration
- Check that the MCP server path is correct
- Verify the API key is correctly set in the environment variables

