#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/.run/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
RUNTIME_ENV_FILE="$BACKEND_DIR/.env.local.runtime"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
INSTALL_DEPS=true
START_FRONTEND=true

ts() {
  date +"%Y-%m-%d %H:%M:%S"
}

log() {
  printf "[%s] [INFO] %s\n" "$(ts)" "$1"
}

warn() {
  printf "[%s] [WARN] %s\n" "$(ts)" "$1"
}

fail() {
  printf "[%s] [ERROR] %s\n" "$(ts)" "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

ensure_dirs() {
  mkdir -p "$RUN_DIR" "$LOG_DIR" "$BACKEND_DIR/data" "$BACKEND_DIR/uploads" "$BACKEND_DIR/logs" "$BACKEND_DIR/chroma_db"
}

resolve_venv() {
  if [ -x "$BACKEND_DIR/venv/bin/python" ]; then
    VENV_PY="$BACKEND_DIR/venv/bin/python"
    VENV_PIP="$BACKEND_DIR/venv/bin/pip"
    return
  fi
  if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
    VENV_PY="$BACKEND_DIR/.venv/bin/python"
    VENV_PIP="$BACKEND_DIR/.venv/bin/pip"
    return
  fi
  log "Creating backend virtual environment at backend/.venv"
  python3 -m venv "$BACKEND_DIR/.venv"
  VENV_PY="$BACKEND_DIR/.venv/bin/python"
  VENV_PIP="$BACKEND_DIR/.venv/bin/pip"
}

upsert_env() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$RUNTIME_ENV_FILE"; then
    perl -0777 -i -pe "s|^${key}=.*$|${key}=${value}|mg" "$RUNTIME_ENV_FILE"
  else
    printf "%s=%s\n" "$key" "$value" >> "$RUNTIME_ENV_FILE"
  fi
}

build_runtime_env() {
  if [ -f "$BACKEND_DIR/.env.local" ]; then
    cp "$BACKEND_DIR/.env.local" "$RUNTIME_ENV_FILE"
  elif [ -f "$BACKEND_DIR/.env" ]; then
    cp "$BACKEND_DIR/.env" "$RUNTIME_ENV_FILE"
  else
    : > "$RUNTIME_ENV_FILE"
  fi
  upsert_env "DEPLOYMENT_ENV" "local"
  upsert_env "USE_AWS_AI" "false"
  upsert_env "MOCK_EXTERNAL_SERVICES" "true"
  upsert_env "AWS_EC2_METADATA_DISABLED" "true"
  upsert_env "AWS_ACCESS_KEY_ID" "local"
  upsert_env "AWS_SECRET_ACCESS_KEY" "local"
  upsert_env "AWS_REGION" "ap-south-1"
  upsert_env "DATABASE_TYPE" "sqlite"
  upsert_env "DATABASE_PATH" "./data"
  upsert_env "DATABASE_NAME" "krishi_local.db"
  upsert_env "STORAGE_TYPE" "local"
  upsert_env "STORAGE_BASE_PATH" "./uploads"
  upsert_env "CHROMA_PERSIST_DIRECTORY" "./chroma_db"
  upsert_env "AUTH_PROVIDER" "local"
  upsert_env "MOCK_COGNITO" "true"
  upsert_env "LOCAL_LAMBDA_MODE" "uvicorn"
}

setup_frontend_env() {
  local env_file="$FRONTEND_DIR/.env.local"
  if [ ! -f "$env_file" ]; then
    : > "$env_file"
  fi
  if grep -q "^VITE_API_URL=" "$env_file"; then
    perl -0777 -i -pe "s|^VITE_API_URL=.*$|VITE_API_URL=http://127.0.0.1:${BACKEND_PORT}|mg" "$env_file"
  else
    printf "VITE_API_URL=http://127.0.0.1:%s\n" "$BACKEND_PORT" >> "$env_file"
  fi
}

install_backend_deps() {
  if [ "$INSTALL_DEPS" = true ]; then
    log "Installing backend dependencies"
    "$VENV_PIP" install -r "$BACKEND_DIR/requirements.txt" >/dev/null
  else
    log "Skipping backend dependency installation"
  fi
}

install_frontend_deps() {
  if [ "$START_FRONTEND" = false ]; then
    return
  fi
  if [ "$INSTALL_DEPS" = true ]; then
    log "Installing frontend dependencies"
    (cd "$FRONTEND_DIR" && npm install >/dev/null)
  else
    log "Skipping frontend dependency installation"
  fi
}

validate_dependency_injection() {
  log "Validating backend is configured for local dependency injection"
  (
    cd "$BACKEND_DIR"
    set -a
    source "$RUNTIME_ENV_FILE"
    set +a
    "$VENV_PY" - <<'PY'
from app.core.config import settings
assert settings.USE_AWS_AI is False, "USE_AWS_AI must be false for local mode"
print("local-ai-selected=true")
PY
  ) >/dev/null
}

