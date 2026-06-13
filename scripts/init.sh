#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

validate_env() {
    log_info "Validating environment configuration..."
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error ".env not found. Copy .env.example to .env and configure."
        exit 1
    fi
    set -a; source "$PROJECT_ROOT/.env"; set +a

    local required_vars=("POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD"
        "REDIS_PASSWORD" "JWT_SECRET" "DB_ENCRYPTION_KEY"
        "ADMIN_USERNAME" "ADMIN_PASSWORD")
    local missing=0
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required variable $var is not set in .env"; missing=1
        fi
    done
    [ "$missing" -eq 1 ] && { log_error "Set all required variables in .env."; exit 1; }

    [ ${#JWT_SECRET} -lt 32 ] && log_warn "JWT_SECRET < 32 chars. Generate: openssl rand -hex 32"
    [ ${#DB_ENCRYPTION_KEY} -ne 64 ] && log_warn "DB_ENCRYPTION_KEY should be 64 hex chars."
    log_ok "Environment configuration validated."
}

build_images() {
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"
    docker compose build 2>&1 | while read -r line; do echo "  $line"; done
    log_ok "Docker images built."
}

start_infrastructure() {
    log_info "Starting infrastructure services (postgres, redis)..."
    cd "$PROJECT_ROOT"
    docker compose up -d db redis

    log_info "Waiting for PostgreSQL..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker compose exec db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
            log_ok "PostgreSQL is ready."; break
        fi
        retries=$((retries - 1)); sleep 2
    done
    [ $retries -eq 0 ] && { log_error "PostgreSQL failed to start."; exit 1; }

    log_info "Waiting for Redis..."
    retries=30
    while [ $retries -gt 0 ]; do
        if docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
            log_ok "Redis is ready."; break
        fi
        retries=$((retries - 1)); sleep 2
    done
    [ $retries -eq 0 ] && { log_error "Redis failed to start."; exit 1; }
}

run_migrations() {
    log_info "Running database migrations..."
    cd "$PROJECT_ROOT"
    docker compose build api > /dev/null 2>&1
    docker compose run --rm api sh -c "alembic upgrade head" 2>&1 | while read -r line; do echo "  $line"; done
    log_ok "Database migrations applied."
}

seed_brokers() {
    log_info "Seeding broker playbooks..."
    cd "$PROJECT_ROOT"
    docker compose run --rm api python scripts/seed_brokers.py 2>&1 | while read -r line; do echo "  $line"; done
    log_ok "Broker playbooks seeded."
}

create_admin() {
    log_info "Creating admin user..."
    cd "$PROJECT_ROOT"

    docker compose run --rm api python -c "
import asyncio, sys
sys.path.insert(0, '/app')
from database import AsyncSessionLocal
from models.auth import Profile
from security import hash_password

async def main():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(Profile).where(Profile.username == '$ADMIN_USERNAME'))
        if result.scalar_one_or_none():
            print('Admin user already exists.')
            return
        admin = Profile(
            username='$ADMIN_USERNAME',
            password_hash=hash_password('$ADMIN_PASSWORD'),
            role='admin',
            active=True
        )
        session.add(admin)
        await session.commit()
        print('Admin user created successfully.')

asyncio.run(main())
" 2>&1 | while read -r line; do echo "  $line"; done

    log_ok "Admin user ready."
}

start_all_services() {
    log_info "Starting all OpenDataRemoval services..."
    cd "$PROJECT_ROOT"
    docker compose up -d

    echo ""
    log_ok "All services started!"
    echo ""
    log_info "OpenDataRemoval is running:"
    echo "  API:       http://localhost:8000"
    echo "  Docs:      http://localhost:8000/docs"
    echo "  Frontend:  http://localhost:3000"
    echo "  n8n:       http://localhost:5678"
    echo ""
    log_info "Useful commands:"
    echo "  docker compose logs -f api      # Watch API logs"
    echo "  docker compose logs -f worker   # Watch worker logs"
    echo "  docker compose down             # Stop all services"
    echo ""
}

main() {
    echo ""
    log_info "========================================"
    log_info "  OpenDataRemoval Environment Bootstrap"
    log_info "========================================"
    echo ""
    validate_env
    build_images
    start_infrastructure
    run_migrations
    seed_brokers
    create_admin
    start_all_services
    echo ""
    log_ok "OpenDataRemoval setup complete! 🎉"
    echo ""
}

main "$@"