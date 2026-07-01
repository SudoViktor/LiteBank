#!/bin/bash
set -e
set -u

function create_user_and_database() {
    local db_info=$1

    # Розбиваємо рядок виду "db:user:pass" за роздільником ":"
    local database=$(echo "$db_info" | cut -d':' -f1)
    local username=$(echo "$db_info" | cut -d':' -f2)
    local password=$(echo "$db_info" | cut -d':' -f3)

    echo "  Creating user '$username' and database '$database'..."

    # Виконуємо SQL-команди від імені головного адміністратора
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE USER $username WITH PASSWORD '$password';
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $username;
        ALTER DATABASE $database OWNER TO $username;
EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
    echo "Multiple database and user creation requested."

    # Проходимо по черзі через кожну пару налаштувань, розділених комою
    for db_entry in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_user_and_database $db_entry
    done

    echo "All databases and dedicated users created successfully!"
fi