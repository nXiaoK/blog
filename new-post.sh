#!/bin/bash
# 新建文章脚本
# 用法: ./new-post.sh "文章标题" "分类" "标签1,标签2" "源链接" "原作者"

TITLE="${1:?用法: $0 \"标题\" \"分类\" \"标签\" \"源链接\" \"原作者\"}"
CATEGORY="${2:-未分类}"
TAGS="${3:-}"
SOURCE="${4:-}"
SOURCE_AUTHOR="${5:-}"

# 生成文件名
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9\u4e00-\u9fff]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
DATE=$(date +%Y-%m-%d)
FILE="content/posts/${DATE}-${SLUG}.md"

# 处理标签
TAG_LINE=""
if [ -n "$TAGS" ]; then
  TAG_LINE=$(echo "$TAGS" | tr ',' '\n' | sed 's/^/  - /' | tr '\n' '\n')
fi

cat > "$FILE" << EOF
---
title: "${TITLE}"
date: ${DATE}
draft: false
source: "${SOURCE}"
source_author: "${SOURCE_AUTHOR}"
source_desc: "${TITLE}"
categories: ["${CATEGORY}"]
tags:
${TAG_LINE}
---

在此粘贴或编写正文内容...
EOF

echo "✅ 已创建: $FILE"
