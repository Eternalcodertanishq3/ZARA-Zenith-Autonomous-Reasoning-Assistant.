"""
ZARA Feature Deployer
Promotes tested code from sandbox to core directory.
"""
import shutil
import logging
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from config import ROOT_DIR

logger = logging.getLogger("ZARA_DEPLOY")

class Deployer:
    """
    Manages code promotion from sandbox (ghost folder) to production.
    Includes versioning and rollback capability.
    """
    
    def __init__(self):
        self.ghost_dir = ROOT_DIR / "ghost"
        self.core_dir = ROOT_DIR  # Main project directory
        self.backup_dir = ROOT_DIR / "backups"
        self.deployment_log = ROOT_DIR / "deployment_history.json"
        
        self.ghost_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("Deployer initialized.")
    
    def verify_code(self, file_path: Path) -> bool:
        """
        Verify code before deployment.
        Checks syntax and basic safety.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Syntax check
            compile(code, str(file_path), 'exec')
            
            # Safety check
            dangerous_patterns = [
                'os.system', 'subprocess.call', 'eval(', 'exec(',
                'rm -rf', 'shutil.rmtree', '__import__'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in code:
                    logger.warning(f"Dangerous pattern found: {pattern}")
                    return False
            
            return True
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def create_backup(self, target_path: Path) -> Optional[Path]:
        """
        Create backup of existing file before replacement.
        """
        if not target_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target_path.stem}_{timestamp}{target_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(target_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        
        return backup_path
    
    def deploy(self, source_file: str, target_location: str = None, 
               force: bool = False) -> Dict:
        """
        Deploy a file from ghost to production.
        """
        source_path = self.ghost_dir / source_file
        
        if not source_path.exists():
            return {
                "success": False,
                "error": f"Source file not found: {source_file}"
            }
        
        # Verify code
        if not force and not self.verify_code(source_path):
            return {
                "success": False,
                "error": "Code verification failed"
            }
        
        # Determine target
        if target_location:
            target_path = ROOT_DIR / target_location
        else:
            # Default: same name in root
            target_path = self.core_dir / source_file
        
        # Backup existing
        backup_path = self.create_backup(target_path)
        
        # Deploy
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            
            # Log deployment
            self._log_deployment(source_file, str(target_path), backup_path)
            
            logger.info(f"Deployed: {source_file} → {target_path}")
            
            return {
                "success": True,
                "source": str(source_path),
                "target": str(target_path),
                "backup": str(backup_path) if backup_path else None
            }
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def rollback(self, target_file: str) -> bool:
        """
        Rollback to the most recent backup.
        """
        target_path = Path(target_file)
        
        # Find latest backup
        backups = list(self.backup_dir.glob(f"{target_path.stem}_*{target_path.suffix}"))
        
        if not backups:
            logger.error(f"No backups found for {target_file}")
            return False
        
        # Sort by modification time, get latest
        latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
        
        try:
            shutil.copy2(latest_backup, target_path)
            logger.info(f"Rolled back: {target_path} from {latest_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def _log_deployment(self, source: str, target: str, backup: Optional[Path]):
        """Log deployment to history file."""
        import json
        
        history = []
        if self.deployment_log.exists():
            with open(self.deployment_log, 'r') as f:
                history = json.load(f)
        
        history.append({
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "target": target,
            "backup": str(backup) if backup else None
        })
        
        with open(self.deployment_log, 'w') as f:
            json.dump(history, f, indent=2)
    
    def list_ghost_files(self) -> List[str]:
        """List all files in ghost directory."""
        return [f.name for f in self.ghost_dir.glob("*.py")]
    
    def clean_ghost(self, older_than_days: int = 7):
        """Remove old files from ghost directory."""
        import time
        
        cutoff = time.time() - (older_than_days * 86400)
        
        for file_path in self.ghost_dir.glob("*"):
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                logger.info(f"Cleaned old ghost file: {file_path}")
