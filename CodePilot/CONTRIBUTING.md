# 贡献指南

感谢你考虑为 CodePilot 做出贡献！

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 Issue 并包含以下信息：

- Bug 的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python 版本等）
- 相关日志或截图

### 提出新功能

如果你有新功能的想法：

1. 先检查 Issues 中是否已有类似建议
2. 创建一个新的 Feature Request Issue
3. 详细描述功能需求和使用场景
4. 等待社区讨论和反馈

### 提交代码

1. **Fork 仓库**
   ```bash
   # 在 GitHub 上点击 Fork 按钮
   git clone https://github.com/your-username/CodePilot.git
   cd CodePilot
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **编写代码**
   - 遵循现有代码风格
   - 添加必要的注释
   - 确保代码通过测试

4. **运行测试**
   ```bash
   pytest tests/
   ```

5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   # 或
   git commit -m "fix: 修复某个问题"
   ```

   提交信息格式：
   - `feat:` 新功能
   - `fix:` Bug 修复
   - `docs:` 文档更新
   - `style:` 代码格式调整
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建或辅助工具变动

6. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 在 GitHub 上打开你的 fork
   - 点击 "New Pull Request"
   - 填写 PR 描述，说明你的更改
   - 等待代码审查

## 代码规范

### Python 代码风格

- 遵循 PEP 8 规范
- 使用 4 个空格缩进
- 函数和类添加文档字符串
- 变量命名使用小写加下划线
- 类名使用驼峰命名法

### 示例

```python
def calculate_fibonacci(n: int) -> int:
    """
    计算斐波那契数列的第 n 项
    
    Args:
        n: 项数（从 0 开始）
    
    Returns:
        第 n 项的值
    
    Raises:
        ValueError: 当 n 为负数时
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    if n <= 1:
        return n
    
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)
```

## 测试

### 编写测试

- 为新功能添加单元测试
- 测试文件放在 `tests/` 目录
- 测试函数以 `test_` 开头
- 使用 pytest 框架

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_memory_system.py

# 查看覆盖率
pytest --cov=agents tests/
```

## 文档

- 更新相关文档（README.md 等）
- 为新功能添加使用示例
- 保持文档与代码同步

## 行为准则

- 尊重所有贡献者
- 保持友好和专业的态度
- 接受建设性的批评
- 关注对项目最有利的事情

## 问题？

如有任何问题，欢迎：

- 在 Issues 中提问
- 在 Discussions 中讨论
- 查看现有文档和代码

再次感谢你的贡献！🎉
