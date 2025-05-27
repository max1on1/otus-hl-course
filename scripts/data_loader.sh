#!/usr/bin/env bash
set -euo pipefail

# Скрипт для загрузки данных из people.v2.csv в таблицу users
# БД запущена в Docker-контейнере локально на хосте.
# Требует: docker, uuidgen и настройки переменных окружения:
#   DB_CONTAINER - имя контейнера с БД,
#   PGUSER, PGDATABASE, PGPORT (если отличается от дефолтного),
#   PGPASSWORD (можно задавать через .pgpass),
#   (опционально) PGHOST внутри контейнера – обычно localhost.
export DB_CONTAINER=c7da93251d4d
export PGUSER=postgres
export PGDATABASE=socialnetwork
export PGPORT=5432  
export PGPASSWORD=postgres
FILE="people.v2.csv"
DB_CONTAINER=${DB_CONTAINER:-users_db}
: ${PGUSER:?Need to set PGUSER}
: ${PGDATABASE:?Need to set PGDATABASE}
: ${DEFAULT_PASSWORD_HASH:=""}

if [[ ! -f "$FILE" ]]; then
  echo "Файл $FILE не найден!" >&2
  exit 1
fi

# Проверяем контейнер
if ! docker inspect "$DB_CONTAINER" >/dev/null 2>&1; then
  echo "Контейнер '$DB_CONTAINER' не найден или не запущен" >&2
  exit 1
fi

# Генерируем поток CSV для COPY
# Колонки: id,first_name,second_name,birthdate,biography,city,password_hash
{
  echo "id,first_name,second_name,birthdate,biography,city,password_hash"
  while IFS=',' read -r fullname birthdate city; do
    [[ -z "$fullname" ]] && continue
    first_name="${fullname%% *}"
    second_name="${fullname#* }"
    uuid=$(uuidgen)
    printf '"%s","%s","%s","%s","","%s","%s"\n' \
      "$uuid" \
      "$first_name" \
      "$second_name" \
      "$birthdate" \
      "$city" \
      "$DEFAULT_PASSWORD_HASH"
  done < "$FILE"
} |
# Подаём поток в psql внутри контейнера
docker exec -i "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 \
  -U "$PGUSER" -d "$PGDATABASE" ${PGPORT:+-p "$PGPORT"} \
  -c "COPY users (id, first_name, second_name, birthdate, biography, city, password_hash) FROM STDIN WITH CSV HEADER;"