is_running() {
  local pid_file="$1"
  [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" >/dev/null 2>&1
}

start_backend() {
  if is_running "$BACKEND_PID_FILE"; then
    log "Backend already running with PID $(cat "$BACKEND_PID_FILE")"
    return
  fi
  log "Starting backend on 127.0.0.1:${BACKEND_PORT}"
  nohup bash -lc "cd '$BACKEND_DIR' && set -a && source '$RUNTIME_ENV_FILE' && set +a && '$VENV_PY' -m uvicorn app.main:app --host 127.0.0.1 --port ${BACKEND_PORT}" > "$LOG_DIR/backend.log" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
}

start_frontend() {
  if [ "$START_FRONTEND" = false ]; then
    log "Frontend startup disabled"
    return
  fi
  if is_running "$FRONTEND_PID_FILE"; then
    log "Frontend already running with PID $(cat "$FRONTEND_PID_FILE")"
    return
  fi
  log "Starting frontend on 127.0.0.1:${FRONTEND_PORT}"
  nohup bash -lc "cd '$FRONTEND_DIR' && npm run dev -- --host 127.0.0.1 --port ${FRONTEND_PORT}" > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
}

retry_curl() {
  local url="$1"
  local attempts="${2:-40}"
  local sleep_s="${3:-1}"
  local i=1
  while [ "$i" -le "$attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
    i=$((i + 1))
  done
  return 1
}

validate_services() {
  log "Running local validation checks"
  if retry_curl "http://127.0.0.1:${BACKEND_PORT}/api/v1/health" 45 1; then
    log "Backend health check passed"
  else
    tail -n 50 "$LOG_DIR/backend.log" || true
    fail "Backend health check failed"
  fi
  if [ "$START_FRONTEND" = true ]; then
    if retry_curl "http://127.0.0.1:${FRONTEND_PORT}" 45 1; then
      log "Frontend availability check passed"
    else
      tail -n 50 "$LOG_DIR/frontend.log" || true
      fail "Frontend availability check failed"
    fi
  fi
  if curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    log "Ollama is reachable"
  else
    warn "Ollama is not reachable; local mock and rule-based fallbacks remain active"
  fi
}

status_services() {
  if is_running "$BACKEND_PID_FILE"; then
    log "Backend running with PID $(cat "$BACKEND_PID_FILE")"
  else
    warn "Backend not running"
  fi
  if [ "$START_FRONTEND" = true ]; then
    if is_running "$FRONTEND_PID_FILE"; then
      log "Frontend running with PID $(cat "$FRONTEND_PID_FILE")"
    else
      warn "Frontend not running"
    fi
  fi
}

stop_services() {
  if is_running "$BACKEND_PID_FILE"; then
    kill "$(cat "$BACKEND_PID_FILE")" || true
    rm -f "$BACKEND_PID_FILE"
    log "Backend stopped"
  else
    warn "Backend was not running"
  fi
  if is_running "$FRONTEND_PID_FILE"; then
    kill "$(cat "$FRONTEND_PID_FILE")" || true
    rm -f "$FRONTEND_PID_FILE"
    log "Frontend stopped"
  else
    warn "Frontend was not running"
  fi
}

print_help() {
  cat <<EOF
Usage: ./scripts/deploy-local.sh <command> [flags]

Commands:
  start       Configure local mode, initialize services, start backend and frontend, validate
  validate    Validate local services are healthy
  stop        Stop local backend and frontend started by this script
  status      Show process status
  prereqs     Print required local prerequisites

Flags:
  --no-install       Skip dependency installation
  --backend-only     Start and validate backend only
  --backend-port N   Use custom backend port (default: 8000)
  --frontend-port N  Use custom frontend port (default: 5173)

Required local prerequisites:
  - python3
  - pip (via python virtual environment)
  - node and npm
  - curl

Troubleshooting:
  - Backend fails health check: inspect .run/logs/backend.log and verify port availability.
  - Frontend fails startup: inspect .run/logs/frontend.log and run npm install in frontend.
  - Local AI unavailable: start Ollama or continue using fallback mode with MOCK_EXTERNAL_SERVICES=true.
  - Port conflicts: rerun with --backend-port or --frontend-port.
  - Dependency failures: rerun without --no-install to reinstall dependencies.
EOF
}

parse_args() {
  COMMAND="${1:-start}"
  shift || true
  while [ $# -gt 0 ]; do
    case "$1" in
      --no-install)
        INSTALL_DEPS=false
        ;;
      --backend-only)
        START_FRONTEND=false
        ;;
      --backend-port)
        shift
        BACKEND_PORT="${1:-8000}"
        ;;
      --frontend-port)
        shift
        FRONTEND_PORT="${1:-5173}"
        ;;
      *)
        fail "Unknown flag: $1"
        ;;
    esac
    shift || true
  done
}

check_prerequisites() {
  require_cmd python3
  require_cmd curl
  if [ "$START_FRONTEND" = true ]; then
    require_cmd node
    require_cmd npm
  fi
}

start_flow() {
  ensure_dirs
  check_prerequisites
  resolve_venv
  build_runtime_env
  setup_frontend_env
  install_backend_deps
  install_frontend_deps
  validate_dependency_injection
  start_backend
  start_frontend
  validate_services
  status_services
  log "Local deployment is ready"
  log "Backend URL: http://127.0.0.1:${BACKEND_PORT}"
  if [ "$START_FRONTEND" = true ]; then
    log "Frontend URL: http://127.0.0.1:${FRONTEND_PORT}"
  fi
}

validate_flow() {
  ensure_dirs
  validate_services
}

main() {
  parse_args "$@"
  case "$COMMAND" in
    start)
      start_flow
      ;;
    validate)
      validate_flow
      ;;
    stop)
      stop_services
      ;;
    status)
      status_services
      ;;
    prereqs)
      print_help
      ;;
    help|-h|--help)
      print_help
      ;;
    *)
      fail "Unknown command: $COMMAND"
      ;;
  esac
}

main "$@"
