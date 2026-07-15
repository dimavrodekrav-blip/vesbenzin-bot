import sqlite3
from typing import Any

from config import DB_PATH, logger


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def init_db(self) -> None:
        conn = self._conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                captcha_passed INTEGER DEFAULT 0,
                notifications_enabled INTEGER DEFAULT 1,
                snooze_until TEXT,
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_filters (
                user_id INTEGER NOT NULL,
                filter_type TEXT NOT NULL,
                filter_value TEXT NOT NULL,
                PRIMARY KEY (user_id, filter_type, filter_value)
            );

            CREATE TABLE IF NOT EXISTS stations (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                name TEXT NOT NULL,
                address TEXT,
                area_key TEXT NOT NULL,
                network_key TEXT,
                lat REAL,
                lon REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS station_status (
                station_id TEXT NOT NULL,
                fuel_key TEXT NOT NULL,
                status_key TEXT NOT NULL,
                queue_hint TEXT DEFAULT '',
                limit_hint TEXT DEFAULT '',
                source_status TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (station_id, fuel_key)
            );

            CREATE TABLE IF NOT EXISTS notify_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                station_id TEXT NOT NULL,
                fuel_key TEXT NOT NULL,
                status_key TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS push_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                station_id TEXT NOT NULL,
                fuel_key TEXT NOT NULL,
                verdict TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS crowd_status (
                station_id TEXT NOT NULL,
                fuel_key TEXT NOT NULL,
                status_key TEXT NOT NULL,
                confirmations INTEGER DEFAULT 0,
                denials INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (station_id, fuel_key)
            );

            CREATE INDEX IF NOT EXISTS idx_notify_log_lookup
                ON notify_log(user_id, station_id, fuel_key, sent_at);
            CREATE INDEX IF NOT EXISTS idx_stations_area
                ON stations(area_key);
            """
        )
        conn.commit()
        conn.close()
        logger.info("DB ready: %s", self.db_path)

    def upsert_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        referrer_id: int | None = None,
    ) -> None:
        conn = self._conn()
        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, referrer_id, last_active_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_active_at = CURRENT_TIMESTAMP,
                referrer_id = COALESCE(users.referrer_id, excluded.referrer_id)
            """,
            (user_id, username, first_name, referrer_id),
        )
        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        conn = self._conn()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def set_captcha_passed(self, user_id: int) -> None:
        conn = self._conn()
        conn.execute("UPDATE users SET captcha_passed = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def set_notifications(self, user_id: int, enabled: bool) -> None:
        conn = self._conn()
        conn.execute(
            "UPDATE users SET notifications_enabled = ? WHERE user_id = ?",
            (1 if enabled else 0, user_id),
        )
        conn.commit()
        conn.close()

    def set_snooze(self, user_id: int, hours: int) -> None:
        conn = self._conn()
        conn.execute(
            "UPDATE users SET snooze_until = datetime('now', ?) WHERE user_id = ?",
            (f"+{hours} hours", user_id),
        )
        conn.commit()
        conn.close()

    def is_snoozed(self, user_id: int) -> bool:
        conn = self._conn()
        row = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ? AND snooze_until > datetime('now')",
            (user_id,),
        ).fetchone()
        conn.close()
        return row is not None

    def toggle_filter(self, user_id: int, filter_type: str, value: str) -> bool:
        conn = self._conn()
        exists = conn.execute(
            "SELECT 1 FROM user_filters WHERE user_id=? AND filter_type=? AND filter_value=?",
            (user_id, filter_type, value),
        ).fetchone()
        if exists:
            conn.execute(
                "DELETE FROM user_filters WHERE user_id=? AND filter_type=? AND filter_value=?",
                (user_id, filter_type, value),
            )
            conn.commit()
            conn.close()
            return False
        conn.execute(
            "INSERT INTO user_filters (user_id, filter_type, filter_value) VALUES (?, ?, ?)",
            (user_id, filter_type, value),
        )
        conn.commit()
        conn.close()
        return True

    def get_filters(self, user_id: int, filter_type: str) -> list[str]:
        conn = self._conn()
        rows = conn.execute(
            """
            SELECT filter_value FROM user_filters
            WHERE user_id = ? AND filter_type = ?
            ORDER BY filter_value
            """,
            (user_id, filter_type),
        ).fetchall()
        conn.close()
        return [r["filter_value"] for r in rows]

    def get_settings(self, user_id: int) -> dict[str, Any]:
        user = self.get_user(user_id) or {}
        return {
            "areas": self.get_filters(user_id, "area"),
            "fuels": self.get_filters(user_id, "fuel"),
            "statuses": self.get_filters(user_id, "status"),
            "networks": self.get_filters(user_id, "network"),
            "notifications_enabled": bool(user.get("notifications_enabled", 1)),
        }

    def get_subscribed_users(self) -> list[dict[str, Any]]:
        conn = self._conn()
        rows = conn.execute(
            """
            SELECT * FROM users
            WHERE notifications_enabled = 1
              AND captcha_passed = 1
              AND (snooze_until IS NULL OR snooze_until <= datetime('now'))
            """
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def upsert_station(self, **kwargs: Any) -> None:
        conn = self._conn()
        conn.execute(
            """
            INSERT INTO stations (id, source, name, address, area_key, network_key, lat, lon, updated_at)
            VALUES (:id, :source, :name, :address, :area_key, :network_key, :lat, :lon, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                source=excluded.source, name=excluded.name, address=excluded.address,
                area_key=excluded.area_key, network_key=excluded.network_key,
                lat=excluded.lat, lon=excluded.lon, updated_at=CURRENT_TIMESTAMP
            """,
            kwargs,
        )
        conn.commit()
        conn.close()

    def upsert_status(self, **kwargs: Any) -> str | None:
        conn = self._conn()
        old = conn.execute(
            "SELECT status_key FROM station_status WHERE station_id=? AND fuel_key=?",
            (kwargs["station_id"], kwargs["fuel_key"]),
        ).fetchone()
        old_status = old["status_key"] if old else None
        conn.execute(
            """
            INSERT INTO station_status
                (station_id, fuel_key, status_key, queue_hint, limit_hint, source_status, updated_at)
            VALUES
                (:station_id, :fuel_key, :status_key, :queue_hint, :limit_hint, :source_status, CURRENT_TIMESTAMP)
            ON CONFLICT(station_id, fuel_key) DO UPDATE SET
                status_key=excluded.status_key, queue_hint=excluded.queue_hint,
                limit_hint=excluded.limit_hint, source_status=excluded.source_status,
                updated_at=CURRENT_TIMESTAMP
            """,
            kwargs,
        )
        conn.commit()
        conn.close()
        return old_status

    def get_matching_stations(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        areas = self.get_filters(user_id, "area")
        fuels = self.get_filters(user_id, "fuel")
        statuses = self.get_filters(user_id, "status")
        networks = self.get_filters(user_id, "network")
        if not areas or not fuels or not statuses:
            return []

        params: list[Any] = [*areas, *fuels, *statuses]
        network_sql = ""
        if networks:
            network_sql = f"AND s.network_key IN ({','.join('?' * len(networks))})"
            params.extend(networks)

        conn = self._conn()
        rows = conn.execute(
            f"""
            SELECT s.*, st.fuel_key, st.status_key, st.queue_hint, st.limit_hint,
                   st.source_status, st.updated_at AS status_updated
            FROM stations s
            JOIN station_status st ON st.station_id = s.id
            WHERE s.area_key IN ({','.join('?' * len(areas))})
              AND st.fuel_key IN ({','.join('?' * len(fuels))})
              AND st.status_key IN ({','.join('?' * len(statuses))})
              {network_sql}
            ORDER BY st.updated_at DESC
            LIMIT ?
            """,
            [*params, limit],
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def was_notified_recently(self, user_id: int, station_id: str, fuel_key: str, hours: int) -> bool:
        conn = self._conn()
        row = conn.execute(
            """
            SELECT 1 FROM notify_log
            WHERE user_id=? AND station_id=? AND fuel_key=?
              AND sent_at >= datetime('now', ?)
            """,
            (user_id, station_id, fuel_key, f"-{hours} hours"),
        ).fetchone()
        conn.close()
        return row is not None

    def log_notification(self, user_id: int, station_id: str, fuel_key: str, status_key: str) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT INTO notify_log (user_id, station_id, fuel_key, status_key) VALUES (?, ?, ?, ?)",
            (user_id, station_id, fuel_key, status_key),
        )
        conn.commit()
        conn.close()

    def log_push_feedback(self, user_id: int, station_id: str, fuel_key: str, verdict: str) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT INTO push_feedback (user_id, station_id, fuel_key, verdict) VALUES (?, ?, ?, ?)",
            (user_id, station_id, fuel_key, verdict),
        )
        conn.commit()
        conn.close()

    def get_station_snapshot(self, station_id: str, fuel_key: str) -> dict[str, Any] | None:
        conn = self._conn()
        row = conn.execute(
            """
            SELECT s.*, st.fuel_key, st.status_key, st.queue_hint, st.limit_hint,
                   st.source_status, st.updated_at AS status_updated
            FROM stations s
            JOIN station_status st ON st.station_id = s.id
            WHERE s.id = ? AND st.fuel_key = ?
            """,
            (station_id, fuel_key),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def is_status_fresh(self, station_id: str, fuel_key: str, max_age_minutes: int) -> bool:
        conn = self._conn()
        row = conn.execute(
            """
            SELECT 1 FROM station_status
            WHERE station_id = ? AND fuel_key = ?
              AND updated_at >= datetime('now', ?)
            """,
            (station_id, fuel_key, f"-{max_age_minutes} minutes"),
        ).fetchone()
        conn.close()
        return row is not None

    def apply_crowd_feedback(self, station_id: str, fuel_key: str, verdict: str) -> None:
        """Краудсорс: подтверждения пользователей после push."""
        status_key = "free" if verdict == "confirmed" else "absent"
        conn = self._conn()
        if verdict == "confirmed":
            conn.execute(
                """
                INSERT INTO crowd_status (station_id, fuel_key, status_key, confirmations, denials)
                VALUES (?, ?, ?, 1, 0)
                ON CONFLICT(station_id, fuel_key) DO UPDATE SET
                    confirmations = crowd_status.confirmations + 1,
                    status_key = excluded.status_key,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (station_id, fuel_key, status_key),
            )
        else:
            conn.execute(
                """
                INSERT INTO crowd_status (station_id, fuel_key, status_key, confirmations, denials)
                VALUES (?, ?, ?, 0, 1)
                ON CONFLICT(station_id, fuel_key) DO UPDATE SET
                    denials = crowd_status.denials + 1,
                    status_key = excluded.status_key,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (station_id, fuel_key, status_key),
            )
        conn.execute(
            """
            INSERT INTO station_status
                (station_id, fuel_key, status_key, source_status, updated_at)
            VALUES (?, ?, ?, 'crowd', CURRENT_TIMESTAMP)
            ON CONFLICT(station_id, fuel_key) DO UPDATE SET
                status_key = excluded.status_key,
                source_status = 'crowd',
                updated_at = CURRENT_TIMESTAMP
            """,
            (station_id, fuel_key, status_key),
        )
        conn.commit()
        conn.close()

    def get_admin_stats(self) -> dict[str, int]:
        conn = self._conn()
        stats = {
            "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "active_subscribers": conn.execute(
                """
                SELECT COUNT(*) FROM users
                WHERE notifications_enabled = 1 AND captcha_passed = 1
                  AND (snooze_until IS NULL OR snooze_until <= datetime('now'))
                """
            ).fetchone()[0],
            "stations": conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0],
            "status_rows": conn.execute("SELECT COUNT(*) FROM station_status").fetchone()[0],
            "pushes_24h": conn.execute(
                "SELECT COUNT(*) FROM notify_log WHERE sent_at >= datetime('now', '-1 day')"
            ).fetchone()[0],
            "feedback_24h": conn.execute(
                "SELECT COUNT(*) FROM push_feedback WHERE created_at >= datetime('now', '-1 day')"
            ).fetchone()[0],
        }
        conn.close()
        return stats