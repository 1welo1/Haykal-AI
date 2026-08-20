"""
analytics.py — AI Bot Analytics
Async Redis analytics with SQLite fallback.
All operations are fire-and-forget: never block main request flow.
"""
import asyncio
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

async def _safe_redis_call(coro, fallback_fn=None):
    """
    Execute a Redis coroutine safely.
    On failure: logs error, calls fallback if provided.
    Never raises — analytics failure must never crash the main app.
    """
    try:
        return await coro
    except Exception as e:
        logger.error(f"Redis analytics error: {e}", exc_info=False)
        if fallback_fn:
            try:
                # Assuming fallback_fn returns a coroutine
                return await fallback_fn()
            except Exception as fb_err:
                logger.error(f"Fallback analytics error: {fb_err}")
        return None

async def log_new_conversation(phone_number: str) -> None:
    """Log a new conversation event."""
    from database import redis_client, analytics_fallback
    today = datetime.now().strftime("%Y-%m-%d")
    hour = f"{datetime.now().hour:02d}"

    await asyncio.gather(
        _safe_redis_call(
            redis_client.incr("conversations:total"),
            lambda: analytics_fallback.incr("conversations:total")
        ),
        _safe_redis_call(
            redis_client.incr(f"conversations:today:{today}"),
            lambda: analytics_fallback.incr(f"conversations:today:{today}")
        ),
        _safe_redis_call(
            redis_client.hincrby("activity_24h", hour, 1),
            lambda: analytics_fallback.hincrby("activity_24h", hour, 1)
        ),
        return_exceptions=True
    )

def normalize_category(category: str) -> str:
    """Normalize and group similar categories together."""
    cat = category.strip().lower()
    if any(kw in cat for kw in ["guitar", "جيتار", "جيتارات"]):
        return "جيتار"
    if any(kw in cat for kw in ["عود", "العود", "اعواد"]):
        return "عود"
    if any(kw in cat for kw in ["بيانو", "piano", "البيانو"]):
        return "بيانو"
    if any(kw in cat for kw in ["سماعة", "سماعات", "headphones", "audio", "speakers"]):
        return "سماعات"
    return category

async def log_query_category(category: str) -> None:
    """Log which product category was queried."""
    from database import redis_client, analytics_fallback
    normalized = normalize_category(category)
    key = f"categories:{normalized}"
    await _safe_redis_call(
        redis_client.incr(key),
        lambda: analytics_fallback.incr(key)
    )

async def log_city_query(city: str) -> None:
    """Log which city was queried."""
    from database import redis_client, analytics_fallback
    await _safe_redis_call(
        redis_client.hincrby("city_queries", city, 1),
        lambda: analytics_fallback.hincrby("city_queries", city, 1)
    )

async def log_response_time(ms: int) -> None:
    """Log response time for performance tracking."""
    from database import redis_client, analytics_fallback
    await asyncio.gather(
        _safe_redis_call(
            redis_client.lpush("response_times", str(ms)),
            lambda: analytics_fallback.lpush("response_times", str(ms))
        ),
        _safe_redis_call(
            redis_client.ltrim("response_times", 0, 99),
            lambda: analytics_fallback.ltrim("response_times", 0, 99)
        ),
        return_exceptions=True
    )

async def log_product_link_sent(product_name: str = "") -> None:
    """Log when a product purchase link is sent (conversion event)."""
    from database import redis_client, analytics_fallback
    await _safe_redis_call(
        redis_client.incr("conversions:total"),
        lambda: analytics_fallback.incr("conversions:total")
    )

async def log_injection_blocked() -> None:
    """Log prompt injection attempt blocked."""
    from database import redis_client, analytics_fallback
    await _safe_redis_call(
        redis_client.incr("security:injections_blocked"),
        lambda: analytics_fallback.incr("security:injections_blocked")
    )

async def log_chat_message(phone: str, message: str, sender: str) -> None:
    """Log latest chat messages for the dashboard context."""
    from database import redis_client, analytics_fallback
    timestamp = datetime.now().isoformat()
    msg_data = json.dumps({
        "sender": sender,
        "message": str(message)[:500],
        "timestamp": timestamp
    }, ensure_ascii=False)
    
    await asyncio.gather(
        _safe_redis_call(
            redis_client.lpush(f"chat_history:{phone}", msg_data),
            lambda: analytics_fallback.lpush(f"chat_history:{phone}", msg_data)
        ),
        _safe_redis_call(
            redis_client.ltrim(f"chat_history:{phone}", 0, 49),
            lambda: analytics_fallback.ltrim(f"chat_history:{phone}", 0, 49)
        ),
        _safe_redis_call(
            redis_client.hincrby("active_conversations", phone, 1),
            lambda: analytics_fallback.hincrby("active_conversations", phone, 1)
        ),
        return_exceptions=True
    )

