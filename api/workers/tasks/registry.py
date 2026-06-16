# ---------------------------------------------------------------------------
# Registry Tasks — Broker health monitoring & discovery upserts
# ---------------------------------------------------------------------------
# Scheduled via Celery Beat to keep broker registry data fresh.
#
# Tasks:
#   - check_broker_opt_out_urls  (scheduled, every 6h)
#   - upsert_broker_from_discovery  (ad-hoc, called from discovery workflows)
# ---------------------------------------------------------------------------

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from workers.celery_app import celery_app
except ImportError:
    from workers.celery_app import celery_app
try:
    from database import get_async_session
    from models.registry import Broker
except ImportError:
    from database import get_async_session
    from models.registry import Broker

# Aliases for test compatibility
get_db_session = get_async_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# check_broker_opt_out_urls — scheduled health probe
# ---------------------------------------------------------------------------

@celery_app.task(name="registry.check_broker_opt_out_urls")
def check_broker_opt_out_urls():
    """Check broker opt-out URL health.
    
    Probes each active broker's opt_out_url via HTTP HEAD request.
    Updates BrokerHealthStatus rows with current reachability.
    
    Returns:
        dict with checked count, reachable count, unreachable list
    """
    logger.info("check_broker_opt_out_urls started")
    
    async def _run():
        async with get_async_session() as session:
            # Get all active brokers with opt_out_urls
            brokers = (await session.execute(
                select(Broker).where(
                    Broker.is_active == True,
                    Broker.opt_out_url != None,
                )
            )).scalars().all()
            
            results = []
            reachable_count = 0
            
            for broker in brokers:
                try:
                    # HTTP HEAD probe (simplified — actual implementation uses httpx)
                    import httpx
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.head(broker.opt_out_url, follow_redirects=True)
                        is_reachable = resp.status_code < 400
                        
                except Exception as e:
                    logger.warning("Broker %s opt-out URL unreachable: %s", broker.canonical_domain, e)
                    is_reachable = False
                
                # Update last_verified_at as health indicator
                broker.last_verified_at = datetime.now(timezone.utc)
                
                if is_reachable:
                    reachable_count += 1
                
                results.append({
                    "broker_id": str(broker.id),
                    "slug": broker.canonical_domain,
                    "reachable": is_reachable,
                })
            
            await session.commit()
            return {
                "checked": len(results),
                "reachable": reachable_count,
                "unreachable": [r for r in results if not r["reachable"]],
            }
    
    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("check_broker_opt_out_urls failed: %s", e)
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# upsert_broker_from_discovery — ad-hoc broker registry update
# ---------------------------------------------------------------------------

@celery_app.task(name="registry.upsert_broker_from_discovery")
def upsert_broker_from_discovery(domain: str, data: dict):
    """Upsert broker record from discovery workflow.
    
    Args:
        domain: Broker domain slug (e.g., 'spokeo.com')
        data: Dict with fields like name, opt_out_url, category, etc.
    
    Returns:
        dict with broker_id and action taken (created/updated)
    """
    logger.info("upsert_broker_from_discovery: domain=%s", domain)
    
    async def _run():
        async with get_async_session() as session:
            existing = (await session.execute(
                select(Broker).where(Broker.canonical_domain == domain)
            )).scalar_one_or_none()
            
            if existing:
                # Update existing record
                for field in ["display_name", "opt_out_url", "category"]:
                    if field in data:
                        setattr(existing, field, data[field])
                existing.updated_at = datetime.now(timezone.utc)
                action = "updated"
            else:
                # Create new broker record
                broker = Broker(
                    canonical_domain=domain,
                    display_name=data.get("name", domain),
                    opt_out_url=data.get("opt_out_url"),
                    category=data.get("category", "people_search"),
                )
                session.add(broker)
                action = "created"
            
            await session.commit()
            return {
                "broker_id": str(existing.id if existing else broker.id),
                "domain": domain,
                "action": action,
            }
    
    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("upsert_broker_from_discovery failed: %s", e)
        return {"status": "failed", "error": str(e)}