"""
🦞 Universal Skill Loader - OpenClaw Assimilation Engine
=========================================================

This module parses SKILL.md files from the harvested OpenClaw skills
and makes them available to ZARA's brain. Skills are "dormant" by 
default and only activate when explicitly enabled.

Safety:
- NO external code execution from skills
- Skills are documentation that ZARA's brain interprets
- All actual execution happens through ZARA's secure action system
"""

import os
import re
import yaml
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Skills that are active by default (the "Starter Pack")
DEFAULT_ENABLED_SKILLS: Set[str] = {
    "spotify-player",
    "weather",
    "github",
}

# Skills directory relative to ZARA root
SKILLS_DIR = Path(__file__).parent / "skills"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class SkillStatus(Enum):
    """Skill activation status."""
    DORMANT = "dormant"       # Available but not loaded
    ACTIVE = "active"         # Loaded and ready to use
    UNAVAILABLE = "unavailable"  # Missing dependencies
    ERROR = "error"           # Failed to parse


@dataclass
class SkillRequirements:
    """What a skill needs to function."""
    bins: List[str] = field(default_factory=list)      # Required CLI tools
    any_bins: List[str] = field(default_factory=list)  # Any one of these
    env_vars: List[str] = field(default_factory=list)  # Required env vars


@dataclass
class SkillMetadata:
    """Parsed SKILL.md frontmatter."""
    name: str
    description: str
    homepage: Optional[str] = None
    emoji: str = "🔧"
    requirements: SkillRequirements = field(default_factory=SkillRequirements)
    install_instructions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Skill:
    """A complete skill definition."""
    name: str
    path: Path
    metadata: SkillMetadata
    content: str  # The full markdown instructions
    status: SkillStatus = SkillStatus.DORMANT
    missing_deps: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# SKILL PARSER
# ═══════════════════════════════════════════════════════════════════════════════

