#!/usr/bin/env python3
"""
Cleanup script for old sessions and logs.
Deletes sessions and logs older than specified retention period.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.session_manager import SessionManager
from app.core.logging import logger
import argparse
from datetime import datetime, timedelta
import shutil


def cleanup_logs(log_dir: str, retention_days: int):
    """Cleanup old log files"""
    log_path = Path(log_dir)
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    deleted_count = 0
    
    # Cleanup session logs
    sessions_dir = log_path / "sessions"
    if sessions_dir.exists():
        for session_dir in sessions_dir.iterdir():
            if session_dir.is_dir():
                # Check directory modification time
                mtime = datetime.fromtimestamp(session_dir.stat().st_mtime)
                if mtime < cutoff_date:
                    try:
                        shutil.rmtree(session_dir)
                        deleted_count += 1
                        logger.info(f"Deleted old session logs: {session_dir.name}")
                    except Exception as e:
                        logger.error(f"Failed to delete {session_dir}: {e}")
    
    # Cleanup system logs
    system_dir = log_path / "system"
    if system_dir.exists():
        for log_file in system_dir.glob("*.log.*"):  # Rotated logs
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff_date:
                try:
                    log_file.unlink()
                    logger.info(f"Deleted old system log: {log_file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {log_file}: {e}")
    
    return deleted_count


def main():
    parser = argparse.ArgumentParser(description="Cleanup old sessions and logs")
    parser.add_argument(
        "--days",
        type=int,
        default=10,
        help="Retention period in days (default: 10)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/sessions/sessions.db",
        help="Path to sessions database"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Path to logs directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    
    print(f"🧹 Session Cleanup Script")
    print(f"Retention period: {args.days} days")
    print(f"Database: {args.db_path}")
    print(f"Logs directory: {args.log_dir}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 50)
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")
        print("-" * 50)
    
    # Initialize session manager
    session_manager = SessionManager(db_path=args.db_path, log_dir=args.log_dir)
    
    # Get sessions to be deleted
    cutoff_date = datetime.utcnow() - timedelta(days=args.days)
    cutoff_str = cutoff_date.isoformat()
    
    # List old sessions
    all_sessions = session_manager.list_sessions(limit=1000)
    old_sessions = [
        s for s in all_sessions
        if s.get('updated_at', '') < cutoff_str
    ]
    
    print(f"📊 Found {len(old_sessions)} sessions older than {args.days} days")
    
    if old_sessions:
        print("\nSessions to be deleted:")
        for session in old_sessions[:10]:  # Show first 10
            print(f"  - {session['id'][:8]}... (updated: {session['updated_at'][:10]})")
        
        if len(old_sessions) > 10:
            print(f"  ... and {len(old_sessions) - 10} more")
    
    if not args.dry_run:
        # Cleanup sessions
        print(f"\n🗑️  Deleting old sessions...")
        deleted_count = session_manager.cleanup_old_sessions(days=args.days)
        print(f"✅ Deleted {deleted_count} sessions")
        
        # Cleanup logs
        print(f"\n🗑️  Cleaning up old logs...")
        log_deleted = cleanup_logs(args.log_dir, args.days)
        print(f"✅ Deleted {log_deleted} log directories")
        
        print(f"\n✨ Cleanup complete!")
        print(f"Total sessions deleted: {deleted_count}")
        print(f"Total log directories deleted: {log_deleted}")
    else:
        print(f"\n⚠️  Dry run complete - no changes made")
        print(f"Would delete {len(old_sessions)} sessions")


if __name__ == "__main__":
    main()
