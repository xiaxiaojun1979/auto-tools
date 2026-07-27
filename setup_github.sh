#!/bin/bash
# AutoTools - GitHub 上传脚本
# 用法: bash setup_github.sh

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  上传代码到 GitHub，然后部署到 Zeabur              ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# 检查是否已经有远程仓库
if git remote -v 2>/dev/null | grep -q origin; then
    echo "✅ 已配置远程仓库"
    git remote -v
else
    echo ""
    echo "📋 第一步：创建 GitHub 仓库"
    echo "   1. 打开 https://github.com/new"
    echo "   2. 仓库名填: auto-tools"
    echo "   3. 选 Public（免费）"
    echo "   4. 不要勾选任何初始化选项"
    echo "   5. 点击 Create repository"
    echo ""
    echo "📋 第二步：连接本地代码到 GitHub"
    echo "   复制下面命令并执行："
    echo ""
    echo "   git remote add origin https://github.com/你的用户名/auto-tools.git"
    echo "   git add ."
    echo '   git commit -m "初始化 AutoTools 系统"'
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "📋 第三步：部署到 Zeabur"
    echo "   1. 打开 https://zeabur.com/zh-CN/dashboard"
    echo "   2. 点击「新建项目」"
    echo "   3. 选择「从 GitHub 部署」"
    echo "   4. 选择 auto-tools 仓库"
    echo "   5. 自动部署完成！"
    echo ""
    echo "💡 部署后 Zeabur 会分配一个 *.zeabur.app 域名"
    echo "   这就是你的产品网站地址！"
fi
