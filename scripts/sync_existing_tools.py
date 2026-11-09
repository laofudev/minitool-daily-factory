#!/usr/bin/env python3
"""sync_existing_tools.py — regenerate existing-tools.md from the site registry.

The authoritative source of truth is:
    https://github.com/laofudev/minitool/blob/main/registry.json

Run this after a batch goes live to refresh the local dedup file:
    python3 scripts/sync_existing_tools.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "existing-tools.md"
REGISTRY_URL = "https://raw.githubusercontent.com/laofudev/minitool/main/registry.json"


def fetch_registry():
    try:
        with urllib.request.urlopen(REGISTRY_URL, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print("error: cannot fetch registry: %s" % e, file=sys.stderr)
        sys.exit(1)


def category_display(cat_id):
    return {
        "text-tools": "Text & Writing",
        "developer-tools": "Developer",
        "calculators": "Calculators & Converters",
    }.get(cat_id, cat_id.replace("-", " ").title())


def load_registry(local_path=None):
    if local_path:
        with open(local_path, encoding="utf-8") as f:
            return json.load(f)
    return fetch_registry()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", metavar="PATH", help="use a local registry.json instead of fetching from GitHub")
    args = parser.parse_args()

    registry = load_registry(args.local)
    tools = registry.get("tools", [])
    rows = []
    for i, t in enumerate(tools, 1):
        rows.append("| %d | %s | `%s` | %s |" % (
            i, t["name"], t["file"], category_display(t.get("category", ""))))

    content = (
        "# minitool.io 已上线工具清单（防重复档案）\n"
        "\n"
        "> **本文件由 `scripts/sync_existing_tools.py` 自动生成，不要手动编辑。**\n"
        "> 权威来源：`https://github.com/laofudev/minitool/blob/main/registry.json`\n"
        "> 开发新工具前，先运行上述脚本或直接用 registry.json 查重。\n"
        "\n"
        "## 已存在（截至生成时，站点共 %d 个）\n"
        "\n"
        "| # | 工具 | slug | 类别 |\n"
        "|---|------|------|------|\n"
        "%s\n"
    ) % (len(tools), "\n".join(rows))

    OUT_PATH.write_text(content, encoding="utf-8")
    print("wrote %d tools to %s" % (len(tools), OUT_PATH))


if __name__ == "__main__":
    main()
