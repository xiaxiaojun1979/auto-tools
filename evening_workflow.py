#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌙 AutoTools 晚间工作流（20:00定时执行）
1. 分析热门应用趋势
2. 开发1-2个新工具
3. 发布到网站
4. 生成运营报告
5. 发送邮件通知
"""

import sys, os, json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "daily_report"
ORDERS_FILE = LOG_DIR / "data" / "orders.json"

# 确保导入路径
sys.path.insert(0, str(BASE_DIR))


def log(msg):
    """记录日志"""
    log_file = LOG_DIR / "evening_workflow.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def step1_analyze_trends():
    """第一步：分析热门应用趋势"""
    log("📊 第一步：分析热门应用趋势...")
    try:
        from market_research import analyze_trends, get_all_available_tools
        recommendations, trend_data = analyze_trends()
        available = get_all_available_tools()
        log(f"    趋势类别: {trend_data['total_categories']}")
        log(f"    已有产品: {trend_data['existing_products']}")
        log(f"    可开发: {len(available)} 个")
        log(f"    推荐开发: {len(recommendations)} 个")
        for rec in recommendations:
            log(f"      ✅ {rec['name']} (¥{rec['price']})")
        return recommendations
    except Exception as e:
        log(f"    ❌ 分析失败: {e}")
        import traceback
        log(traceback.format_exc())
        return []


def step2_develop_tools(recommendations):
    """第二步：开发新工具"""
    if not recommendations:
        log("📦 第二步：无可开发的新工具")
        return []
    
    log(f"🔧 第二步：开发 {len(recommendations)} 个新工具...")
    try:
        from daily_dev_pipeline import generate_tool_code, add_to_products
        developed = []
        
        for rec in recommendations:
            tool_info = {
                "id": rec["tool_id"],
                "name": rec["name"],
                "desc": rec["desc"],
                "price": rec["price"],
                "category": rec["category"]
            }
            
            # 生成代码
            file_path = generate_tool_code(tool_info)
            log(f"     📄 代码生成: {file_path}")
            
            # 添加到产品
            if add_to_products(tool_info):
                log(f"     ✅ 已上架: {tool_info['name']} ¥{tool_info['price']}")
                developed.append(tool_info)
            else:
                log(f"     ⚠️ 上架失败")
        
        # 统计
        with open(BASE_DIR / "products" / "products.json") as f:
            products = json.load(f)
        total_value = sum(p["price"] for p in products)
        log(f"     📊 产品总数: {len(products)}, 总价值: ¥{total_value}")
        
        return developed
    except Exception as e:
        log(f"    ❌ 开发失败: {e}")
        import traceback
        log(traceback.format_exc())
        return []


def step3_generate_report():
    """第三步：生成运营报告"""
    log("📈 第三步：生成运营报告...")
    try:
        from daily_report.reporter import run as run_reporter
        run_reporter()
        log("    ✅ 运营报告已生成")
    except Exception as e:
        log(f"    ❌ 报告生成失败: {e}")
    
    try:
        from auto_optimizer import AutoOptimizer
        optimizer = AutoOptimizer()
        optimizer.run()
        log("    ✅ 优化报告已生成")
    except Exception as e:
        log(f"    ❌ 优化报告生成失败: {e}")


def step4_send_email():
    """第四步：发送邮件报告"""
    log("📧 第四步：发送邮件报告...")
    try:
        from email_report import build_report, send_email
        html = build_report()
        related = send_email(html)
        log(f"    ✅ 邮件处理完成")
    except Exception as e:
        log(f"    ❌ 邮件发送失败: {e}")
        import traceback
        log(traceback.format_exc())


def step5_push_to_git():
    """第五步：推送到GitHub触发Zeabur部署"""
    log("📤 第五步：推送到GitHub...")
    try:
        import subprocess
        # Add all changes
        result = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, text=True, timeout=30,
            cwd=str(BASE_DIR)
        )
        log(f"    git add: {result.returncode}")
        
        # Commit
        today = datetime.now().strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "commit", "-m", f"auto: 每日更新 {today} - 新工具+报告"],
            capture_output=True, text=True, timeout=30,
            cwd=str(BASE_DIR)
        )
        if result.returncode == 0:
            log(f"    ✅ 提交成功: {result.stdout[:100]}")
        else:
            log(f"    git commit: {result.stderr[:100]}")
        
        # Push via SSH
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True, text=True, timeout=120,
            cwd=str(BASE_DIR),
            env={**os.environ, "GIT_SSH_COMMAND": "ssh -i /tmp/deploy_key -o StrictHostKeyChecking=no"}
        )
        if result.returncode == 0:
            log(f"    ✅ 推送成功")
        else:
            log(f"    git push: {result.stderr[:100]}")
    except subprocess.TimeoutExpired:
        log(f"    ⚠️ 推送超时")
    except Exception as e:
        log(f"    ❌ Git操作失败: {e}")


def step0_maintenance():
    """第零步：系统维护检查"""
    log("🔧 第零步：系统维护检查...")
    try:
        from system_maintenance import main as run_maintenance
        healthy, results = run_maintenance()
        log(f"    {'✅ 系统健康' if healthy else '⚠️ 发现问题'}")
        return healthy, results
    except Exception as e:
        log(f"    ⚠️ 维护检查异常: {e}")
        return True, {}


def main():
    """执行完整晚间工作流"""
    start_time = datetime.now()
    
    log("")
    log("=" * 50)
    log(f"  🌙 AutoTools 晚间工作流启动")
    log(f"  ⏰ {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 50)
    
    # 第零步：系统维护
    healthy, health_results = step0_maintenance()
    
    # 检查服务器
    log("🔍 检查服务器状态...")
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://localhost:8000/", timeout=5)
        log(f"    ✅ 本地服务器在线 (HTTP {resp.status})")
    except:
        log(f"    ⚠️ 本地服务器未运行，尝试启动...")
        import subprocess
        subprocess.Popen(
            ["python3", "app.py"],
            cwd=str(BASE_DIR),
            stdout=open("/tmp/autotools_server.log", "a"),
            stderr=subprocess.STDOUT
        )
        log(f"    🔧 服务器启动命令已执行")
    
    # 执行各步骤
    recommendations = step1_analyze_trends()
    developed = step2_develop_tools(recommendations)
    step3_generate_report()
    step4_send_email()
    step5_push_to_git()
    
    # 汇总
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    total_issues = sum(len(v) for v in health_results.values()) if health_results else 0
    
    log("")
    log("=" * 50)
    log(f"  ✅ 晚间工作流完成")
    log(f"  ⏱ 耗时: {duration:.0f}秒")
    log(f"  {'✅ 系统健康' if total_issues == 0 else f'⚠️ {total_issues} 个维护问题'}")
    log(f"  📦 新开发: {len(developed)} 个工具")
    log(f"  📧 邮件报告: 已保存/发送")
    log("=" * 50)
    log("")
    
    return {
        "status": "completed",
        "time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "new_tools": len(developed),
        "tools": [d["name"] for d in developed]
    }


if __name__ == "__main__":
    main()
