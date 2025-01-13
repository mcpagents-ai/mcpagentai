
# MCPAgentAI 🚀 

[![PyPI](https://img.shields.io/pypi/v/mcpagentai.svg)](https://pypi.org/project/mcpagentai/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcpagentai.svg)](https://pypi.org/project/mcpagentai/)
[![License](https://img.shields.io/pypi/l/mcpagentai.svg)](https://github.com/mcpagents-ai/mcpagentai/blob/main/LICENSE)

**MCPAgentAI** is a standardized **tool wrapping framework** for implementing and managing diverse tools in a unified way. It is designed to help developers quickly integrate and launch tool-based use cases.

### Key Features
- 🔧 **Standardized Wrapping**: Provides an abstraction layer for building tools using the MCP protocol.
- 🚀 **Flexible Use Cases**: Easily add or remove tools to fit your specific requirements.
- ✨ **Out-of-the-Box Tools**: Includes pre-built tools for common scenarios:
  - 🕑 Time utilities
  - ☁️ Weather information (API)
  - 📚 Dictionary lookups
  - 🧮 Calculator for mathematical expressions
  - 💵 Currency exchange (API)
  - 📈 Stocks Data: Access real-time and historical stock market information.
  - 🤖 [ElizaOS](https://github.com/elizaos/eliza) Integration: Seamlessly connect and interact with ElizaOS for enhanced automation.
  - 🐦 **Twitter Management**: Automate tweeting, replying, and managing Twitter interactions.
   

### Tech Stack 🛠️
- **Python**: Core programming language
- **[MCP](https://pypi.org/project/mcp/) Framework**: Communication protocol
- **Docker**: Containerization

#### 🤔 What is MCP?

The **Model Context Protocol ([MCP](https://modelcontextprotocol.io/introduction))** is a cutting-edge standard for **context sharing and management** across AI models and systems. Think of it as the **language** AI agents use to interact seamlessly. 🧠✨

Here’s why **MCP** matters:

- 🧩 **Standardization**: MCP defines how context can be shared across models, enabling **interoperability**.
- ⚡ **Scalability**: It’s built to handle large-scale AI systems with high throughput.
- 🔒 **Security**: Robust authentication and fine-grained access control.
- 🌐 **Flexibility**: Works across diverse systems and AI architectures.

![mcp_architecture](https://imageio.forbes.com/specials-images/imageserve/674aaa6ac3007d55b62fc2bf/MCP-Architecture/960x0.png?height=559&width=711&fit=bounds)
[source](https://www.forbes.com/sites/janakirammsv/2024/11/30/why-anthropics-model-context-protocol-is-a-big-step-in-the-evolution-of-ai-agents/)
---

## Installation 📦

### Install via PyPI
```bash
pip install mcpagentai
```

---

## Usage 💻

### Run Locally
```bash
mcpagentai --local-timezone "America/New_York"
```

### Run in Docker
1. **Build the Docker image:**
   `docker build -t mcpagentai .`

2. **Run the container:**
   `docker run -i --rm mcpagentai`

---

## Docker Environment Variables for Twitter Integration 🐦

When running MCPAgentAI within Docker, it's essential to configure environment variables for Twitter integration. These variables are divided into two categories:

### **1. Agent Node Client Credentials**
These credentials are used by the **Node.js client** within the agent for managing Twitter interactions, so the `src/mcpagentai/tools/twitter/client_agent.py`
#### Twitter credentials for Agent Node Client
```dockerfile
ENV TWITTER_USERNAME=
ENV TWITTER_PASSWORD=
ENV TWITTER_EMAIL=
```

### **2. Tweepy (Twitter API v2) Credentials**
These credentials are utilized by **Tweepy** for interacting with Twitter's API v2 so the `src/mcpagentai/tools/twitter/api_agent.py`

#### Twitter API v2 credentials for Tweepy
```dockerfile
ENV TWITTER_API_KEY=
ENV TWITTER_API_SECRET=
ENV TWITTER_ACCESS_TOKEN=
ENV TWITTER_ACCESS_SECRET=
ENV TWITTER_CLIENT_ID=
ENV TWITTER_CLIENT_SECRET=
ENV TWITTER_BEARER_TOKEN=
```


---

## ElizaOS Integration 🤖

[MCPAgentAI](https://github.com/mcpagents-ai/mcpagentai) offers seamless integration with [ElizaOS](https://github.com/elizaos/eliza), providing enhanced automation capabilities through Eliza Agents. There are two primary ways to integrate Eliza Agents:

### **1. Directly Use Eliza Agents from MCPAgentAI**
This approach allows you to use Eliza Agents without running the Eliza Framework in the background. It simplifies the setup by embedding Eliza functionality directly within MCPAgentAI.

**Steps:**

1. **Configure MCPAgentAI to Use Eliza MCP Agent:**
   In your Python code, add Eliza MCP Agent to the `MultiToolAgent`:
    ```python
    from mcpagentai.core.multi_tool_agent import MultiToolAgent
    from mcpagentai.tools.eliza_mcp_agent import eliza_mcp_agent

    multi_tool_agent = MultiToolAgent([
        # ... other agents
        eliza_mcp_agent
    ])
   ```

**Advantages:**
- **Simplified Setup:** No need to manage separate background processes.
- **Easier Monitoring:** All functionalities are encapsulated within MCPAgentAI.
- **Highlight Feature:** Emphasizes the flexibility of MCPAgentAI in integrating various tools seamlessly.


### **2. Run Eliza Framework from MCPAgentAI**
This method involves running the Eliza Framework as a separate background process alongside MCPAgentAI.

**Steps:**

1. **Start Eliza Framework:**
   `bash src/mcpagentai/tools/eliza/scripts/run.sh`

2. **Monitor Eliza Processes:**
   `bash src/mcpagentai/tools/eliza/scripts/monitor.sh`

3. **Configure MCPAgentAI to Use Eliza Agent:**
   In your Python code, add Eliza Agent to the `MultiToolAgent`:
    ```python
   from mcpagentai.core.multi_tool_agent import MultiToolAgent
   from mcpagentai.tools.eliza_agent import eliza_agent

   multi_tool_agent = MultiToolAgent([
       # ... other agents
       eliza_agent
   ])
   ```
---

## Tutorial: Selecting Specific Tools

You can configure MCPAgentAI to run only certain tools by modifying the agent configuration in your server or by updating the `server.py` file to only load desired agents. For example:

```python
from mcpagentai.tools.time_agent import TimeAgent
from mcpagentai.tools.weather_agent import WeatherAgent
from mcpagentai.core.multi_tool_agent import MultiToolAgent

multi_tool_agent = MultiToolAgent([
    TimeAgent(),
    WeatherAgent()
])
This setup will only enable **Time** and **Weather** tools.
```
---

## Integration Example: Claude Desktop Configuration

You can integrate MCPAgentAI with Claude Desktop using the following configuration (`claude_desktop_config.json`), **note that** local ElizaOS repo is optional arg:
```json
{
    "mcpServers": {
        "mcpagentai": {
            "command": "docker",
            "args": ["run", "-i", "-v", "/path/to/local/eliza:/app/eliza", "--rm", "mcpagentai"]
        }
    }
}
```
---

## Development 🛠️

1. **Clone this repository:**
   ```bash
   git clone https://github.com/mcpagents-ai/mcpagentai.git
   cd mcpagentai
   ```

2. **(Optional) Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Build the package:**
   ```bash
   python -m build
   ```
---

## Contributing 🤝

We welcome contributions! Please open an [issue](https://github.com/mcpagents-ai/mcpagentai/issues) or [pull request](https://github.com/mcpagents-ai/mcpagentai/pulls).

---

**License**: MIT  
Enjoy! 🎉
