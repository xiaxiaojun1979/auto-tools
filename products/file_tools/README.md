# 📁 文件批处理大师 v1.0

一键搞定批量重命名、图片压缩、格式转换、重复文件查找。

## 快速开始

```bash
# 安装依赖
pip3 install pillow

# 批量重命名（编号模式）
python3 main.py rename ./文件夹 --pattern number --prefix "项目_" --start 1

# 批量压缩图片
python3 main.py compress ./图片文件夹 --quality 80

# 查找重复文件
python3 main.py dupes ./文件夹

# 批量转换格式
python3 main.py convert ./图片文件夹 --format webp
```

## 功能列表

| 功能 | 命令 | 说明 |
|------|------|------|
| 批量重命名 | rename | 6种模式：前缀/编号/日期/大小写/替换 |
| 图片压缩 | compress | 可调质量，多线程并行处理 |
| 查找重复 | dupes | SHA-256哈希比对，精准查重 |
| 格式转换 | convert | 图片格式互转，支持递归子目录 |

## 系统要求

- Python 3.6+
- macOS / Linux / Windows

## 文件说明

- `main.py` - 主程序（可独立运行）
- `README.md` - 本文件
- `examples/` - 使用示例

## 许可证

购买后获得永久个人使用授权。
