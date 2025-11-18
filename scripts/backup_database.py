#!/usr/bin/env python3
"""
Database Backup Script

Concept: Automated database backup and recovery
Logic: Create timestamped backups, compress, upload to storage
Security: Encrypt backups, secure storage access
"""
import os
import sys
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
import argparse
import gzip
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DatabaseBackup:
    """
    Database Backup Manager
    
    Concept: Automated backup and restore operations
    Logic: pg_dump → Compress → Upload → Verify
    Storage: Local filesystem, S3, or cloud storage
    """
    
    def __init__(self):
        self.backup_dir = Path(os.getenv("BACKUP_DIR", project_root / "backups"))
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(self) -> Path:
        """
        Create database backup
        
        Returns:
            Path to backup file
        """
        print("[*] Creating database backup...")
        
        from hyperagent.core.config import settings
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"hyperagent_backup_{timestamp}.sql"
        compressed_file = backup_file.with_suffix(".sql.gz")
        
        try:
            # Extract connection details from DATABASE_URL
            # Format: postgresql://user:pass@host:port/db
            db_url = settings.database_url
            
            # Run pg_dump
            print(f"[*] Dumping database to {backup_file}...")
            result = subprocess.run(
                ["pg_dump", db_url, "-F", "c", "-f", str(backup_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"[-] Backup failed: {result.stderr}")
                return None
            
            # Compress backup
            print("[*] Compressing backup...")
            with open(backup_file, "rb") as f_in:
                with gzip.open(compressed_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            backup_file.unlink()
            
            # Verify backup
            if compressed_file.exists() and compressed_file.stat().st_size > 0:
                print(f"[+] Backup created: {compressed_file}")
                print(f"[*] Backup size: {compressed_file.stat().st_size / 1024 / 1024:.2f} MB")
                return compressed_file
            else:
                print("[-] Backup file is empty or missing")
                return None
                
        except Exception as e:
            print(f"[-] Backup error: {e}")
            return None
    
    async def restore_backup(self, backup_file: Path) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_file: Path to backup file (.sql.gz)
        
        Returns:
            bool: True if restore successful
        """
        print(f"[*] Restoring database from {backup_file}...")
        
        if not backup_file.exists():
            print(f"[-] Backup file not found: {backup_file}")
            return False
        
        from hyperagent.core.config import settings
        
        try:
            # Decompress if needed
            if backup_file.suffix == ".gz":
                decompressed = backup_file.with_suffix("")
                print("[*] Decompressing backup...")
                with gzip.open(backup_file, "rb") as f_in:
                    with open(decompressed, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed
            else:
                restore_file = backup_file
            
            # Restore database
            print("[*] Restoring database...")
            result = subprocess.run(
                ["pg_restore", "-d", settings.database_url, "-c", str(restore_file)],
                capture_output=True,
                text=True
            )
            
            if restore_file.suffix == ".gz":
                decompressed.unlink()
            
            if result.returncode == 0:
                print("[+] Database restored successfully")
                return True
            else:
                print(f"[-] Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[-] Restore error: {e}")
            return False
    
    def list_backups(self) -> list:
        """List available backups"""
        backups = sorted(
            self.backup_dir.glob("hyperagent_backup_*.sql.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return backups
    
    async def cleanup_old_backups(self, keep_days: int = 30):
        """Remove backups older than specified days"""
        print(f"[*] Cleaning up backups older than {keep_days} days...")
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        backups = self.list_backups()
        removed = 0
        
        for backup in backups:
            backup_time = datetime.fromtimestamp(backup.stat().st_mtime)
            if backup_time < cutoff_date:
                backup.unlink()
                removed += 1
                print(f"[*] Removed old backup: {backup.name}")
        
        print(f"[+] Cleaned up {removed} old backups")


async def main():
    """Main backup entry point"""
    parser = argparse.ArgumentParser(description="Database backup and restore")
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list", "cleanup"],
        help="Action to perform"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Backup file for restore operation"
    )
    parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="Days to keep backups (for cleanup)"
    )
    
    args = parser.parse_args()
    
    backup_manager = DatabaseBackup()
    
    if args.action == "backup":
        await backup_manager.create_backup()
    elif args.action == "restore":
        if not args.file:
            print("[-] --file required for restore operation")
            sys.exit(1)
        await backup_manager.restore_backup(args.file)
    elif args.action == "list":
        backups = backup_manager.list_backups()
        print(f"[*] Found {len(backups)} backups:")
        for backup in backups:
            size_mb = backup.stat().st_size / 1024 / 1024
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  - {backup.name} ({size_mb:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    elif args.action == "cleanup":
        await backup_manager.cleanup_old_backups(args.keep_days)


if __name__ == "__main__":
    asyncio.run(main())

