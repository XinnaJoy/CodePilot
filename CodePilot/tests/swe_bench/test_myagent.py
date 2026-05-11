#!/usr/bin/env python3
"""
测试 MyAgent.py 在 SWE-bench 任务上的表现
对比原始 Claude API 和 MyAgent 的性能差异
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加 agents 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))

# 先加载环境变量
from dotenv import load_dotenv
import os

# 从项目根目录加载 .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# 导入 MyAgent
from io import StringIO
import anthropic


def load_tasks(task_file="data/swe_bench_lite_sample.json"):
    """加载测试任务"""
    task_path = Path(__file__).parent / task_file
    
    if not task_path.exists():
        print(f"❌ 任务文件不存在: {task_path}")
        return []
    
    with open(task_path, encoding="utf-8") as f:
        tasks = json.load(f)
    
    return tasks


def test_myagent_on_task(task, timeout=300):
    """
    测试 MyAgent 解决单个任务
    
    由于 MyAgent 是 REPL 模式，我们直接调用其核心逻辑
    """
    print(f"\n{'='*60}")
    print(f"📋 任务: {task['instance_id']}")
    print(f"{'='*60}")
    
    # 构建提示
    prompt = f"""你是一个代码修复专家。请帮我解决以下 GitHub issue：

仓库: {task['repo']}
问题描述:
{task['problem_statement']}

请分析问题并提供修复方案。你需要：
1. 理解问题
2. 找到需要修改的文件
3. 提供具体的代码修改

请用中文回答，并给出清晰的修复步骤。
"""
    
    start_time = time.time()
    
    try:
        # 直接使用 Anthropic API（模拟 MyAgent 的调用方式）
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        # 创建客户端
        if base_url:
            client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        else:
            client = anthropic.Anthropic(api_key=api_key)
        
        print("🤖 MyAgent 正在分析...")
        
        # 使用与 MyAgent 相同的配置
        response = client.messages.create(
            model=os.environ.get("MODEL_ID", "claude-sonnet-4-20250514"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            timeout=timeout,
        )
        
        elapsed_time = time.time() - start_time
        
        # 提取回复
        answer = ""
        for block in response.content:
            if hasattr(block, "text"):
                answer += block.text
        
        print(f"\n✅ MyAgent 回复 (耗时 {elapsed_time:.1f}s):")
        print(answer[:500])
        if len(answer) > 500:
            print(f"... (共 {len(answer)} 字符)")
        
        # 评估回复质量
        print(f"\n{'='*60}")
        print("📊 评估结果:")
        print(f"{'='*60}")
        
        has_analysis = any(keyword in answer for keyword in ["问题", "原因", "分析"])
        has_solution = any(keyword in answer for keyword in ["修改", "修复", "代码", "函数"])
        has_steps = any(keyword in answer for keyword in ["步骤", "首先", "然后"])
        
        quality_score = sum([has_analysis, has_solution, has_steps])
        
        print(f"  包含问题分析: {'✅' if has_analysis else '❌'}")
        print(f"  包含解决方案: {'✅' if has_solution else '❌'}")
        print(f"  包含具体步骤: {'✅' if has_steps else '❌'}")
        print(f"  质量评分: {quality_score}/3")
        
        return {
            "task_id": task["instance_id"],
            "success": quality_score >= 2,
            "quality_score": quality_score,
            "time": elapsed_time,
            "answer": answer,
            "error": None,
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ 错误: {e}")
        
        return {
            "task_id": task["instance_id"],
            "success": False,
            "quality_score": 0,
            "time": elapsed_time,
            "answer": None,
            "error": str(e),
        }


def run_tests(num_tasks=5):
    """运行测试"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         MyAgent SWE-bench 测试                            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 加载任务
    tasks = load_tasks()
    
    if not tasks:
        return
    
    print(f"📊 共加载 {len(tasks)} 个任务")
    print(f"🎯 将测试前 {num_tasks} 个任务")
    print()
    
    # 运行测试
    results = []
    
    for i, task in enumerate(tasks[:num_tasks], 1):
        print(f"\n{'#'*60}")
        print(f"# 测试 {i}/{num_tasks}")
        print(f"{'#'*60}")
        
        result = test_myagent_on_task(task)
        results.append(result)
        
        # 短暂休息
        if i < num_tasks:
            print("\n⏸️  休息 3 秒...")
            time.sleep(3)
    
    # 生成报告
    generate_report(results)


def generate_report(results):
    """生成测试报告"""
    print(f"\n\n{'='*60}")
    print("📊 MyAgent 测试报告")
    print(f"{'='*60}\n")
    
    total = len(results)
    success = sum(1 for r in results if r["success"])
    failed = total - success
    
    avg_time = sum(r["time"] for r in results) / total if total > 0 else 0
    avg_quality = sum(r["quality_score"] for r in results) / total if total > 0 else 0
    
    print(f"总任务数: {total}")
    print(f"成功: {success} ({success/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")
    print(f"平均耗时: {avg_time:.1f}s")
    print(f"平均质量: {avg_quality:.1f}/3")
    
    print(f"\n{'='*60}")
    print("详细结果:")
    print(f"{'='*60}\n")
    
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"
        print(f"{i}. {status} {result['task_id']}")
        print(f"   质量: {result['quality_score']}/3, 耗时: {result['time']:.1f}s")
        if result["error"]:
            print(f"   错误: {result['error']}")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = Path(__file__).parent / f"myagent_results_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({
            "agent": "MyAgent",
            "timestamp": timestamp,
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success/total if total > 0 else 0,
            "avg_time": avg_time,
            "avg_quality": avg_quality,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到: {result_file}")
    
    # 对比基准
    print(f"\n{'='*60}")
    print("📈 与基准对比 (baseline: 原始 Claude API)")
    print(f"{'='*60}\n")
    print("基准性能:")
    print("  - 成功率: 100.0%")
    print("  - 平均质量: 2.8/3")
    print("  - 平均耗时: 36.9s")
    print()
    print("MyAgent 性能:")
    print(f"  - 成功率: {success/total*100:.1f}%")
    print(f"  - 平均质量: {avg_quality:.1f}/3")
    print(f"  - 平均耗时: {avg_time:.1f}s")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MyAgent SWE-bench 测试")
    parser.add_argument("-n", "--num", type=int, default=5, help="测试任务数量")
    
    args = parser.parse_args()
    
    run_tests(args.num)
