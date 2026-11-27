#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
MYSQL_DIR="${PROJECT_DIR:h}/mysql-runtime"
RUN_DIR="$PROJECT_DIR/.local-run"

for service in clinica governo; do
  pid_file="$RUN_DIR/$service.pid"
  if [[ -f "$pid_file" ]]; then
    pid="$(<"$pid_file")"
    if ps -p "$pid" -o command= 2>/dev/null | grep -q uvicorn; then
      kill "$pid"
    fi
    rm -f "$pid_file"
  fi
done

if "$MYSQL_DIR/mysql/bin/mysqladmin" --protocol=tcp -h127.0.0.1 -P3306 -uroot ping >/dev/null 2>&1; then
  "$MYSQL_DIR/mysql/bin/mysqladmin" --protocol=tcp -h127.0.0.1 -P3306 -uroot shutdown
fi

echo "Clínica Veterinária e MySQL foram encerrados."
