# Music Search MCP Server

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12.4%2B-green.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

一个基于 FastMCP 的音乐搜索服务器，支持在线搜索歌曲、获取播放链接和歌词信息。

## ✨ 功能特性

- 🔍 **智能搜索**: 支持按歌曲名或歌手名搜索音乐
- 🎵 **播放支持**: 获取歌曲播放链接和封面图片
- ?? **歌词显示**: 支持获取歌曲歌词信息
- 🤖 **MCP 集成**: 兼容 Model Context Protocol 标准
- 🚀 **高性能**: 异步处理，快速响应

## 📦 安装

### 使用 uv (推荐)

```bash
# 克隆项目
git clone https://github.com/ailearncoder/music-search.git
cd music-search

# 安装依赖
uv sync

# 运行服务器
uv run music-search
```

### 使用 pip

```bash
pip install music-search
```

## ⚡️ 快速开始

### 作为独立应用运行

```bash
# 直接运行
music-search

# 或使用 Python 模块
python -m music_search
```

### 作为 MCP 服务器集成

在你的 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "music-search": {
      "command": "music-search"
    }
  }
}
```

## 🛠️ API 使用

### 搜索音乐

```python
from music_search import search_music

# 搜索歌曲
results = search_music("周杰伦 七里香")

# 搜索结果示例
[
    {
        "url": "https://music-url.com/play.mp3",
        "title": "七里香",
        "artist": "周杰伦", 
        "artworkUrl": "https://cover-url.com/cover.jpg"
    }
]
```

### 命令行使用

```bash
# 搜索音乐
curl -X POST http://localhost:8000/tools/search_music \
  -H "Content-Type: application/json" \
  -d '{"keyword": "林俊杰"}'
```

## 📁 项目结构

```
music-search/
├── src/
│   └── music_search/
│       ├── __init__.py          # 主程序入口
│       ├── mcp_server.py        # MCP 服务器实现
│       ├── api_music_gequbao.py # 音乐 API 实现
│       └── logging_config.py    # 日志配置
├── pyproject.toml               # 项目配置
├── README.md                    # 项目说明
└── .gitignore                   # Git 忽略文件
```

## 💻 开发

### 设置开发环境

```bash
# 克隆项目
git clone https://github.com/ailearncoder/music-search.git
cd music-search

# 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装开发依赖
uv sync --dev
```

### 运行测试

```bash
# 运行单元测试
uv run pytest

# 运行代码检查
uv run ruff check
uv run mypy src/
```

## 🌐 支持的平台

- **音乐源**: 歌曲宝 (gequbao.com)
- **协议**: HTTP/HTTPS
- **编码**: UTF-8

## ⚠️ 注意事项

1. **网络依赖**: 需要稳定的网络连接访问音乐 API
2. **服务可用性**: 依赖第三方音乐服务的可用性
3. **版权声明**: 请遵守相关版权法律法规，仅用于学习和研究目的

## 📝 免责声明

**重要提示：本工具仅供交流学习使用**

- **数据来源**: 本工具通过访问 [歌曲宝](https://www.gequbao.com) 获取音乐相关信息
- **版权声明**: 我们不保证获取到的音乐信息的版权归属，所有音乐资源版权归原作者及版权方所有
- **使用限制**: 本代码仅用于技术交流和学习目的，严禁用于商业用途
- **责任声明**: 如有资源侵权问题，与开发者无关，使用者需自行承担相应法律责任
- **合规使用**: 请遵守当地法律法规，合理使用本工具

**使用者在使用本工具前应充分了解并同意上述声明，如不同意请立即停止使用。**

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) - MCP Python SDK
- [歌曲宝](https://www.gequbao.com) - 音乐数据源
- [Requests](https://docs.python-requests.org/) - HTTP 请求库
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析

## 📞 联系方式

- 作者: ailearncoder
- 邮箱: ailearncoder8@gmail.com
- 项目地址: [https://github.com/ailearncoder/music-search](https://github.com/ailearncoder/music-search)

---

⭐ 如果这个项目对你有帮助，请给它一个 Star！