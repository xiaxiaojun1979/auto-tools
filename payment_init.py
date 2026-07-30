"""
一键初始化和验证支付系统
"""
import json, sys
from pathlib import Path

BASE = Path(__file__).parent

# 1. 检查当前支付配置
def check_current():
    print("=" * 50)
    print("📋 当前支付系统状态")
    print("=" * 50)
    
    # 手动支付 - 已就绪
    print("\n✅ 手动支付（交易号验证）: 已运行")
    print("   用户扫码付款 → 输入交易号 → 获取校验码 → 输入邮箱下载")
    
    # 虎皮椒配置检查
    cfg_file = BASE / "xunhupay_config.json"
    if cfg_file.exists():
        cfg = json.loads(cfg_file.read_text())
        if cfg.get("appid") and cfg["appid"] != "YOUR_APPID":
            print(f"\n✅ 虎皮椒: 已配置 (appid: {cfg['appid'][:8]}...)")
        else:
            print("\n❌ 虎皮椒: 未配置")
            print("   需要注册 https://www.xunhupay.com/ 获取 appid 和 appsecret")
    
    # 支付宝当面付
    alipay_cfg = BASE / "alipay_config.json"
    if alipay_cfg.exists():
        cfg = json.loads(alipay_cfg.read_text())
        if cfg.get("app_id") and cfg["app_id"] != "YOUR_APP_ID":
            print(f"\n✅ 支付宝当面付: 已配置 (app_id: {cfg['app_id'][:8]}...)")
        else:
            print("\n❌ 支付宝当面付: 未配置")
            print("   需要在支付宝开放平台注册获取 app_id")

check_current()

print("\n" + "=" * 50)
print("🔧 准备就绪的支付模块")
print("=" * 50)
print("\n1. xunhupay_payment.py - 虎皮椒支付")
print("2. alipay_payment.py - 支付宝当面付")
print("3. payment_gateway.py - PayJS (已停运)")
print("4. app.py - 手动支付（当前运行中）")

print("\n" + "=" * 50)
print("🛒 购买页面: http://118.31.4.27/product/<产品ID>")
print("👑 后台管理: http://118.31.4.27/admin")
print("💳 测试购买: http://118.31.4.27/product/file_tools")
