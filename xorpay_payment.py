#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""虎皮椒 XorPay 支付模块 - 个人开发者无需营业执照
文档: https://xorpay.com/doc
- 创建支付: POST https://xorpay.com/api/pay/{aid}
- 查询订单: GET  https://xorpay.com/api/query2/{aid}?order_id=XXX&sign=XXX
- 回调通知: POST notify_url
"""
import json, hashlib, logging, urllib.request, urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "xorpay_config.json"

logger = logging.getLogger("xorpay")

def load_config():
    """加载虎皮椒配置"""
    config = {
        "aid": "",
        "app_secret": "",
        "configured": False
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                saved = json.load(f)
            config.update(saved)
            config["configured"] = bool(config.get("aid") and config.get("app_secret"))
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    return config

def save_config(aid, app_secret):
    """保存虎皮椒配置"""
    config = {"aid": aid, "app_secret": app_secret, "configured": True}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return config

def _sign(*parts):
    """签名: 按参数顺序拼接后MD5"""
    raw = "".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest().lower()

def _post(url, data):
    """POST表单请求"""
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "AutoTools/1.0"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _get(url):
    """GET请求"""
    req = urllib.request.Request(url, headers={"User-Agent": "AutoTools/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def create_qrcode(amount, order_id, subject="商品", notify_url=None, order_uid="", more=""):
    """创建扫码支付二维码 (pay_type: alipay/wechat)"""
    try:
        cfg = load_config()
        if not cfg.get("configured"):
            return {"ok": False, "msg": "虎皮椒未配置，请在后台填写 aid 和 app_secret"}

        aid = cfg["aid"]
        secret = cfg["app_secret"]
        pay_type = "alipay"
        price = f"{float(amount):.2f}"

        if not notify_url:
            notify_url = "http://118.31.4.27/api/xorpay/notify"

        sign = _sign(subject, pay_type, price, order_id, notify_url, secret)

        data = {
            "name": subject,
            "pay_type": pay_type,
            "price": price,
            "order_id": order_id,
            "notify_url": notify_url,
            "sign": sign,
            "expire": "1800"
        }
        if order_uid:
            data["order_uid"] = order_uid
        if more:
            data["more"] = more

        result = _post(f"https://xorpay.com/api/pay/{aid}", data)

        if result.get("status") == "ok":
            qr_url = result.get("info", {}).get("qr", "")
            return {
                "ok": True,
                "qrcode": qr_url,
                "aoid": result.get("aoid", ""),
                "msg": "success"
            }
        else:
            status = result.get("status", "unknown")
            info = result.get("info", {})
            msg = f"虎皮椒错误: {status}"
            if isinstance(info, dict) and info.get("qr") == "ACCESS_FORBIDDEN":
                msg = "需要去支付宝邮件中完成签约"
            elif isinstance(info, str):
                msg = f"虎皮椒错误: {status} - {info}"
            logger.error(msg)
            return {"ok": False, "msg": msg, "status": status}
    except Exception as e:
        logger.exception("create_qrcode异常")
        return {"ok": False, "msg": str(e)}

def query_payment(order_id):
    """查询订单支付状态"""
    try:
        cfg = load_config()
        if not cfg.get("configured"):
            return {"ok": False, "paid": False, "msg": "虎皮椒未配置"}

        aid = cfg["aid"]
        secret = cfg["app_secret"]
        sign = _sign(order_id, secret)

        result = _get(f"https://xorpay.com/api/query2/{aid}?order_id={urllib.parse.quote(order_id)}&sign={sign}")

        status = result.get("status", "not_exist")
        paid = status in ("payed", "success")
        return {
            "ok": True,
            "paid": paid,
            "status": status,
            "msg": "已支付" if paid else "未支付"
        }
    except Exception as e:
        logger.exception("query_payment异常")
        return {"ok": False, "paid": False, "msg": str(e)}

def verify_notify(data):
    """验证回调通知签名"""
    try:
        cfg = load_config()
        if not cfg.get("configured"):
            return False

        sign = data.pop("sign", "")
        expected = _sign(
            data.get("aoid", ""),
            data.get("order_id", ""),
            str(data.get("pay_price", "")),
            data.get("pay_time", ""),
            cfg["app_secret"]
        )
        return sign == expected
    except Exception as e:
        logger.exception("verify_notify异常")
        return False
