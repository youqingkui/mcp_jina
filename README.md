# MCP Jina

[English](#english) | [中文](#chinese)

<a name="english"></a>
## English Documentation

### Introduction
A Jina AI service implementation based on [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). This service enables LLMs like Claude to access Jina AI capabilities through the MCP protocol.

### Features
- Full MCP protocol support
- Jina AI API integration
- Tool invocation capabilities
- Claude Desktop integration

### Requirements
- Python >= 3.12
- Valid Jina AI API key

### Quick Start

#### 1. Installation
```bash
# Clone repository
git clone https://github.com/youqingkui/mcp_jina.git
cd mcp_jina

# Create environment and install dependencies
uv venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

uv pip install -e .
```

#### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file, add your API key
JINA_API_KEY=your_jina_api_key_here
```

#### 3. Test Service
Use MCP Inspector for testing:
```bash
npx @modelcontextprotocol/inspector uv run mcp-jina
```

### Claude Desktop Integration

#### 1. Configuration File Location
- MacOS/Linux: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

#### 2. Configuration Example
```json
{
    "mcpServers": {
        "mcp-jina": {
            "command": "uv",
            "args": [
                "--directory",
                "/absolute/path/to/mcp_jina",  // Replace with actual path
                "run",
                "mcp-jina"
            ],
            "env": {
                "JINA_API_KEY": "your_jina_api_key_here"
            }
        }
    }
}
```

#### 3. Usage
1. Launch Claude Desktop
2. Check the hammer icon in the toolbar for service connection status
3. Use Jina AI features in conversations

### Troubleshooting

#### Common Issues
- **Service Not Showing**
  - Check configuration file syntax
  - Verify project path
  - Restart Claude Desktop

#### View Logs
```bash
# MacOS/Linux
tail -f logs/jina_reader.log

# Windows
type logs\jina_reader.log
```

#### Common Error Solutions
- Invalid API Key: Check key in .env file
- Connection Failed: Check network and firewall settings
- Service Start Failed: Verify Python environment setup

---

<a name="chinese"></a>
## 中文文档

### 简介
基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 的 Jina AI 服务实现。该服务允许 Claude 等 LLM 通过 MCP 协议访问 Jina AI 的功能。

### 功能特点
- 完整支持 MCP 协议标准
- 集成 Jina AI API 功能
- 提供工具调用能力
- 支持 Claude Desktop 集成

### 系统要求
- Python >= 3.12
- 有效的 Jina AI API 密钥

### 快速开始

#### 1. 安装
```bash
# 克隆仓库
git clone https://github.com/youqingkui/mcp_jina.git
cd mcp_jina

# 创建环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

uv pip install -e .
```

#### 2. 配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加你的 API 密钥
JINA_API_KEY=your_jina_api_key_here
```

#### 3. 测试服务
使用 MCP Inspector 进行测试：
```bash
npx @modelcontextprotocol/inspector uv run mcp-jina
```

### Claude Desktop 集成

#### 1. 配置文件位置
- MacOS/Linux: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

#### 2. 配置示例
```json
{
    "mcpServers": {
        "mcp-jina": {
            "command": "uv",
            "args": [
                "--directory",
                "/absolute/path/to/mcp_jina",  // 替换为实际路径
                "run",
                "mcp-jina"
            ],
            "env": {
                "JINA_API_KEY": "your_jina_api_key_here"
            }
        }
    }
}
```

#### 3. 使用方法
1. 启动 Claude Desktop
2. 检查工具栏中的锤子图标，确认服务连接状态
3. 在对话中使用 Jina AI 功能

### 故障排除

#### 常见问题
- **服务未显示**
  - 检查配置文件语法
  - 确认项目路径正确
  - 重启 Claude Desktop

#### 日志查看
```bash
# MacOS/Linux
tail -f logs/jina_reader.log

# Windows
type logs\jina_reader.log
```

#### 常见错误解决
- API 密钥无效：检查 .env 文件中的密钥
- 连接失败：检查网络和防火墙设置
- 服务启动失败：验证 Python 环境配置

