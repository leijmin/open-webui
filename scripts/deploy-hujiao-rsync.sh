#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DEPLOY_HOST="${DEPLOY_HOST:-root@118.31.70.82}"
REMOTE_APP_DIR="${REMOTE_APP_DIR:-/www/wwwroot/hujiao_icloverai_cn}"
REMOTE_SERVICE="${REMOTE_SERVICE:-open-webui.service}"
REMOTE_URL="${REMOTE_URL:-https://hujiao.icloverai.cn}"
REMOTE_VENV_DIR="${REMOTE_VENV_DIR:-$REMOTE_APP_DIR/venv}"
REMOTE_SITECUSTOMIZE="${REMOTE_SITECUSTOMIZE:-$REMOTE_VENV_DIR/lib64/python3.11/site-packages/sitecustomize.py}"

SSH_BIN="${SSH_BIN:-ssh}"
RSYNC_BIN="${RSYNC_BIN:-rsync}"
CURL_BIN="${CURL_BIN:-curl}"
GIT_BIN="${GIT_BIN:-git}"
AUTO_COMMIT_BEFORE_DEPLOY="${AUTO_COMMIT_BEFORE_DEPLOY:-true}"
AUTO_COMMIT_MESSAGE="${AUTO_COMMIT_MESSAGE:-chore: deploy hujiao branding snapshot}"

log() {
	printf '[deploy-hujiao] %s\n' "$*"
}

die() {
	printf '[deploy-hujiao] 错误: %s\n' "$*" >&2
	exit 1
}

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || die "未找到命令: $1"
}

run_remote() {
	"$SSH_BIN" -o StrictHostKeyChecking=accept-new "$DEPLOY_HOST" \
		"REMOTE_APP_DIR='$REMOTE_APP_DIR' REMOTE_SERVICE='$REMOTE_SERVICE' REMOTE_SITECUSTOMIZE='$REMOTE_SITECUSTOMIZE' bash -s"
}

require_cmd npm
require_cmd "$SSH_BIN"
require_cmd "$RSYNC_BIN"
require_cmd "$CURL_BIN"
require_cmd "$GIT_BIN"

cd "$REPO_ROOT"

if [[ ! -f package.json ]]; then
	die "当前目录不是 open-webui 仓库根目录: $REPO_ROOT"
fi

if [[ "$AUTO_COMMIT_BEFORE_DEPLOY" == "true" ]]; then
	if [[ -n "$("$GIT_BIN" status --porcelain)" ]]; then
		log "检测到本地未提交改动，自动提交后再部署"
		"$GIT_BIN" add -A
		"$GIT_BIN" commit -m "$AUTO_COMMIT_MESSAGE"
	else
		log "当前工作区没有未提交改动，跳过自动提交"
	fi
fi

if [[ ! -d node_modules ]]; then
	log "未检测到 node_modules，使用兼容模式安装前端依赖"
	npm install --legacy-peer-deps
fi

log "检查远端 venv 与 SQLite 兼容补丁"
run_remote <<'EOF'
set -euo pipefail
test -d "$REMOTE_APP_DIR"
test -d "$REMOTE_APP_DIR/venv"
test -f "$REMOTE_SITECUSTOMIZE"
EOF

log "检查远端 rsync（若缺失则自动安装）"
run_remote <<'EOF'
set -euo pipefail
if command -v rsync >/dev/null 2>&1; then
	exit 0
fi

echo "[deploy-hujiao] 远端未安装 rsync，正在尝试自动安装..."

if command -v apt-get >/dev/null 2>&1; then
	export DEBIAN_FRONTEND=noninteractive
	apt-get update
	apt-get install -y rsync
elif command -v dnf >/dev/null 2>&1; then
	dnf install -y rsync
elif command -v yum >/dev/null 2>&1; then
	yum install -y rsync
elif command -v apk >/dev/null 2>&1; then
	apk add --no-cache rsync
else
	echo "[deploy-hujiao] 错误: 远端缺少 rsync，且无法识别包管理器，请手动安装 rsync。" >&2
	exit 1
fi

command -v rsync >/dev/null 2>&1
EOF

log "构建前端资源"
npm run build

RSYNC_EXCLUDES=(
	"--exclude=.git"
	"--exclude=.worktrees"
	"--exclude=node_modules"
	"--exclude=.venv"
	"--exclude=venv"
	"--exclude=.env"
	"--exclude=.env.*"
	"--exclude=.webui_secret_key"
	"--exclude=.svelte-kit"
	"--exclude=.DS_Store"
	"--exclude=__pycache__"
	"--exclude=*.pyc"
	"--exclude=backend/data"
	"--exclude=data"
	"--exclude=coverage"
)

log "同步仓库到 $DEPLOY_HOST:$REMOTE_APP_DIR"
"$RSYNC_BIN" -az --delete \
	-e "$SSH_BIN -o StrictHostKeyChecking=accept-new" \
	"${RSYNC_EXCLUDES[@]}" \
	"$REPO_ROOT/" \
	"$DEPLOY_HOST:$REMOTE_APP_DIR/"

log "远端重启服务"
run_remote <<'EOF'
set -euo pipefail
cd "$REMOTE_APP_DIR"
test -d venv
test -f "$REMOTE_SITECUSTOMIZE"
systemctl restart "$REMOTE_SERVICE"
systemctl is-active "$REMOTE_SERVICE" >/dev/null
EOF

log "执行服务状态检查"
"$SSH_BIN" -o StrictHostKeyChecking=accept-new "$DEPLOY_HOST" \
	"systemctl status '$REMOTE_SERVICE' --no-pager"

log "执行站点健康检查"
TMP_RESPONSE="$(mktemp)"
trap 'rm -f "$TMP_RESPONSE"' EXIT
HEALTH_MAX_ATTEMPTS="${HEALTH_MAX_ATTEMPTS:-30}"
HEALTH_SLEEP_SECONDS="${HEALTH_SLEEP_SECONDS:-5}"

for ((attempt = 1; attempt <= HEALTH_MAX_ATTEMPTS; attempt++)); do
	if "$CURL_BIN" -fsSL "$REMOTE_URL" >"$TMP_RESPONSE" 2>/dev/null &&
		"$CURL_BIN" -fsSI "$REMOTE_URL/static/logo.jpg" >/dev/null 2>&1; then
		sed -n '1,10p' "$TMP_RESPONSE"
		log "部署完成: $REMOTE_URL"
		exit 0
	fi

	log "站点尚未就绪（${attempt}/${HEALTH_MAX_ATTEMPTS}），等待 ${HEALTH_SLEEP_SECONDS}s 后重试..."
	sleep "$HEALTH_SLEEP_SECONDS"
done

die "站点健康检查失败: $REMOTE_URL"
