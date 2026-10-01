#!/usr/bin/env bash
# 一键发布到 GitHub。用法：在本目录执行  bash publish.sh
set -e
REPO=ai-film-studio
git init -q 2>/dev/null || true
git add -A
git commit -q -m "ai-film-studio · AI 电影全能工作流 首次发布" || true
git branch -M main
if command -v gh >/dev/null 2>&1; then
  gh repo create "$REPO" --public --source=. --push \
    --description "AI 电影全能工作流：资产库 → 产线 → 决策台 → 回库，剧本进，全片提示词出"
  echo "✔ 已发布：$(gh repo view "$REPO" --json url -q .url)"
else
  read -p "先在 github.com/new 建一个空仓库 $REPO，然后输入你的 GitHub 用户名：" U
  git remote add origin "https://github.com/$U/$REPO.git" 2>/dev/null || git remote set-url origin "https://github.com/$U/$REPO.git"
  git push -u origin main
  echo "✔ 已发布：https://github.com/$U/$REPO"
fi
