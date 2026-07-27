# 🚀 AutoTools 自动化工具集 - 在线销售系统

## 📦 一键部署（3分钟上线）

### 方式一：Railway.app（推荐，国际通用）

1. **注册 GitHub** → https://github.com/signup （5分钟）
2. **上传代码** → 创建新仓库，上传本文件夹所有文件
3. **部署** → 打开 https://railway.app ，用 GitHub 登录
   - 点击 "New Project" → "Deploy from GitHub repo"
   - 选择刚创建的仓库
   - Railway 自动检测并部署 ✅
   - 部署后点击 "Generate Domain" 获得公网地址

### 方式二：Zeabur（适合国内用户，支持支付宝登录）

1. 打开 https://zeabur.com 注册
2. 创建项目 → 选择 GitHub 部署
3. 选择本仓库代码
4. 自动部署完成 ✅

## ✅ 部署后

部署成功后，系统会自动运行在：

| 页面 | 地址 |
|------|------|
| 🛒 产品网站 | `https://你的域名/` |
| 📋 订单管理 | `https://你的域名/admin` |
| 📝 下单页面 | `https://你的域名/order` |

## 💳 收款设置

部署到线上后，把产品网站的地址发给买家：

- **支付宝账号**: 15156215580
- **微信收款码**: 见 website/assets/wechat_pay.jpg

买家付款后，去 `/admin` 确认收款即可。

## 🔧 本地开发

```bash
python3 delivery/order_server.py
```

访问 http://localhost:8080
