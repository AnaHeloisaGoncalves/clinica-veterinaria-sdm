#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
MYSQL_DIR="${PROJECT_DIR:h}/mysql-runtime"
RUN_DIR="$PROJECT_DIR/.local-run"

mkdir -p "$RUN_DIR" "$MYSQL_DIR/run" "$MYSQL_DIR/logs"
cd "$PROJECT_DIR"

if ! "$MYSQL_DIR/mysql/bin/mysqladmin" --protocol=tcp -h127.0.0.1 -P3306 -uroot ping >/dev/null 2>&1; then
  "$MYSQL_DIR/mysql/bin/mysqld" \
    --daemonize \
    --basedir="$MYSQL_DIR/mysql" \
    --datadir="$MYSQL_DIR/data" \
    --port=3306 \
    --bind-address=127.0.0.1 \
    --socket="$MYSQL_DIR/run/mysql.sock" \
    --pid-file="$MYSQL_DIR/run/mysql.pid" \
    --log-error="$MYSQL_DIR/logs/mysql.log"
fi

cleanup() {
  [[ -n "${CLINICA_PID:-}" ]] && kill "$CLINICA_PID" >/dev/null 2>&1 || true
  [[ -n "${GOVERNO_PID:-}" ]] && kill "$GOVERNO_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

"$PROJECT_DIR/.venv/bin/python" -m uvicorn api_governo.main:app \
  --host 127.0.0.1 --port 8001 >"$RUN_DIR/governo.log" 2>&1 &
GOVERNO_PID=$!
echo "$GOVERNO_PID" > "$RUN_DIR/governo.pid"

"$PROJECT_DIR/.venv/bin/python" -m uvicorn api_clinica.main:app \
  --host 127.0.0.1 --port 8000 >"$RUN_DIR/clinica.log" 2>&1 &
CLINICA_PID=$!
echo "$CLINICA_PID" > "$RUN_DIR/clinica.pid"

for attempt in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/ >/dev/null && curl -fsS http://127.0.0.1:8001/health >/dev/null; then
    echo ""
    echo "Clínica Veterinária está rodando."
    echo "Sistema: http://127.0.0.1:8000"
    echo "API da clínica: http://127.0.0.1:8000/docs"
    echo "API do governo: http://127.0.0.1:8001/docs"
    echo "Login: demo@example.test"
    echo "Senha: consulte DEMO_PASSWORD no arquivo .env"
    [[ "${1:-}" == "--no-open" ]] || open http://127.0.0.1:8000
    echo ""
    echo "Mantenha esta janela aberta durante a apresentação."
    echo "Para encerrar, pressione Control+C."
    wait "$CLINICA_PID" "$GOVERNO_PID"
    exit $?
  fi
  sleep 1
done

echo "Os serviços não ficaram prontos. Consulte os logs em $RUN_DIR" >&2
exit 1
