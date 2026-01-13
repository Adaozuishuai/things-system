#!/usr/bin/env bash
set -euo pipefail

############################################
# 配置区：你只需要改这里
############################################
BRANCH="${BRANCH:-main}" # 你的分支名：main / master / dev 等
DRY_RUN="${DRY_RUN:-false}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 项目路径
FRONTEND_DIR="${FRONTEND_DIR:-${ROOT_DIR}/frontend}"
BACKEND_DIR="${BACKEND_DIR:-${ROOT_DIR}/backend}"

# PM2 进程名（跟 pm2 list 里一致）
PM2_FRONTEND_NAME="${PM2_FRONTEND_NAME:-react-dev}"
PM2_BACKEND_NAME="${PM2_BACKEND_NAME:-api}"

# 后端 venv 路径（你现在是 backend/venv）
BACKEND_VENV_DIR="${BACKEND_VENV_DIR:-${BACKEND_DIR}/venv}"

# 后端依赖文件路径（本仓库在根目录）
BACKEND_REQUIREMENTS_FILE="${BACKEND_REQUIREMENTS_FILE:-${ROOT_DIR}/requirements.txt}"

# 是否在拉取后自动重启（建议 true）
RESTART_FRONTEND="${RESTART_FRONTEND:-true}"
RESTART_BACKEND="${RESTART_BACKEND:-true}"

############################################
# 工具函数
############################################
log() { echo -e "\n==> $*"; }

run() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "+ $*"
    return 0
  fi
  "$@"
}

ensure_git_clean_or_allow() {
  local dir="$1"
  if [[ "${DRY_RUN}" == "true" ]]; then
    return 0
  fi
  cd "$dir"
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: 目录 $dir 有未提交改动，先提交或 stash 再部署。"
    git status --porcelain
    exit 1
  fi
}

git_pull() {
  local dir="$1"
  if [[ "${DRY_RUN}" == "true" ]]; then
    cd "$dir"
    echo "no_change"
    return 0
  fi
  cd "$dir"
  local before
  before="$(git rev-parse HEAD)"
  run git fetch origin "$BRANCH"
  run git reset --hard "origin/$BRANCH"
  local after
  after="$(git rev-parse HEAD)"

  if [[ "$before" == "$after" ]]; then
    echo "no_change"
  else
    echo "changed"
  fi
}

############################################
# 前端部署
############################################
deploy_frontend() {
  log "前端：检查并更新代码"
  ensure_git_clean_or_allow "$FRONTEND_DIR"

  cd "$FRONTEND_DIR"
  local old_head
  old_head="$(git rev-parse HEAD)"

  local status
  status="$(git_pull "$FRONTEND_DIR")"
  cd "$FRONTEND_DIR"

  if [[ "$status" == "no_change" ]]; then
    log "前端：代码无变化，跳过"
    return 0
  fi

  local new_head
  new_head="$(git rev-parse HEAD)"
  if git diff --name-only "$old_head" "$new_head" | grep -qE 'package-lock\.json|package\.json'; then
    log "前端：依赖有变化，执行 npm install"
    run npm install
  else
    log "前端：依赖无变化，跳过 npm install"
  fi

  if [[ "$RESTART_FRONTEND" == "true" ]]; then
    log "前端：重启 PM2 进程 $PM2_FRONTEND_NAME"
    run pm2 restart "$PM2_FRONTEND_NAME"
  fi
}

############################################
# 后端部署
############################################
deploy_backend() {
  log "后端：检查并更新代码"
  ensure_git_clean_or_allow "$BACKEND_DIR"

  cd "$BACKEND_DIR"
  local old_head
  old_head="$(git rev-parse HEAD)"

  local status
  status="$(git_pull "$BACKEND_DIR")"
  cd "$BACKEND_DIR"

  if [[ "$status" == "no_change" ]]; then
    log "后端：代码无变化，跳过"
    return 0
  fi

  local new_head
  new_head="$(git rev-parse HEAD)"

  if git diff --name-only "$old_head" "$new_head" | grep -qE '(^|/)requirements\.txt$|pyproject\.toml|poetry\.lock'; then
    log "后端：依赖有变化，安装/更新依赖"
    run "${BACKEND_VENV_DIR}/bin/pip" install -r "${BACKEND_REQUIREMENTS_FILE}"
  else
    log "后端：依赖无变化，跳过 pip install"
  fi

  if [[ "$RESTART_BACKEND" == "true" ]]; then
    log "后端：重启 PM2 进程 $PM2_BACKEND_NAME"
    run pm2 restart "$PM2_BACKEND_NAME"
  fi
}

############################################
# 主流程
############################################
main() {
  log "开始部署（branch=$BRANCH）"
  deploy_backend
  deploy_frontend
  log "部署完成"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "+ pm2 save >/dev/null 2>&1 || true"
  else
    pm2 save >/dev/null 2>&1 || true
  fi
  log "已执行 pm2 save"
}

main "$@"
