#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 AutoTools 系统维护引擎
确保系统7x24小时正常运行，自动修复常见问题
"""

import os, sys, json, shutil, socket, signal
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "daily_report"
DATA_DIR = LOG_DIR / "data"
REPORT_DIR = LOG_DIR / "reports"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
ORDERS_FILE = DATA_DIR / "orders.json"

# 维护配置
MAX_LOG_AGE_DAYS = 30        # 日志保留30天
MAX_REPORT_AGE_DAYS = 7      # 报告保留7天
MAX_DATA_FILES = 90          # 最多保留90份日数据
SERVER_PORT = 8000
CHECK_INTERVAL = 300         # 检查间隔（秒）


def log(msg):
    """记录维护日志"""
    log_file = LOG_DIR / "maintenance.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def check_server_health():
    """检查服务器健康状态"""
    log("🔍 检查Web服务器健康状态...")
    issues = []
    
    # 1. 检查端口是否在监听
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', SERVER_PORT))
        sock.close()
        
        if result == 0:
            log(f"    ✅ 端口 {SERVER_PORT} 正在监听")
        else:
            log(f"    ❌ 端口 {SERVER_PORT} 未监听")
            issues.append("server_not_listening")
    except Exception as e:
        log(f"    ❌ 端口检查异常: {e}")
        issues.append("port_check_failed")
    
    # 2. 检查HTTP响应
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{SERVER_PORT}/", timeout=5)
        if resp.status == 200:
            body = resp.read().decode('utf-8')
            log(f"    ✅ HTTP 200 OK ({len(body)} bytes)")
            # 检查产品是否正常加载
            if "card" in body:
                cards = body.count("card")
                log(f"    ✅ 产品渲染: {cards} 个卡片")
            else:
                log(f"    ⚠️ 页面可能未正确渲染产品")
                issues.append("no_products_rendered")
        else:
            log(f"    ❌ HTTP {resp.status}")
            issues.append(f"http_error_{resp.status}")
    except Exception as e:
        log(f"    ❌ HTTP请求失败: {e}")
        issues.append("http_request_failed")
    
    # 3. 检查API
    try:
        import urllib.request
        resp = urllib.request.urlopen(f"http://localhost:{SERVER_PORT}/api/stats", timeout=5)
        if resp.status == 200:
            import json
            data = json.loads(resp.read())
            log(f"    ✅ API正常: {data.get('total_orders',0)}单/¥{data.get('total_revenue',0)}")
        else:
            log(f"    ⚠️ API异常: HTTP {resp.status}")
            issues.append("api_error")
    except Exception as e:
        log(f"    ❌ API请求失败: {e}")
        issues.append("api_failed")
    
    return issues


def restart_server():
    """重启Flask服务器"""
    log("🔄 正在重启服务器...")
    
    # 杀死旧进程
    try:
        subprocess.run(["pkill", "-f", "python3.*app.py"], 
                      capture_output=True, timeout=5)
        log("    ✅ 旧进程已终止")
    except:
        pass
    
    import time
    time.sleep(2)
    
    # 启动新进程
    try:
        proc = subprocess.Popen(
            ["python3", "app.py"],
            cwd=str(BASE_DIR),
            stdout=open("/tmp/autotools_server.log", "a"),
            stderr=subprocess.STDOUT
        )
        log(f"    ✅ 服务器已启动 (PID: {proc.pid})")
        time.sleep(3)
        return True
    except Exception as e:
        log(f"    ❌ 启动失败: {e}")
        return False


def check_products_integrity():
    """检查产品数据完整性"""
    log("📦 检查产品数据完整性...")
    issues = []
    
    if not PRODUCTS_FILE.exists():
        log("    ❌ products.json 不存在！")
        return ["products_file_missing"]
    
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        if not isinstance(products, list):
            log("    ❌ products.json 格式错误")
            return ["products_format_error"]
        
        log(f"    ✅ {len(products)} 个产品")
        
        # 检查每个产品必填字段
        required_fields = ["id", "name", "price"]
        for i, p in enumerate(products):
            missing = [f for f in required_fields if f not in p]
            if missing:
                log(f"    ⚠️ 产品[{i}] {p.get('name','?')} 缺少字段: {missing}")
                issues.append(f"product_{i}_missing_{missing}")
        
        # 检查价格合理性
        invalid_prices = [p for p in products if not isinstance(p.get("price", 0), (int, float)) or p["price"] <= 0]
        if invalid_prices:
            log(f"    ⚠️ {len(invalid_prices)} 个产品价格异常")
            issues.append("invalid_prices")
        
        # 检查是否有重复ID
        ids = [p["id"] for p in products]
        dups = [i for i in ids if ids.count(i) > 1]
        if dups:
            log(f"    ❌ 重复产品ID: {set(dups)}")
            issues.append("duplicate_ids")
        else:
            log(f"    ✅ 无重复ID")
        
        # 自动修复：如果有问题，尝试修复
        if issues:
            log("    🔧 尝试自动修复产品数据...")
            # 去重
            seen_ids = set()
            unique_products = []
            for p in products:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    unique_products.append(p)
            
            if len(unique_products) != len(products):
                log(f"    ✅ 已修复重复ID: {len(products)} -> {len(unique_products)}")
                with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(unique_products, f, ensure_ascii=False, indent=2)
                issues = [i for i in issues if "duplicate" not in i]
        
    except json.JSONDecodeError as e:
        log(f"    ❌ products.json JSON解析失败: {e}")
        issues.append("products_json_decode_error")
    except Exception as e:
        log(f"    ❌ 产品检查异常: {e}")
        issues.append("products_check_exception")
    
    return issues


def check_orders_integrity():
    """检查订单数据完整性"""
    log("📋 检查订单数据完整性...")
    issues = []
    
    if not ORDERS_FILE.exists():
        log("    ⚠️ orders.json 不存在，将创建空文件")
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"orders": [], "total_revenue": 0}, f, ensure_ascii=False, indent=2)
            log("    ✅ 已创建空订单文件")
        except Exception as e:
            log(f"    ❌ 创建失败: {e}")
            issues.append("orders_create_failed")
        return issues
    
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "orders" not in data or "total_revenue" not in data:
            log("    ❌ orders.json 结构错误")
            issues.append("orders_format_error")
            return issues
        
        orders = data["orders"]
        log(f"    ✅ {len(orders)} 笔订单, 累计收入: ¥{data['total_revenue']}")
        
        # 验证累计收入是否匹配
        calc_revenue = sum(o.get("price", 0) for o in orders)
        if abs(calc_revenue - data["total_revenue"]) > 0.01:
            log(f"    ⚠️ 收入不一致: 累计={data['total_revenue']}, 实际计算={calc_revenue}")
            data["total_revenue"] = calc_revenue
            with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log(f"    ✅ 已自动修复收入: ¥{calc_revenue}")
            issues.append("revenue_fixed")
        
        # 检查待处理订单
        pending = [o for o in orders if o.get("status") == "pending"]
        if pending:
            log(f"    ⚠️ 有 {len(pending)} 笔待处理订单！")
            for o in pending:
                log(f"       {o['order_id']}: {o['product_name']} ¥{o['price']}")
            issues.append(f"pending_orders_{len(pending)}")
        else:
            log(f"    ✅ 无待处理订单")
        
    except json.JSONDecodeError as e:
        log(f"    ❌ orders.json JSON解析失败: {e}")
        issues.append("orders_json_decode_error")
    except Exception as e:
        log(f"    ❌ 订单检查异常: {e}")
        issues.append("orders_check_exception")
    
    return issues


def check_launchagents():
    """检查LaunchAgent定时任务状态"""
    log("⏰ 检查LaunchAgent定时任务...")
    issues = []
    
    agents = [
        "com.auto.daily",
        "com.auto.evening",
        "com.auto.flask",
        "com.auto.optimizer"
    ]
    
    for agent in agents:
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{agent}.plist"
        if plist_path.exists():
            # 检查是否已加载
            result = subprocess.run(
                ["launchctl", "list", agent],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                log(f"    ✅ {agent} 已加载")
            else:
                log(f"    ⚠️ {agent} 未加载，尝试重新加载...")
                subprocess.run(["launchctl", "load", str(plist_path)], 
                             capture_output=True, timeout=5)
                log(f"    ✅ {agent} 已重新加载")
                issues.append(f"{agent}_reloaded")
        else:
            log(f"    ⚠️ {agent}.plist 不存在")
            issues.append(f"{agent}_plist_missing")
    
    return issues


def cleanup_old_files():
    """清理旧文件，释放空间"""
    log("🧹 清理旧文件...")
    
    # 清理旧报告 (>7天)
    if REPORT_DIR.exists():
        cutoff = datetime.now() - timedelta(days=MAX_REPORT_AGE_DAYS)
        deleted = 0
        for f in REPORT_DIR.iterdir():
            if f.suffix in ('.html', '.json'):
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    deleted += 1
        log(f"    ✅ 清理旧报告: {deleted} 个")
    
    # 清理旧日数据 (>90份)
    if DATA_DIR.exists():
        files = sorted(DATA_DIR.glob("daily_*.json"), reverse=True)
        if len(files) > MAX_DATA_FILES:
            for f in files[MAX_DATA_FILES:]:
                f.unlink()
            log(f"    ✅ 清理旧日数据: {len(files) - MAX_DATA_FILES} 个")
    
    # 清理维护日志 (>500行)
    log_file = LOG_DIR / "maintenance.log"
    if log_file.exists():
        lines = log_file.read_text().splitlines()
        if len(lines) > 500:
            with open(log_file, 'w') as f:
                f.write("\n".join(lines[-400:]) + "\n")
            log(f"    ✅ 维护日志已截断: {len(lines)} -> 400 行")
    
    # 清理系统日志（如果太大）
    for log_name in ["/tmp/autotools_server.log", "/tmp/auto_daily.log", "/tmp/auto_daily_err.log"]:
        log_path = Path(log_name)
        if log_path.exists() and log_path.stat().st_size > 5 * 1024 * 1024:  # 5MB
            log_path.write_text("")
            log(f"    ✅ 已清空 {log_name} (超过5MB)")
    
    return True


def check_disk_space():
    """检查磁盘空间"""
    log("💾 检查磁盘空间...")
    issues = []
    
    try:
        stat = shutil.disk_usage(str(BASE_DIR))
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_pct = stat.used / stat.total * 100
        
        log(f"    💿 总空间: {total_gb:.1f}GB, 已用: {used_pct:.1f}%, 剩余: {free_gb:.1f}GB")
        
        if free_gb < 1:
            log(f"    ❌ 磁盘空间不足! 仅剩 {free_gb:.1f}GB")
            issues.append("low_disk_space")
            # 强制清理
            cleanup_old_files()
        elif free_gb < 5:
            log(f"    ⚠️ 磁盘空间低于5GB")
            issues.append("low_disk_space_warning")
        else:
            log(f"    ✅ 磁盘空间充足")
    except Exception as e:
        log(f"    ❌ 磁盘检查失败: {e}")
        issues.append("disk_check_failed")
    
    return issues


def check_network():
    """检查网络连通性"""
    log("🌐 检查网络连通性...")
    issues = []
    
    targets = [
        ("github.com", 443),
        ("api.github.com", 443),
    ]
    
    for host, port in targets:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                log(f"    ✅ {host}:{port} 可达")
            else:
                log(f"    ⚠️ {host}:{port} 不可达")
                issues.append(f"{host}_unreachable")
        except Exception as e:
            log(f"    ⚠️ {host}:{port} 检查失败: {e}")
    
    return issues


def generate_maintenance_report(health_results):
    """生成维护报告HTML"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    
    issues = []
    for key, items in health_results.items():
        if items:
            for item in items:
                issues.append("{}: {}".format(key, item))
    
    issue_count = len(issues)
    
    # Build issue section
    if issue_count > 0:
        issue_items = ""
        for i in issues:
            issue_items += "<div class=\"item\" style='color:#ff4d4f'>\u2022 {}</div>".format(i)
        issue_section = "<div class=\"section\"><h2>\u26a0\ufe0f 发现 {} 个问题</h2>{}</div>".format(issue_count, issue_items)
    else:
        issue_section = ""
    
    # Build maintenance time string
    maint_time = "自动执行"
    
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>""" + "系统维护报告" + """ - """ + today + """</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f5f7fa; color:#1a1a2e; padding:20px; }}
.container {{ max-width:800px; margin:0 auto; }}
.header {{ background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:30px; border-radius:16px; margin-bottom:20px; text-align:center; }}
.header h1 {{ font-size:1.5em; }}
.section {{ background:white; border-radius:12px; padding:20px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,0.05); }}
.section h2 {{ font-size:1.1em; margin-bottom:12px; border-bottom:2px solid #f0f0f0; padding-bottom:8px; }}
.status-ok {{ color:#52c41a; }}
.status-warn {{ color:#fa8c16; }}
.status-err {{ color:#ff4d4f; }}
.item {{ padding:6px 0; font-size:0.9em; border-bottom:1px solid #fafafa; }}
.footer {{ text-align:center; color:#999; font-size:0.8em; padding:16px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>\U0001f527 系统维护报告</h1>
    <div style="opacity:0.85;font-size:0.9em">""" + now + """ \u00b7 """ + ("\u2705 系统健康" if issue_count == 0 else "\u26a0\ufe0f {} 个问题".format(issue_count)) + """</div>
  </div>
  
  <div class="section">
    <h2>\U0001f5a5\ufe0f Web服务器</h2>
    <div class="item">""" + ("\u2705 运行正常" if 'server_not_listening' not in str(issues) and 'http_request_failed' not in str(issues) else "\u274c 异常") + """</div>
  </div>
  
  <div class="section">
    <h2>\U0001f4e6 产品数据</h2>
    <div class="item">""" + ("\u2705 数据完整" if 'products_file_missing' not in str(issues) and 'products_format_error' not in str(issues) else "\u274c 数据异常") + """</div>
  </div>
  
  <div class="section">
    <h2>\U0001f4cb 订单数据</h2>
    <div class="item">""" + ("\u2705 数据完整" if 'orders_format_error' not in str(issues) else "\u274c 数据异常") + """</div>
  </div>
  
  <div class="section">
    <h2>\u23f0 定时任务</h2>
    <div class="item">""" + ("\u2705 已加载" if 'plist_missing' not in str(issues) else "\u26a0\ufe0f 部分任务未加载") + """</div>
  </div>
  
  <div class="section">
    <h2>\U0001f4be 磁盘空间</h2>
    <div class="item">""" + ("\u2705 空间充足" if 'low_disk_space' not in str(issues) else "\u274c 磁盘空间不足") + """</div>
  </div>

  """ + issue_section + """
  
  <div class="section">
    <h2>\U0001f517 快捷操作</h2>
    <div class="item"><a href="http://localhost:8000/admin" style="color:#667eea">\U0001f4cb 管理后台</a></div>
    <div class="item"><a href="http://localhost:8000/admin/revenue" style="color:#667eea">\U0001f4b0 收益看板</a></div>
    <div class="item"><a href="http://localhost:8000/admin/reports" style="color:#667eea">\U0001f4ca 历史报告</a></div>
  </div>
  
  <div class="footer">
    AutoTools 系统维护 \u00b7 7x24小时自动运行<br>
    维护间隔: 每天4次(8:00/12:00/18:00/23:00)
  </div>
</div>
</body>
</html>""" 
    
    report_path = REPORT_DIR / "maintenance_{}.html".format(today)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_path

def main():
    """执行完整系统维护"""
    start_time = datetime.now()
    
    log("")
    log("=" * 50)
    log(f"  🔧 AutoTools 系统维护")
    log(f"  ⏰ {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 50)
    
    results = {}
    
    # 按顺序执行各项检查
    results["server"] = check_server_health()
    
    # 如果服务器有问题，自动重启
    if any("not_listening" in str(i) or "failed" in str(i) for i in results["server"]):
        log("⚠️ 服务器异常，尝试自动重启...")
        restart_server()
        # 重启后再次检查
        results["server_retry"] = check_server_health()
    
    results["products"] = check_products_integrity()
    results["orders"] = check_orders_integrity()
    results["launchagents"] = check_launchagents()
    results["disk"] = check_disk_space()
    results["network"] = check_network()
    
    # 清理
    cleanup_old_files()
    
    # 生成报告
    report_path = generate_maintenance_report(results)
    
    # 统计
    total_issues = sum(len(v) for v in results.values())
    
    log("")
    log("=" * 50)
    log(f"  ✅ 系统维护完成")
    log(f"  ⏱ 耗时: {(datetime.now()-start_time).total_seconds():.0f}秒")
    log(f"  {'✅ 系统健康' if total_issues == 0 else f'⚠️ {total_issues} 个问题'}")
    log(f"  📄 报告: {report_path}")
    log("=" * 50)
    log("")
    
    return total_issues == 0, results


def run_watchdog():
    """看门狗模式 - 持续监控"""
    log("🐕 启动看门狗监控模式...")
    
    check_interval = CHECK_INTERVAL
    max_checks = 288  # 最多运行24小时（5分钟一次）
    
    for i in range(max_checks):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # 快速健康检查
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', SERVER_PORT))
            sock.close()
            
            if result != 0:
                log(f"⚠️ 服务器离线! 自动重启 (检查#{i+1})")
                restart_server()
            
            # 每6次检查（30分钟）做一次完整维护
            if i % 6 == 0:
                log(f"📋 执行定期维护检查...")
                main()
            
        except Exception as e:
            log(f"❌ 看门狗异常: {e}")
        
        import time
        time.sleep(check_interval)
    
    log("⏹️ 看门狗超时停止")


if __name__ == "__main__":
    if "--watchdog" in sys.argv:
        run_watchdog()
    elif "--watchdog-quick" in sys.argv:
        # 快速看门狗 - 只检查服务器
        import socket, subprocess
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        if result != 0:
            subprocess.run(['pkill', '-f', 'python3.*app.py'], capture_output=True)
            subprocess.Popen(['python3', 'app.py'], cwd=str(BASE_DIR),
                           stdout=open('/tmp/autotools_server.log','a'), stderr=subprocess.STDOUT)
            print(f'Watchdog: Server restarted')
        else:
            pass
    else:
        main()
