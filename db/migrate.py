#!/usr/bin/env python3
"""Database migration runner for Ztrade.

Runs SQL migration files in order from db/migrations/ directory.
Tracks applied migrations in a migrations table.
"""
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.utils.logger import get_logger

logger = get_logger(__name__)


def get_database_url():
    """Get database URL from environment."""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://ztrade:ztrade_dev_password@localhost:5432/ztrade'
    )


def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_file VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    conn.commit()
    logger.info("Migrations tracking table ready")


def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    with conn.cursor() as cur:
        cur.execute("SELECT migration_file FROM schema_migrations ORDER BY id")
        return {row[0] for row in cur.fetchall()}


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
        # Execute migration
        with conn.cursor() as cur:
            cur.execute(sql)

        # Record migration
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO schema_migrations (migration_file) VALUES (%s)",
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

    database_url = get_database_url()
    logger.info(f"Connecting to database...")

    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

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
