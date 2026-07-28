"""
支付网关集成模块
支持：PayJS (payjs.cn)
配置：在 payment_config.json 中设置商户号 + 密钥
"""

import json, hashlib, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CONFIG_FILE = Path(__file__).parent / "payment_config.json"
PAYJS_API_NATIVE = "https://payjs.cn/api/native"
PAYJS_API_CHECK = "https://payjs.cn/api/check"
PAYJS_API_CLOSE = "https://payjs.cn/api/close"

def load_config():
    """加载支付网关配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"gateway": "none", "payjs_mchid": "", "payjs_key": "", "notify_url": ""}

def save_config(data):
    """保存支付网关配置"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_sign(params, key):
    """PayJS 签名算法"""
    # 按参数名排序
    keys = sorted(params.keys())
    pairs = []
    for k in keys:
        v = params[k]
        if v != '' and v is not None:
            pairs.append(f"{k}={v}")
    pairs.append(f"key={key}")
    sign_str = "&".join(pairs)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

def create_native_qrcode(total_fee, out_trade_no, attach=""):
    """
    创建 PayJS 原生支付二维码
    返回: {ok, qrcode_url, payjs_order_id, msg}
    """
    config = load_config()
    if config.get("gateway") != "payjs" or not config.get("payjs_mchid"):
        return {"ok": False, "msg": "支付网关未配置"}
    
    params = {
        "mchid": config["payjs_mchid"],
        "total_fee": int(total_fee * 100),  # 单位:分
        "out_trade_no": out_trade_no,
        "notify_url": config.get("notify_url", ""),
        "attach": attach
    }
    
    sign = get_sign(params, config["payjs_key"])
    params["sign"] = sign
    
    try:
        data = urlencode(params).encode('utf-8')
        req = Request(PAYJS_API_NATIVE, data=data)
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))
        
        if result.get("return_code") == 1:
            return {
                "ok": True,
                "qrcode_url": result.get("qrcode", ""),
                "payjs_order_id": result.get("payjs_order_id", ""),
                "out_trade_no": out_trade_no,
                "msg": "success"
            }
        else:
            return {"ok": False, "msg": result.get("return_msg", "创建订单失败")}
    except Exception as e:
        return {"ok": False, "msg": f"支付网关异常: {str(e)}"}

def check_payment(payjs_order_id):
    """
    查询支付状态
    返回: {ok, status: "paid" | "unpaid" | "closed", msg}
    """
    config = load_config()
    if config.get("gateway") != "payjs" or not config.get("payjs_mchid"):
        return {"ok": False, "status": "error", "msg": "支付网关未配置"}
    
    params = {
        "payjs_order_id": payjs_order_id,
        "mchid": config["payjs_mchid"]
    }
    
    sign = get_sign(params, config["payjs_key"])
    params["sign"] = sign
    
    try:
        data = urlencode(params).encode('utf-8')
        req = Request(PAYJS_API_CHECK, data=data)
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))
        
        if result.get("return_code") == 1:
            status = "paid" if result.get("status") == 1 else "unpaid"
            return {
                "ok": True,
                "status": status,
                "paid": result.get("status") == 1,
                "openid": result.get("openid", ""),
                "msg": result.get("return_msg", "")
            }
        else:
            return {"ok": False, "status": "error", "msg": result.get("return_msg", "查询失败")}
    except Exception as e:
        return {"ok": False, "status": "error", "msg": str(e)}
