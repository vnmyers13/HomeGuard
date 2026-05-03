"""
Seed broker registry from playbook JSON files.
Loads each playbook from playbooks/brokers/, validates against schema,
and upserts into registry.brokers + registry.broker_playbooks.
"""
import asyncio
import glob
import json
import os
import sys
from datetime import datetime

# Ensure /app is in path for docker container execution
sys.path.insert(0, "/app")

import jsonschema
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

# Allow running inside docker container where api/ is not in path
try:
    from api.database import engine, Base
    from api.models.registry import Broker, BrokerPlaybook
except ImportError:
    from database import engine, Base
    from models.registry import Broker, BrokerPlaybook


SCHEMA_PATH = os.environ.get("SCHEMA_PATH", "playbooks/schema.json")
BROKER_DIR = os.environ.get("BROKER_DIR", "playbooks/brokers")


def load_schema(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def validate_playbook(playbook: dict, schema: dict) -> bool:
    try:
        jsonschema.validate(instance=playbook, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"  INVALID: {e.message}")
        return False


async def seed_brokers():
    schema = load_schema(SCHEMA_PATH)
    playbook_files = sorted(glob.glob(os.path.join(BROKER_DIR, "*.json")))
    print(f"Found {len(playbook_files)} playbook files in {BROKER_DIR}")

    if not playbook_files:
        print("No playbook files found. Nothing to seed.")
        return

    seeded = 0
    skipped = 0

    async with engine.begin() as conn:
        for filepath in playbook_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r") as f:
                    playbook_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  SKIP {filename}: JSON parse error: {e}")
                skipped += 1
                continue

            if not validate_playbook(playbook_data, schema):
                print(f"  SKIP {filename}: schema validation failed")
                skipped += 1
                continue

            domain = playbook_data.get("canonical_domain", "")
            if not domain:
                print(f"  SKIP {filename}: no canonical_domain")
                skipped += 1
                continue

            # Upsert broker using actual columns
            upsert_broker = text("""
                INSERT INTO registry.brokers (
                    canonical_domain, display_name, removal_method, opt_out_url,
                    estimated_response_days, is_active, discovered_via,
                    ccpa_applicable, gdpr_applicable, captcha_required, requires_manual,
                    created_at, updated_at
                ) VALUES (:domain, :name, :method, :opt_url, :est_days, true, 'manual_seed',
                         true, true, false, false, now(), now())
                ON CONFLICT (canonical_domain) DO UPDATE SET
                    estimated_response_days = excluded.estimated_response_days,
                    opt_out_url = excluded.opt_out_url,
                    is_active = true,
                    updated_at = now()
            """)

            # Derive removal_method from playbook phases
            phases = playbook_data.get("phases", [])
            removal_method = "email"
            for phase in phases:
                if phase.get("name") == "opt_out":
                    removal_method = "web_form"
                    break

            result = await conn.execute(
                upsert_broker,
                {
                    "domain": domain,
                    "name": domain.replace(".", " ").title(),
                    "method": removal_method,
                    "opt_url": playbook_data.get("opt_out_url_template", ""),
                    "est_days": playbook_data.get("estimated_response_days", 14),
                },
            )

            # Get broker_id
            broker_query = text("SELECT id FROM registry.brokers WHERE canonical_domain = :domain")
            broker_row = (await conn.execute(broker_query, {"domain": domain})).fetchone()
            if not broker_row:
                print(f"  ERROR: could not find broker for {domain}")
                skipped += 1
                continue

            broker_id = broker_row[0]

            # Insert playbook version
            # Get current max version
            version_query = text(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM registry.broker_playbooks WHERE broker_id = :bid"
            )
            ver_row = (await conn.execute(version_query, {"bid": broker_id})).fetchone()
            new_version = ver_row[0] if ver_row else 1

            # Deactivate previous playbooks
            deactivate = text(
                "UPDATE registry.broker_playbooks SET is_active = false WHERE broker_id = :bid AND is_active = true"
            )
            await conn.execute(deactivate, {"bid": broker_id})

            # Insert new playbook
            insert_playbook = text("""
                INSERT INTO registry.broker_playbooks (
                    broker_id, version, is_active, playbook_json, created_by, created_at
                ) VALUES (:bid, :ver, true, CAST(:pj AS jsonb), 'seed_script', now())
            """)
            await conn.execute(
                insert_playbook,
                {
                    "bid": broker_id,
                    "ver": new_version,
                    "pj": json.dumps(playbook_data),
                },
            )

            print(f"  SEED {filename}: {domain} (playbook v{new_version})")
            seeded += 1

    print(f"\n{seeded} brokers seeded, {skipped} skipped")


if __name__ == "__main__":
    asyncio.run(seed_brokers())