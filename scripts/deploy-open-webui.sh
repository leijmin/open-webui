#!/usr/bin/env bash
# Open WebUI — 非 Docker 部署（Python venv + pip + systemd）
#
# 从本机推到服务器（需本机能 ssh 登录）：
#   export DEPLOY_HOST=root@8.154.25.72
#   # 可选：阿里云 PyPI
#   # export PIP_INDEX=https://mirrors.aliyun.com/pypi/simple
#   ./scripts/deploy-open-webui.sh
#
# 仅在本机（或已 scp 到服务器后）执行安装：
#   sudo ./scripts/deploy-open-webui.sh --local
#
# 环境变量（均可选）：
#   DEPLOY_HOST  SSH 目标，远程部署时必填
#   APP_DIR      默认 /opt/open-webui
#   PYTHON_BIN   默认 python3.11
#   PORT         默认 8080
#   PIP_INDEX    镜像，如 https://mirrors.aliyun.com/pypi/simple
#

set -euo pipefail

DEPLOY_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

APP_DIR="${APP_DIR:-/opt/open-webui}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
PORT="${PORT:-8080}"
DEPLOY_HOST="${DEPLOY_HOST:-}"

log() { printf '[deploy] %s\n' "$*"; }
die() { printf '[deploy] 错误: %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "未找到命令: $1"
}

ensure_python_on_debian() {
  if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    return 0
  fi
  log "未找到 $PYTHON_BIN，尝试使用 apt 安装 …"
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y python3.11 python3.11-venv || {
      apt-get install -y python3.11 python3.11-venv python3.11-distutils || true
    }
  fi
  command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "请先安装 Python 3.11，并保证可执行文件名为: $PYTHON_BIN"
}

install_on_server() {
  require_cmd systemctl || die "未找到 systemctl，请使用带 systemd 的 Linux"
  ensure_python_on_debian

  if [[ "$(id -u)" -ne 0 ]]; then
    die "在服务器上安装 systemd 服务需要 root，请使用: sudo $0 --local"
  fi

  log "安装目录: $APP_DIR"
  mkdir -p "$APP_DIR"
  cd "$APP_DIR"

  if [[ ! -d venv ]]; then
    log "创建虚拟环境: $PYTHON_BIN -m venv venv"
    "$PYTHON_BIN" -m venv venv
  fi
  # shellcheck source=/dev/null
  source venv/bin/activate
  python -m pip install -U pip setuptools wheel

  if [[ -n "${PIP_INDEX:-}" ]]; then
    pip install -i "$PIP_INDEX" --no-cache-dir 'open-webui'
  else
    pip install --no-cache-dir 'open-webui'
  fi

  PY_ENV_ROOT="$(python -c "import sysconfig; from pathlib import Path; print(Path(sysconfig.get_path('platlib')).parent)")"
  ENV_FILE="${PY_ENV_ROOT}/.env"

  if [[ ! -f "$ENV_FILE" ]]; then
    log "写入默认配置: $ENV_FILE"
    umask 077
    cat > "$ENV_FILE" <<'ENVEOF'
OLLAMA_BASE_URL=http://127.0.0.1:11434
OPENAI_API_BASE_URL=
OPENAI_API_KEY=
CORS_ALLOW_ORIGIN=*
FORWARDED_ALLOW_IPS=*
SCARF_NO_ANALYTICS=true
DO_NOT_TRACK=true
ANONYMIZED_TELEMETRY=false
ENVEOF
    chmod 600 "$ENV_FILE"
  else
    log "已存在 $ENV_FILE，保留已有配置"
  fi

  if [[ ! -e "$APP_DIR/.env" ]]; then
    ln -sf "$ENV_FILE" "$APP_DIR/.env" || true
  fi

  log "写入 /etc/systemd/system/open-webui.service"
  cat > /etc/systemd/system/open-webui.service <<EOF
[Unit]
Description=Open WebUI (pip / venv)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
ExecStart=$APP_DIR/venv/bin/open-webui serve --host 0.0.0.0 --port $PORT
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable open-webui.service
  systemctl restart open-webui.service

  log "部署完成。"
  systemctl --no-pager -l status open-webui.service || true
  log "监听: http://0.0.0.0:$PORT/ （请按需配置防火墙/安全组放行 TCP $PORT）"
}

remote_via_ssh() {
  require_cmd ssh
  [[ -n "$DEPLOY_HOST" ]] || die "请设置 DEPLOY_HOST，例如: export DEPLOY_HOST=root@8.154.25.72"

  log "通过 SSH 连接: $DEPLOY_HOST"
  # 将同一脚本 stdin 交给远端 bash，由远端以 --local 执行安装逻辑
  ssh -o StrictHostKeyChecking=accept-new "$DEPLOY_HOST" \
    env APP_DIR="$APP_DIR" PYTHON_BIN="$PYTHON_BIN" PORT="$PORT" PIP_INDEX="${PIP_INDEX:-}" \
    bash -s -- --local < "$DEPLOY_SCRIPT"
}

main() {
  case "${1:-}" in
    -h|--help)
      sed -n '1,22p' "$DEPLOY_SCRIPT" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    --local)
      install_on_server
      ;;
    "")
      remote_via_ssh
      ;;
    *)
      die "未知参数: $1 （使用 --local 在服务器本机安装，或不传参从本机 SSH 远程安装）"
      ;;
  esac
}

main "$@"