async def get_recent_conversations(limit: int = 20) -> list:
    from database import redis_client, analytics_fallback
    
    async def safe_hgetall(key: str):
        try:
            return await redis_client.hgetall(key)
        except Exception:
            return await analytics_fallback.hgetall(key)

    async def safe_lrange(key: str, start: int, end: int):
        try:
            return await redis_client.lrange(key, start, end)
        except Exception:
            return await analytics_fallback.lrange(key, start, end)
            
    phones_dict = await safe_hgetall("active_conversations")
    if not phones_dict:
        return []
        
    conversations = []
    for phone_k, _ in phones_dict.items():
        phone = phone_k.decode() if isinstance(phone_k, bytes) else phone_k
        history = await safe_lrange(f"chat_history:{phone}", 0, 0)
        
        if history:
            last_msg_raw = history[0]
            if isinstance(last_msg_raw, bytes): last_msg_raw = last_msg_raw.decode()
            try:
                last_msg = json.loads(last_msg_raw)
                conversations.append({
                    "phone": phone,
                    "last_message": last_msg.get("message", ""),
                    "timestamp": last_msg.get("timestamp", ""),
                    "sender": last_msg.get("sender", "")
                })
            except Exception as e:
                logger.error(f"Error parsing chat history JSON: {e}")
                
    conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    return conversations[:limit]

async def get_all_metrics() -> dict:
    """Fetch all analytics metrics for dashboard display."""
    from database import redis_client, analytics_fallback

    today = datetime.now().strftime("%Y-%m-%d")
    metrics = {}

    async def safe_get(key: str, default=0):
        try:
            val = await redis_client.get(key)
            return int(val) if val else default
        except Exception:
            val = await analytics_fallback.get(key)
            return int(val) if val else default

    async def safe_lrange(key: str, start: int, end: int):
        try:
            return await redis_client.lrange(key, start, end)
        except Exception:
            return await analytics_fallback.lrange(key, start, end)
            
    async def safe_hgetall(key: str):
        try:
            return await redis_client.hgetall(key)
        except Exception:
            return await analytics_fallback.hgetall(key)

    metrics["total_conversations"] = await safe_get("conversations:total")
    metrics["conversations_today"] = await safe_get(f"conversations:today:{today}")
    metrics["total_conversions"] = await safe_get("conversions:total")
    metrics["injections_blocked"] = await safe_get("security:injections_blocked")

    times_raw = await safe_lrange("response_times", 0, 99)
    if times_raw:
        times = [int(t) for t in times_raw if str(t).isdigit() or (isinstance(t, bytes) and t.decode().isdigit())]
        metrics["avg_response_ms"] = round(sum(times) / len(times)) if times else 0
    else:
        metrics["avg_response_ms"] = 0
        
    # 3. Category distribution (Dynamic)
    top_cats = []
    try:
        from database import analytics_fallback
        from upstash_redis.asyncio import Redis as AsyncRedis
        is_real_redis = isinstance(redis_client, AsyncRedis)
    except ImportError:
        is_real_redis = False

    raw_pairs = []
    if is_real_redis:
        try:
            keys = await redis_client.keys("categories:*")
            if keys:
                vals = await redis_client.mget(keys)
                raw_pairs = [(k.decode().replace("categories:", "") if isinstance(k, bytes) else k.replace("categories:", ""), int(v or 0)) for k, v in zip(keys, vals)]
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            # Fallback to SQLite on Redis error
            raw_pairs = await analytics_fallback.get_top_by_prefix("categories:", limit=100)
    else:
        raw_pairs = await analytics_fallback.get_top_by_prefix("categories:", limit=100)
        
    # Group and merge raw pairs
    merged = {}
    for cat_name, val in raw_pairs:
        norm_name = normalize_category(cat_name)
        merged[norm_name] = merged.get(norm_name, 0) + val
        
    # Sort merged categories and take top 4
    sorted_cats = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    top_cats = sorted_cats[:4]
        
    cat_labels = [c[0] for c in top_cats]
    cat_data = [c[1] for c in top_cats]
    
    metrics["cat_labels"] = cat_labels
    metrics["cat_data"] = cat_data
    
    # 4. Hourly interaction (Line chart)
    activity = await safe_hgetall("activity_24h")
    # activity is dict of {hour_string: count_string}
    int_labels = []
    int_data = []
    for h in range(24):
        h_str = f"{h:02d}"
        int_labels.append(f"{h_str}:00")
        # Try finding in dict (could be bytes or string)
        val = 0
        for k, v in activity.items():
            k_dec = k.decode() if isinstance(k, bytes) else str(k)
            if k_dec == h_str or k_dec == str(h):
                val = int(v)
                break
        int_data.append(val)
        
    metrics["int_labels"] = int_labels
    metrics["int_data"] = int_data

    return metrics

