#!/usr/bin/env python3
"""Database migration runner for Ztrade (SQLite).

Runs SQL migration files in order from db/migrations/ directory.
Tracks applied migrations in a migrations table.
"""
import os
import sys
from pathlib import Path
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ztrade.core.logger import get_logger
from ztrade.core.database import get_database_path

logger = get_logger(__name__)


def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_file TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    logger.info("Migrations tracking table ready")


def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    cursor = conn.execute("SELECT migration_file FROM schema_migrations ORDER BY id")
    return {row[0] for row in cursor.fetchall()}


def get_pending_migrations(migrations_dir, applied):
    """Get list of pending migration files."""
    all_migrations = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith('.sql')
    ])
    return [m for m in all_migrations if m not in applied]


def apply_migration(conn, migrations_dir, migration_file):
    """Apply a single migration file."""
    migration_path = os.path.join(migrations_dir, migration_file)

    logger.info(f"Applying migration: {migration_file}")

    # Read migration SQL
    with open(migration_path, 'r') as f:
        sql = f.read()

    try:
        # Execute migration (may contain multiple statements)
        conn.executescript(sql)

        # Record migration
        conn.execute(
            "INSERT INTO schema_migrations (migration_file) VALUES (?)",
            (migration_file,)
        )

        conn.commit()
        logger.info(f"✅ Successfully applied: {migration_file}")
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Failed to apply {migration_file}: {e}")
        raise


def run_migrations(dry_run=False):
    """Run all pending migrations."""
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')

    if not os.path.exists(migrations_dir):
        logger.error(f"Migrations directory not found: {migrations_dir}")
        return False

    db_path = get_database_path()
    logger.info(f"Connecting to database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)

        # Ensure migrations table exists
        create_migrations_table(conn)

        # Get applied and pending migrations
        applied = get_applied_migrations(conn)
        pending = get_pending_migrations(migrations_dir, applied)

        if not pending:
            logger.info("✅ No pending migrations")
            return True

        logger.info(f"Found {len(pending)} pending migration(s)")

        if dry_run:
            logger.info("DRY RUN - Would apply:")
            for migration in pending:
                logger.info(f"  - {migration}")
            return True

        # Apply pending migrations
        for migration in pending:
            apply_migration(conn, migrations_dir, migration)

        logger.info(f"✅ All migrations applied successfully")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False

    finally:
        if 'conn' in locals():
            conn.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show pending migrations without applying'
    )

    args = parser.parse_args()

    success = run_migrations(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
