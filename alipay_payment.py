"""
支付宝当面付集成模块
使用 alipay.trade.precreate API 生成二维码
"""
import json, os, time, logging
from pathlib import Path
from alipay import AliPay, AliPayConfig

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "alipay_config.json"

# App 通知回调地址（必须配置在支付宝开放平台）
NOTIFY_URL = "https://xiaxiaojun.com/api/alipay/notify"

def load_config():
    """加载支付宝配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        # 如果仅配置了gateway=alipay但无app_id，视为未完成配置
        if not cfg.get("app_id") or cfg["app_id"] == "YOUR_APP_ID":
            return {"configured": False, "reason": "未配置app_id，请先在支付宝开放平台注册"}
        return {**cfg, "configured": True}
    return {"configured": False, "reason": "配置文件不存在"}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_alipay_client(config=None):
    """获取支付宝SDK客户端"""
    if config is None:
        config = load_config()
    if not config.get("configured"):
        return None
    
    app_private_key_str = config.get("app_private_key", "")
    alipay_public_key_str = config.get("alipay_public_key", "")
    
    # 处理换行
    app_private_key_str = app_private_key_str.replace("\\n", "\n")
    alipay_public_key_str = alipay_public_key_str.replace("\\n", "\n")
    
    return AliPay(
        appid=config["app_id"],
        app_notify_url=None,  # 使用notify_url参数
        app_private_key_string=app_private_key_str,
        alipay_public_key_string=alipay_public_key_str,
        sign_type="RSA2",
        debug=False
    )

def create_qrcode(amount, out_trade_no, subject="AutoTools工具包"):
    """
    创建支付宝当面付二维码
    返回: {ok, qrcode, out_trade_no, msg}
    """
    config = load_config()
    if not config.get("configured"):
        return {"ok": False, "msg": config.get("reason", "支付宝未配置")}
    
    alipay = get_alipay_client(config)
    if not alipay:
        return {"ok": False, "msg": "支付宝客户端初始化失败"}
    
    # 单位转换：元转分
    total_amount = float(amount)
    
    try:
        # 调用 alipay.trade.precreate（扫码支付）
        result = alipay.api_alipay_trade_precreate(
            subject=subject,
            out_trade_no=out_trade_no,
            total_amount=total_amount,
            timeout_express="30m",  # 30分钟过期
            notify_url=config.get("notify_url", NOTIFY_URL)
        )
        
        if result.get("code") == "10000":  # 成功
            qr_code = result.get("qr_code", "")
            return {
                "ok": True,
                "qrcode": qr_code,
                "out_trade_no": out_trade_no,
                "trade_no": result.get("trade_no", ""),
                "msg": "success"
            }
        else:
            return {
                "ok": False,
                "msg": f"支付宝错误: {result.get('sub_msg', result.get('msg', '未知错误'))}",
                "code": result.get("code", ""),
                "sub_code": result.get("sub_code", "")
            }
    except Exception as e:
        return {"ok": False, "msg": f"支付宝接口异常: {str(e)}"}

def query_payment(out_trade_no):
    """
    查询支付状态
    返回: {ok, status, trade_no, buyer_id, msg}
    """
    config = load_config()
    if not config.get("configured"):
        return {"ok": False, "status": "error", "msg": "支付宝未配置"}
    
    alipay = get_alipay_client(config)
    if not alipay:
        return {"ok": False, "status": "error", "msg": "客户端初始化失败"}
    
    try:
        result = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
        
        if result.get("code") == "10000":
            trade_status = result.get("trade_status", "")
            is_paid = trade_status == "TRADE_SUCCESS"
            return {
                "ok": True,
                "status": "paid" if is_paid else "unpaid",
                "paid": is_paid,
                "trade_no": result.get("trade_no", ""),
                "buyer_id": result.get("buyer_user_id", ""),
                "buyer_logon_id": result.get("buyer_logon_id", ""),
                "total_amount": result.get("total_amount", "0"),
                "receipt_amount": result.get("receipt_amount", "0"),
                "msg": "成功"
            }
        else:
            return {"ok": True, "status": "unpaid", "paid": False, "msg": result.get("sub_msg", "未支付")}
    except Exception as e:
        return {"ok": False, "status": "error", "msg": str(e)}

def verify_notify(data):
    """
    验证支付宝异步通知的签名
    返回: bool
    """
    config = load_config()
    if not config.get("configured"):
        return False
    
    alipay = get_alipay_client(config)
    if not alipay:
        return False
    
    try:
        # data 是支付宝POST过来的dict
        signature = data.pop("sign", "")
        return alipay.verify(signature, data)
    except Exception as e:
        print(f"  ⚠️ 通知验签失败: {e}")
        return False

def generate_keys():
    """
    生成RSA密钥对（用于在支付宝开放平台配置）
    返回: {private_key, public_key}
    """
    from Crypto.PublicKey import RSA
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')
    return {"private_key": private_key, "public_key": public_key}

# === 测试函数 ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "gen_keys":
        keys = generate_keys()
        print("=== 应用私钥（保存到 alipay_config.json）===")
        print(keys["private_key"])
        print("\n=== 应用公钥（配置到支付宝开放平台）===")
        print(keys["public_key"])
    else:
        print("支付宝当面付模块已加载")
        print(f"配置路径: {CONFIG_FILE}")
        if CONFIG_FILE.exists():
            cfg = load_config()
            if cfg.get("configured"):
                print("✅ 支付宝已配置")
            else:
                print(f"⚠️ 支付宝未完成配置: {cfg.get('reason', '未知')}")
