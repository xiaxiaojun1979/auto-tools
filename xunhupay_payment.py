"""
虎皮椒 (xunhupay) 支付集成模块
官网: https://www.xunhupay.com/
API文档: https://www.xunhupay.com/doc/api/pay.html
"""
import json, hashlib, time, random, string, logging
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "xunhupay_config.json"

# API地址
API_URL = "https://api.xunhupay.com/payment/do.html"

def load_config():
    """加载虎皮椒配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        if not cfg.get("appid") or cfg["appid"] == "YOUR_APPID":
            return {"configured": False, "reason": "未配置appid"}
        return {**cfg, "configured": True}
    return {"configured": False, "reason": "配置文件不存在"}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_nonce_str(length=16):
    """生成随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def md5_sign(params, appsecret):
    """
    虎皮椒签名算法
    1. 按参数名排序
    2. 拼接 key=value&key=value&appsecret=SECRET
    3. MD5加密转小写
    """
    keys = sorted(params.keys())
    pairs = []
    for k in keys:
        v = params[k]
        if v != '' and v is not None and k != 'hash':
            pairs.append(f"{k}={v}")
    pairs.append(f"appsecret={appsecret}")
    sign_str = "&".join(pairs)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

def create_payment(amount, trade_order_id, title, notify_url, return_url=""):
    """
    创建付款订单
    返回: {ok, url, order_id, msg}
    """
    config = load_config()
    if not config.get("configured"):
        return {"ok": False, "msg": config.get("reason", "虎皮椒未配置")}
    
    appid = config["appid"]
    appsecret = config["appsecret"]
    
    params = {
        "version": "1.1",
        "appid": appid,
        "trade_order_id": trade_order_id,
        "total_fee": str(amount),
        "title": title,
        "time": str(int(time.time())),
        "notify_url": notify_url,
        "return_url": return_url or notify_url,
        "nonce_str": generate_nonce_str(),
        "attach": "autotools"
    }
    
    # 生成签名
    sign = md5_sign(params, appsecret)
    params["hash"] = sign
    
    try:
        data = json.dumps(params).encode('utf-8')
        req = Request(API_URL, data=data, headers={"Content-Type": "application/json"})
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))
        
        if result.get("errcode") == 0:
            return {
                "ok": True,
                "url": result.get("url", ""),  # 支付链接
                "order_id": result.get("order_id", ""),
                "trade_order_id": trade_order_id,
                "msg": "success"
            }
        else:
            return {"ok": False, "msg": f"虎皮椒错误: {result.get('errmsg', '未知错误')}"}
    except Exception as e:
        return {"ok": False, "msg": f"支付接口异常: {str(e)}"}

def verify_notify(data):
    """
    验证支付回调通知
    返回: (ok, order_id, total_fee, trade_order_id)
    """
    config = load_config()
    if not config.get("configured"):
        return False, None, None, None
    
    appsecret = config["appsecret"]
    
    # 验证签名
    sign = data.pop("hash", "")
    if not sign:
        return False, None, None, None
    
    expected_sign = md5_sign(data, appsecret)
    if sign.lower() != expected_sign.lower():
        return False, None, None, None
    
    # 验证订单状态
    status = data.get("status", "")
    if status == "OD":  # 支付成功
        return (
            True,
            data.get("order_id", ""),
            data.get("total_fee", ""),
            data.get("trade_order_id", "")
        )
    
    return False, None, None, None

# ===== 测试 =====
if __name__ == "__main__":
    import sys
    cfg = load_config()
    if cfg.get("configured"):
        print(f"✅ 虎皮椒已配置 (appid: {cfg['appid'][:8]}...)")
    else:
        print(f"⚠️ {cfg.get('reason', '未配置')}")
        print("请在 xunhupay_config.json 中配置 appid 和 appsecret")
