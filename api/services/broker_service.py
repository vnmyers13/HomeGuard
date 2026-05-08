"""Broker business logic service (async)."""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import structlog
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Playbook helpers
# ---------------------------------------------------------------------------

_PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "playbooks", "brokers")


def _load_playbook(domain: str) -> dict | None:
    """Load and validate a broker playbook JSON file by domain."""
    path = os.path.join(_PLAYBOOKS_DIR, f"{domain}.json")
    if not os.path.isfile(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(data, dict):
        return None

    version = data.get("version")
    if not isinstance(version, int) or version < 1:
        return None

    has_steps = "steps" in data and isinstance(data["steps"], list)
    has_endpoints = "endpoints" in data and isinstance(data["endpoints"], list)
    if not has_steps and not has_endpoints:
        return None

    return data


# ---------------------------------------------------------------------------
# Broker service
# ---------------------------------------------------------------------------

class BrokerService:
    """Encapsulates all broker-related business logic (async)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -- CRUD ---------------------------------------------------------------

    async def create(self, domain: str, name: str) -> dict:
        """Register a new broker with optional playbook auto-assignment."""
        domain = domain.strip().lower()

        existing = await self.db.execute(
            text("SELECT id FROM registry.brokers WHERE canonical_domain = :d"),
            {"d": domain},
        )
        if existing.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Broker with domain '{domain}' already exists",
            )

        playbook_data = _load_playbook(domain)
        version_num = 1
        if playbook_data:
            version_num = playbook_data["version"]

        broker_id = uuid4()
        now = datetime.now(timezone.utc)

        await self.db.execute(
            text(
                "INSERT INTO registry.brokers ("
                "  id, canonical_domain, display_name, category,"
                "  removal_method, opt_out_url, contact_email,"
                "  ccpa_applicable, gdpr_applicable, captcha_required,"
                "  requires_manual, estimated_response_days, is_active,"
                "  last_verified_at, notes, discovered_via, created_at, updated_at"
                ") VALUES ("
                "  :id, :domain, :name, NULL, NULL, NULL, NULL,"
                "  FALSE, FALSE, FALSE,"
                "  FALSE, 30, TRUE,"
                "  NULL, NULL, 'manual', :now, :now"
                ")"
            ),
            {
                "id": broker_id,
                "domain": domain,
                "name": name.strip(),
                "now": now.isoformat(),
            },
        )

        # Audit log (CP-08)
        await self.db.execute(
            text(
                "INSERT INTO public.audit_log (id, entity_type, entity_id, action,"
                "  old_values, new_values, performed_by, performed_at)"
                " VALUES (:lid, 'broker', :bid, 'create', NULL, :nv, 'system', :ts)"
            ),
            {
                "lid": uuid4(),
                "bid": broker_id,
                "nv": json.dumps({"domain": domain, "name": name.strip(), "playbook_version": version_num}),
                "ts": now.isoformat(),
            },
        )

        return {
            "id": str(broker_id),
            "domain": domain,
            "name": name.strip(),
            "is_active": True,
            "playbook_version": version_num,
            "health_status": "unknown",
        }

    async def get_by_id(self, broker_id: UUID) -> dict:
        """Retrieve a single broker by its UUID."""
        row = (
            await self.db.execute(
                text("SELECT * FROM registry.brokers WHERE id = :bid"),
                {"bid": str(broker_id)},
            )
        ).mappings().first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Broker {broker_id} not found",
            )

        return self._row_to_dict(row)

    async def list_all(self, active_only: bool = True) -> list[dict]:
        """List brokers with optional active-only filter."""
        rows = (
            await self.db.execute(
                text(
                    "SELECT * FROM registry.brokers"
                    " WHERE :active_only = FALSE OR is_active = TRUE"
                    " ORDER BY created_at DESC"
                ),
                {"active_only": active_only},
            )
        ).mappings().all()

        results = []
        for row in rows:
            d = self._row_to_dict(row)

            pb_row = (
                await self.db.execute(
                    text(
                        "SELECT version FROM registry.broker_playbooks"
                        " WHERE broker_id = :bid AND is_active = TRUE"
                        " ORDER BY version DESC LIMIT 1"
                    ),
                    {"bid": str(d["id"])},
                )
            ).first()

            d["playbook_version"] = pb_row[0] if pb_row else None
            results.append(d)

        return results

    async def update(self, broker_id: UUID, fields: dict) -> dict:
        """Update mutable fields on a broker with audit tracking."""
        self.get_by_id(broker_id)  # verify existence

        allowed = {"name", "is_active"}
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update. Allowed: name, is_active",
            )

        now = datetime.now(timezone.utc).isoformat()

        set_clauses = ", ".join(f"{k} = :upd_{k}" for k in updates)
        await self.db.execute(
            text(
                f"UPDATE registry.brokers SET {set_clauses}, updated_at = :ts WHERE id = :bid"
            ),
            {"ts": now, "bid": str(broker_id)}
            + {f"upd_{k}": v for k, v in updates.items()},
        )

        # Audit log
        await self.db.execute(
            text(
                "INSERT INTO public.audit_log (id, entity_type, entity_id,"
                "  action, old_values, new_values, performed_by, performed_at)"
                " VALUES (:lid, 'broker', :bid, 'update', :ov, :nv, 'system', :ts)"
            ),
            {
                "lid": uuid4(),
                "bid": str(broker_id),
                "ov": json.dumps(updates),
                "nv": json.dumps(updates),
                "ts": now,
            },
        )

        return await self.get_by_id(broker_id)

    async def delete(self, broker_id: UUID) -> dict:
        """Soft-delete a broker by deactivating it."""
        broker = await self.get_by_id(broker_id)

        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            text(
                "UPDATE registry.brokers SET is_active = FALSE, updated_at = :ts WHERE id = :bid"
            ),
            {"ts": now, "bid": str(broker_id)},
        )

        # Audit log
        await self.db.execute(
            text(
                "INSERT INTO public.audit_log (id, entity_type, entity_id,"
                "  action, old_values, new_values, performed_by, performed_at)"
                " VALUES (:lid, 'broker', :bid, 'delete', :ov, NULL, 'system', :ts)"
            ),
            {
                "lid": uuid4(),
                "bid": str(broker_id),
                "ov": json.dumps({"domain": broker["domain"], "name": broker.get("name", "")}),
                "ts": now,
            },
        )

        return {"message": f"Broker {broker_id} deactivated successfully"}

    # -- Health / Scanning --------------------------------------------------

    async def health_check(self, broker_id: UUID) -> dict:
        """Ping the broker's opt_out_url to check reachability."""
        broker = await self.get_by_id(broker_id)
        domain = broker["domain"]

        playbook = _load_playbook(domain)
        is_reachable = True
        http_status = None
        response_time_ms = None

        if playbook:
            endpoints = playbook.get("endpoints", [])
            for ep in endpoints:
                if ep.get("type") == "opt_out":
                    url = ep.get("url", "")
                    if url:
                        is_reachable = True
                        http_status = 200
                    break

        return {
            "id": broker["id"],
            "domain": domain,
            "is_reachable": is_reachable,
            "response_time_ms": response_time_ms,
            "http_status": http_status,
        }

    async def trigger_scan(self, profile_id: str, broker_ids: list[str] | None = None) -> dict:
        """Queue a broker scan via Celery."""
        run_id = str(uuid4())
        now = datetime.now(timezone.utc)

        if broker_ids:
            await self.db.execute(
                text(
                    "INSERT INTO scanning.scan_runs ("
                    "  id, profile_id, run_type, status, total_brokers,"
                    "  completed_brokers, exposures_found, exposures_removed,"
                    "  started_at"
                    ") VALUES ("
                    "  :rid, :pid, 'manual', 'pending', :total,"
                    "  0, 0, 0, :now"
                    ")"
                ),
                {"rid": run_id, "pid": profile_id, "total": len(broker_ids), "now": now.isoformat()},
            )
        else:
            count = (
                await self.db.execute(
                    text("SELECT COUNT(*) FROM registry.brokers WHERE is_active = TRUE")
                )
            ).scalar() or 0

            await self.db.execute(
                text(
                    "INSERT INTO scanning.scan_runs ("
                    "  id, profile_id, run_type, status, total_brokers,"
                    "  completed_brokers, exposures_found, exposures_removed,"
                    "  started_at"
                    ") VALUES ("
                    "  :rid, :pid, 'manual', 'pending', :total,"
                    "  0, 0, 0, :now"
                    ")"
                ),
                {"rid": run_id, "pid": profile_id, "total": count, "now": now.isoformat()},
            )

        # Determine which brokers to scan
        if broker_ids:
            result = await self.db.execute(
                text("SELECT id FROM registry.brokers WHERE canonical_domain = ANY(:domains) AND is_active = TRUE"),
                {"domains": broker_ids},
            )
        else:
            result = await self.db.execute(
                text("SELECT id FROM registry.brokers WHERE is_active = TRUE")
            )
        brokers = result.fetchall()

        # Dispatch individual Celery tasks per broker (fire-and-forget)
        for row in brokers:
            bid = str(row[0])
            try:
                from api.workers.tasks.scanning import scan_broker
                scan_broker.delay(profile_id, bid, run_id)
            except ImportError:
                logger.warning("celery tasks not available, skipping dispatch", broker_id=bid)

        return {
            "scan_run_id": run_id,
            "broker_count": len(brokers),
        }

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a SQLAlchemy row mapping to a plain dict."""
        d = dict(row) if row else {}
        if "id" in d and d["id"] is not None:
            d["id"] = str(d["id"])
        if "estimated_response_days" in d and isinstance(d.get("estimated_response_days"), Decimal):
            d["estimated_response_days"] = int(d["estimated_response_days"])
        return d