class SkillParser:
    """Parses SKILL.md files into structured Skill objects."""
    
    # Regex to extract YAML frontmatter
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )
    
    def parse_file(self, skill_path: Path) -> Optional[Skill]:
        """Parse a single SKILL.md file."""
        try:
            content = skill_path.read_text(encoding='utf-8')
            return self._parse_content(skill_path.parent.name, skill_path, content)
        except Exception as e:
            logger.error(f"Failed to parse {skill_path}: {e}")
            return None
    
    def _parse_content(self, name: str, path: Path, content: str) -> Optional[Skill]:
        """Parse SKILL.md content into a Skill object."""
        match = self.FRONTMATTER_PATTERN.match(content)
        
        if not match:
            # No frontmatter, treat entire content as instructions
            metadata = SkillMetadata(
                name=name,
                description=f"Skill: {name}",
            )
            return Skill(
                name=name,
                path=path,
                metadata=metadata,
                content=content,
            )
        
        frontmatter_str = match.group(1)
        body = match.group(2)
        
        try:
            frontmatter = yaml.safe_load(frontmatter_str, )
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {path}: {e}")
            frontmatter = {}
        
        # Extract metadata
        metadata = self._extract_metadata(name, frontmatter)
        
        return Skill(
            name=name,
            path=path,
            metadata=metadata,
            content=body,
        )
    
    def _extract_metadata(self, name: str, fm: Dict[str, Any]) -> SkillMetadata:
        """Extract structured metadata from frontmatter."""
        openclaw_meta = fm.get("metadata", {}).get("openclaw", {})
        
        # Parse requirements
        requires = openclaw_meta.get("requires", {})
        requirements = SkillRequirements(
            bins=requires.get("bins", []),
            any_bins=requires.get("anyBins", []),
            env_vars=requires.get("envVars", []),
        )
        
        return SkillMetadata(
            name=fm.get("name", name),
            description=fm.get("description", f"Skill: {name}"),
            homepage=fm.get("homepage"),
            emoji=openclaw_meta.get("emoji", "🔧"),
            requirements=requirements,
            install_instructions=openclaw_meta.get("install", []),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCY CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class DependencyChecker:
    """Checks if skill dependencies are available on the system."""
    
    def __init__(self):
        self._bin_cache: Dict[str, bool] = {}
    
    def check_skill(self, skill: Skill) -> tuple[bool, List[str]]:
        """
        Check if a skill's dependencies are met.
        Returns (is_available, list_of_missing_deps).
        """
        missing = []
        reqs = skill.metadata.requirements
        
        # Check required bins
        for bin_name in reqs.bins:
            if not self._check_bin(bin_name):
                missing.append(f"bin:{bin_name}")
        
        # Check any_bins (at least one must exist)
        if reqs.any_bins:
            has_any = any(self._check_bin(b) for b in reqs.any_bins)
            if not has_any:
                missing.append(f"any_bin:[{', '.join(reqs.any_bins)}]")
        
        # Check env vars
        for var in reqs.env_vars:
            if not os.environ.get(var):
                missing.append(f"env:{var}")
        
        return len(missing) == 0, missing
    
    def _check_bin(self, bin_name: str) -> bool:
        """Check if a binary is available in PATH."""
        if bin_name in self._bin_cache:
            return self._bin_cache[bin_name]
        
        try:
            # Use 'where' on Windows, 'which' on Unix
            cmd = "where" if os.name == "nt" else "which"
            result = subprocess.run(
                [cmd, bin_name],
                capture_output=True,
                timeout=5,
            )
            available = result.returncode == 0
        except Exception:
            available = False
        
        self._bin_cache[bin_name] = available
        return available


# ═══════════════════════════════════════════════════════════════════════════════
# SKILL MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class SkillManager:
    """
    The main interface for ZARA to interact with skills.
    
    Usage:
        manager = SkillManager()
        manager.scan_skills()
        
        # Get active skills for brain injection
        active = manager.get_active_skills()
        
        # Enable/disable skills dynamically
        manager.enable_skill("notion")
        manager.disable_skill("spotify-player")
    """
    
    def __init__(
        self,
        skills_dir: Path = SKILLS_DIR,
        enabled_skills: Optional[Set[str]] = None,
    ):
        self.skills_dir = skills_dir
        self.enabled_skills = enabled_skills or DEFAULT_ENABLED_SKILLS.copy()
        self.skills: Dict[str, Skill] = {}
        
        self._parser = SkillParser()
        self._checker = DependencyChecker()
    
    def scan_skills(self) -> Dict[str, Skill]:
        """Scan the skills directory and parse all SKILL.md files."""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return {}
        
        for skill_folder in self.skills_dir.iterdir():
            if not skill_folder.is_dir():
                continue
            
            skill_file = skill_folder / "SKILL.md"
            if not skill_file.exists():
                continue
            
            skill = self._parser.parse_file(skill_file)
            if skill:
                self._update_skill_status(skill)
                self.skills[skill.name] = skill
        
        logger.info(f"Scanned {len(self.skills)} skills")
        return self.skills
    
    def _update_skill_status(self, skill: Skill) -> None:
        """Update skill status based on dependencies and enabled list."""
        available, missing = self._checker.check_skill(skill)
        skill.missing_deps = missing
        
        if not available:
            skill.status = SkillStatus.UNAVAILABLE
        elif skill.name in self.enabled_skills:
            skill.status = SkillStatus.ACTIVE
        else:
            skill.status = SkillStatus.DORMANT
    
    def enable_skill(self, skill_name: str) -> bool:
        """Enable a skill by name."""
        if skill_name not in self.skills:
            return False
        
        skill = self.skills[skill_name]
        self.enabled_skills.add(skill_name)
        self._update_skill_status(skill)
        
        logger.info(f"Enabled skill: {skill_name} ({skill.status.value})")
        return skill.status == SkillStatus.ACTIVE
    
    def disable_skill(self, skill_name: str) -> bool:
        """Disable a skill by name."""
        if skill_name not in self.skills:
            return False
        
        self.enabled_skills.discard(skill_name)
        skill = self.skills[skill_name]
        skill.status = SkillStatus.DORMANT
        
        logger.info(f"Disabled skill: {skill_name}")
        return True
    
    def get_active_skills(self) -> List[Skill]:
        """Get all currently active skills."""
        return [s for s in self.skills.values() if s.status == SkillStatus.ACTIVE]
    
    def get_dormant_skills(self) -> List[Skill]:
        """Get all dormant (available but not active) skills."""
        return [s for s in self.skills.values() if s.status == SkillStatus.DORMANT]
    
    def get_unavailable_skills(self) -> List[Skill]:
        """Get skills with missing dependencies."""
        return [s for s in self.skills.values() if s.status == SkillStatus.UNAVAILABLE]
    
    def get_skill_prompt(self, skill: Skill) -> str:
        """
        Generate a prompt injection for ZARA's brain.
        This is how ZARA learns to use the skill.
        """
        return f"""
## {skill.metadata.emoji} Skill: {skill.metadata.name}

**Description**: {skill.metadata.description}
{f"**Homepage**: {skill.metadata.homepage}" if skill.metadata.homepage else ""}

### Instructions:
{skill.content}
"""
    
    def get_all_skills_prompt(self) -> str:
        """Generate a combined prompt for all active skills."""
        active = self.get_active_skills()
        if not active:
            return ""
        
        prompts = [self.get_skill_prompt(s) for s in active]
        return "\n\n---\n\n".join(prompts)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of skill statuses."""
        return {
            "total": len(self.skills),
            "active": len(self.get_active_skills()),
            "dormant": len(self.get_dormant_skills()),
            "unavailable": len(self.get_unavailable_skills()),
            "active_skills": [s.name for s in self.get_active_skills()],
            "unavailable_skills": [
                {"name": s.name, "missing": s.missing_deps}
                for s in self.get_unavailable_skills()
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ZARA INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

# Global skill manager instance
_skill_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """Get or create the global skill manager."""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
        _skill_manager.scan_skills()
    return _skill_manager


def get_skills_for_brain() -> str:
    """
    Get the skill instructions to inject into ZARA's brain.
    Call this when building ZARA's system prompt.
    """
    manager = get_skill_manager()
    return manager.get_all_skills_prompt()


def list_available_skills() -> List[Dict[str, Any]]:
    """List all available skills with their status."""
    manager = get_skill_manager()
    return [
        {
            "name": s.name,
            "description": s.metadata.description,
            "emoji": s.metadata.emoji,
            "status": s.status.value,
            "missing_deps": s.missing_deps,
        }
        for s in manager.skills.values()
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🦞 OpenClaw Skill Assimilation Engine")
    print("=" * 50)
    
    manager = SkillManager()
    manager.scan_skills()
    
    status = manager.get_status_summary()
    print(f"\n📊 Skill Arsenal Status:")
    print(f"   Total Skills:     {status['total']}")
    print(f"   Active:           {status['active']}")
    print(f"   Dormant:          {status['dormant']}")
    print(f"   Unavailable:      {status['unavailable']}")
    
    print(f"\n✅ Active Skills:")
    for name in status['active_skills']:
        skill = manager.skills[name]
        print(f"   {skill.metadata.emoji} {name}: {skill.metadata.description}")
    
    if status['unavailable_skills']:
        print(f"\n⚠️ Unavailable Skills (missing deps):")
        for info in status['unavailable_skills'][:5]:  # Show first 5
            print(f"   ❌ {info['name']}: missing {info['missing']}")
    
    print("\n🧠 Skills ready for ZARA's brain injection!")
