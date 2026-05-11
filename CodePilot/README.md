# CodePilot

一个基于 Claude API 的智能编程助手，支持多智能体协作、任务管理、后台执行等高级功能。

## ✨ 特性

- 🤖 **智能对话**: 基于 Claude Sonnet 4 的强大 AI 能力
- 👥 **多智能体协作**: 支持创建多个协作的 AI 助手
- 📋 **任务管理**: 内置任务系统，支持任务创建、分配和跟踪
- 🔄 **后台执行**: 支持长时间运行的命令后台执行
- 💾 **记忆系统**: 工作记忆和会话恢复功能
- 🛠️ **技能加载**: 可扩展的技能系统
- 📨 **消息总线**: 智能体间通信机制
- 🔧 **文件操作**: 安全的文件读写和编辑功能

## 📦 安装

### 前置要求

- Python 3.8+
- Anthropic API Key (或兼容的 API 提供商)

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/CodePilot.git
cd CodePilot
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 配置：
```env
ANTHROPIC_API_KEY=sk-ant-xxx
MODEL_ID=claude-sonnet-4-6
```

## 🚀 快速开始

### 基础使用

```bash
python agents/MyAgent.py
```

启动后，你可以直接与 AI 助手对话，它会帮助你完成各种编程任务。

### REPL 命令

在交互模式下，支持以下命令：

- `/compact` - 手动触发对话压缩
- `/tasks` - 查看所有任务
- `/team` - 查看团队成员状态
- `/inbox` - 查看收件箱消息

### 示例对话

```
You: 帮我创建一个 Python 函数来计算斐波那契数列

Agent: 我来帮你创建这个函数...
[Agent 会自动创建文件并实现功能]
```

## 🔧 高级功能

### 多智能体协作

创建多个 AI 助手协同工作：

```python
# 在对话中使用
spawn_teammate(name="coder", role="Python开发", prompt="帮我实现后端API")
spawn_teammate(name="tester", role="测试工程师", prompt="为代码编写测试")
```

### 任务管理

```python
# 创建任务
task_create(subject="实现用户认证", description="使用JWT实现用户登录")

# 查看任务列表
task_list()

# 更新任务状态
task_update(task_id=1, status="completed")
```

### 技能系统

将可复用的知识封装为技能：

```bash
skills/
  my-skill/
    SKILL.md  # 技能定义文件
```

在对话中加载技能：
```python
load_skill(name="my-skill")
```

## 🌐 支持的 API 提供商

除了 Anthropic 官方 API，还支持以下兼容提供商：

| 提供商 | MODEL_ID | Base URL |
|--------|----------|----------|
| Anthropic | claude-sonnet-4-6 | (默认) |
| MiniMax | MiniMax-M2.5 | https://api.minimax.io/anthropic |
| GLM (智谱) | glm-5 | https://api.z.ai/api/anthropic |
| Kimi (月之暗面) | kimi-k2.5 | https://api.moonshot.ai/anthropic |
| DeepSeek | deepseek-chat | https://api.deepseek.com/anthropic |

详见 `.env.example` 文件中的配置说明。

## 📁 项目结构

```
CodePilot/
├── agents/
│   ├── MyAgent.py          # 主智能体程序
│   ├── memory.py           # 记忆系统
│   └── .memory/            # 记忆数据库
├── skills/                 # 技能目录
│   ├── code-review/
│   ├── pdf/
│   └── superpowers/
├── tests/                  # 测试文件
├── .env.example            # 环境变量示例
├── requirements.txt        # Python 依赖
└── README.md              # 项目文档
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_memory_system.py
```

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - 提供强大的 Claude API
- 所有贡献者和使用者

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/CodePilot/issues)
- 发起 [Discussion](https://github.com/yourusername/CodePilot/discussions)

## ⚠️ 注意事项

- 请妥善保管你的 API Key，不要提交到版本控制系统
- 使用 API 会产生费用，请注意控制使用量
- 本项目仅供学习和研究使用

---

**Star ⭐ 本项目以支持开发！**
