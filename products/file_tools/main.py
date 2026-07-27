#!/usr/bin/env python3
"""
文件批处理大师 (File Batch Processing Toolkit)
Author: AutoTools Studio
Version: 1.0.0
一键搞定批量重命名、图片压缩、格式转换、重复文件查找
"""

import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[!] 建议安装 Pillow 以使用图片处理功能: pip3 install pillow")


class FileBatchProcessor:
    """核心处理器"""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.stats = {"processed": 0, "skipped": 0, "errors": 0}

    def log(self, msg):
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    # ========== 功能1: 批量重命名 ==========
    def batch_rename(self, directory, pattern, prefix="", suffix="",
                     start_num=1, digits=3, replace_old="", replace_new="",
                     extensions=None, dry_run=False):
        """批量重命名文件"""
        folder = Path(directory)
        if not folder.exists():
            print(f"[X] 目录不存在: {directory}")
            return

        files = self._get_files(folder, extensions)
        if not files:
            print("[!] 没有找到匹配的文件")
            return

        self.log(f"找到 {len(files)} 个文件，开始重命名...")

        for i, f in enumerate(files):
            old_name = f.name
            stem = f.stem
            ext = f.suffix

            # 应用替换
            if replace_old:
                stem = stem.replace(replace_old, replace_new)

            # 应用模式
            if pattern == "prefix":
                new_name = f"{prefix}{stem}{suffix}{ext}"
            elif pattern == "number":
                new_name = f"{prefix}{str(start_num + i).zfill(digits)}{suffix}{ext}"
            elif pattern == "date":
                date_str = datetime.now().strftime("%Y%m%d")
                new_name = f"{prefix}{date_str}_{str(i+1).zfill(digits)}{suffix}{ext}"
            elif pattern == "lower":
                new_name = f"{prefix}{stem.lower()}{suffix}{ext}"
            elif pattern == "upper":
                new_name = f"{prefix}{stem.upper()}{suffix}{ext}"
            elif pattern == "regex_replace":
                new_name = f"{prefix}{stem}{suffix}{ext}"
            else:
                new_name = f"{prefix}{stem}{suffix}{ext}"

            new_path = f.parent / new_name

            if dry_run:
                print(f"  [模拟] {old_name} → {new_name}")
            else:
                try:
                    f.rename(new_path)
                    print(f"  [OK] {old_name} → {new_name}")
                    self.stats["processed"] += 1
                except Exception as e:
                    print(f"  [X] {old_name} → 失败: {e}")
                    self.stats["errors"] += 1

        return self.stats

    # ========== 功能2: 图片批量压缩 ==========
    def compress_images(self, directory, quality=80, max_size=None,
                        output_dir=None, max_workers=4):
        """批量压缩图片"""
        if not HAS_PIL:
            print("[X] 需要安装 Pillow: pip3 install pillow")
            return

        folder = Path(directory)
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        images = [f for f in folder.iterdir()
                  if f.is_file() and f.suffix.lower() in image_exts]

        if not images:
            print("[!] 没有找到图片文件")
            return

        out_dir = Path(output_dir) if output_dir else folder / "compressed"
        out_dir.mkdir(exist_ok=True)

        self.log(f"找到 {len(images)} 张图片，质量={quality}，开始压缩...")

        total_in = 0
        total_out = 0

        def compress_one(img_path):
            try:
                in_size = img_path.stat().st_size
                img = Image.open(img_path)
                # 保持EXIF方向
                img = ImageOps.exif_transpose(img)
                # 调整尺寸
                if max_size:
                    img.thumbnail((max_size, max_size), Image.LANCZOS)
                # 确定输出格式
                ext = img_path.suffix.lower()
                out_path = out_dir / img_path.name

                if ext in ('.jpg', '.jpeg'):
                    img.save(out_path, 'JPEG', quality=quality, optimize=True)
                elif ext == '.png':
                    img.save(out_path, 'PNG', optimize=True)
                elif ext == '.webp':
                    img.save(out_path, 'WEBP', quality=quality)
                else:
                    out_path = out_dir / f"{img_path.stem}.jpg"
                    img.save(out_path, 'JPEG', quality=quality, optimize=True)

                out_size = out_path.stat().st_size
                ratio = (1 - out_size / in_size) * 100
                return (img_path.name, in_size, out_size, ratio, None)
            except Exception as e:
                return (img_path.name, 0, 0, 0, str(e))

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(compress_one, img): img for img in images}
            for future in as_completed(futures):
                name, in_sz, out_sz, ratio, err = future.result()
                if err:
                    print(f"  [X] {name}: {err}")
                    self.stats["errors"] += 1
                else:
                    saved = f"{ratio:.1f}%" if ratio > 0 else "+0%"
                    print(f"  [OK] {name}: {in_sz//1024}KB → {out_sz//1024}KB ({saved})")
                    total_in += in_sz
                    total_out += out_sz
                    self.stats["processed"] += 1

        if total_in > 0:
            total_saved = (1 - total_out / total_in) * 100
            print(f"\n总计: {total_in//1024}KB → {total_out//1024}KB (节省 {total_saved:.1f}%)")

        return self.stats

    # ========== 功能3: 重复文件查找 ==========
    def find_duplicates(self, directory, min_size=1):
        """查找重复文件"""
        folder = Path(directory)
        if not folder.exists():
            print(f"[X] 目录不存在: {directory}")
            return

        self.log(f"正在扫描 {folder} ...")
        size_map = {}

        # 按文件大小分组
        for f in folder.rglob("*"):
            if f.is_file() and f.stat().st_size >= min_size * 1024:
                sz = f.stat().st_size
                size_map.setdefault(sz, []).append(f)

        # 对同大小的文件计算哈希
        dup_groups = []
        for sz, files in size_map.items():
            if len(files) < 2:
                continue
            hash_map = {}
            for f in files:
                h = self._file_hash(f)
                hash_map.setdefault(h, []).append(f)
            for h, same_files in hash_map.items():
                if len(same_files) > 1:
                    dup_groups.append((sz, same_files))

        if not dup_groups:
            print("[✓] 没有找到重复文件")
            return []

        print(f"\n找到 {len(dup_groups)} 组重复文件:\n")
        total_wasted = 0
        for sz, files in sorted(dup_groups, key=lambda x: x[0], reverse=True):
            wasted = sz * (len(files) - 1)
            total_wasted += wasted
            print(f"  [{sz//1024}KB × {len(files)}份] 浪费 {wasted//1024}KB")
            for f in files:
                print(f"    └─ {f}")
            print()

        print(f"总计可释放空间: {total_wasted // (1024*1024)}MB")
        return dup_groups

    # ========== 功能4: 格式批量转换 ==========
    def convert_format(self, directory, target_format, delete_original=False,
                       recursive=False):
        """批量转换文件格式"""
        folder = Path(directory)
        format_map = {
            'txt': '.txt', 'csv': '.csv', 'json': '.json', 'md': '.md',
            'jpg': '.jpg', 'png': '.png', 'gif': '.gif', 'webp': '.webp',
        }
        ext = format_map.get(target_format, f".{target_format}")

        if HAS_PIL and target_format in ('jpg', 'png', 'webp', 'gif'):
            return self._convert_images(folder, target_format, delete_original, recursive)
        else:
            return self._convert_text_files(folder, target_format, delete_original, recursive)

    def _convert_images(self, folder, target_format, delete_original, recursive):
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
        files = []
        if recursive:
            files = [f for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in image_exts]
        else:
            files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in image_exts]

        self.log(f"开始转换 {len(files)} 个文件到 .{target_format}...")
        for f in files:
            try:
                img = Image.open(f)
                img = ImageOps.exif_transpose(img)
                out_path = f.parent / f"{f.stem}.{target_format}"
                img.save(out_path, target_format.upper())
                if delete_original and out_path.name != f.name:
                    f.unlink()
                print(f"  [OK] {f.name} → {out_path.name}")
                self.stats["processed"] += 1
            except Exception as e:
                print(f"  [X] {f.name}: {e}")
                self.stats["errors"] += 1

        return self.stats

    def _convert_text_files(self, folder, target_format, delete_original, recursive):
        print(f"[!] 文本格式转换暂只支持图片格式转换")
        return self.stats

    # ========== 辅助方法 ==========
    def _get_files(self, folder, extensions=None):
        files = sorted([f for f in folder.iterdir() if f.is_file()])
        if extensions:
            exts = [e if e.startswith('.') else f'.{e}' for e in extensions]
            files = [f for f in files if f.suffix.lower() in exts]
        return files

    def _file_hash(self, path, chunk_size=8192):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="📁 文件批处理大师 v1.0 - 批量处理文件的神器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 批量重命名（添加前缀）
  python3 main.py rename ./folder --pattern prefix --prefix "project_"

  # 批量重命名（编号）
  python3 main.py rename ./folder --pattern number --prefix "img_" --digits 4

  # 批量重命名（替换文字）
  python3 main.py rename ./folder --replace_old "draft" --replace_new "final"

  # 批量压缩图片（质量80）
  python3 main.py compress ./images --quality 80

  # 批量压缩图片（限制尺寸）
  python3 main.py compress ./images --quality 85 --max_size 1920

  # 查找重复文件
  python3 main.py dupes ./folder --min_size 1

  # 批量转换格式
  python3 main.py convert ./images --format webp --recursive
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # rename
    p_rename = subparsers.add_parser("rename", help="批量重命名")
    p_rename.add_argument("directory", help="目标目录")
    p_rename.add_argument("--pattern", choices=["prefix", "number", "date", "lower", "upper"],
                          default="prefix", help="重命名模式")
    p_rename.add_argument("--prefix", default="", help="文件名前缀")
    p_rename.add_argument("--suffix", default="", help="文件名后缀")
    p_rename.add_argument("--start", type=int, default=1, help="起始编号")
    p_rename.add_argument("--digits", type=int, default=3, help="编号位数")
    p_rename.add_argument("--replace_old", default="", help="替换旧文字")
    p_rename.add_argument("--replace_new", default="", help="替换新文字")
    p_rename.add_argument("--ext", nargs="*", help="限定的扩展名 (如 jpg png)")
    p_rename.add_argument("--dry-run", action="store_true", help="模拟运行，不实际修改")

    # compress
    p_comp = subparsers.add_parser("compress", help="批量压缩图片")
    p_comp.add_argument("directory", help="图片目录")
    p_comp.add_argument("--quality", type=int, default=80, help="压缩质量 1-100 (默认80)")
    p_comp.add_argument("--max_size", type=int, default=0, help="最大边长 (像素)")
    p_comp.add_argument("--output", default="", help="输出目录")
    p_comp.add_argument("--workers", type=int, default=4, help="并行线程数")

    # dupes
    p_dupes = subparsers.add_parser("dupes", help="查找重复文件")
    p_dupes.add_argument("directory", help="扫描目录")
    p_dupes.add_argument("--min_size", type=int, default=1, help="最小文件大小 (KB)")

    # convert
    p_conv = subparsers.add_parser("convert", help="批量格式转换")
    p_conv.add_argument("directory", help="文件目录")
    p_conv.add_argument("--format", dest="fmt", default="jpg", help="目标格式 (jpg/png/webp)")
    p_conv.add_argument("--delete", action="store_true", help="删除原文件")
    p_conv.add_argument("--recursive", action="store_true", help="递归子目录")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    processor = FileBatchProcessor()

    if args.command == "rename":
        processor.batch_rename(
            args.directory, args.pattern, args.prefix, args.suffix,
            args.start, args.digits, args.replace_old, args.replace_new,
            args.ext, args.dry_run
        )
    elif args.command == "compress":
        processor.compress_images(
            args.directory, args.quality,
            args.max_size if args.max_size > 0 else None,
            args.output, args.workers
        )
    elif args.command == "dupes":
        processor.find_duplicates(args.directory, args.min_size)
    elif args.command == "convert":
        processor.convert_format(args.directory, args.fmt, args.delete, args.recursive)


if __name__ == "__main__":
    main()
