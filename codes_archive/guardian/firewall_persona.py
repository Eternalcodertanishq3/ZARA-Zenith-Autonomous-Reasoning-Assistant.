# """
# ZARA Firewall Persona - Enhanced Security Monitoring
# """
# import logging
# import psutil
# import threading
# import time
# import hashlib
# import re
# from typing import List, Dict, Optional, Callable, Set
# from dataclasses import dataclass, field
# from enum import Enum
# from collections import deque
# from datetime import datetime
#
# logger = logging.getLogger("ZARA_FIREWALL")
#
#
# class ThreatLevel(Enum):
#     NONE = 0
#     LOW = 1
#     MEDIUM = 2
#     HIGH = 3
#     CRITICAL = 4
#
#
# class ThreatCategory(Enum):
#     SUSPICIOUS_PROCESS = "suspicious_process"
#     NETWORK_ANOMALY = "network_anomaly"
#     RESOURCE_ABUSE = "resource_abuse"
#     FILE_SYSTEM = "file_system"
#     PRIVILEGE_ESCALATION = "privilege_escalation"
#     DATA_EXFILTRATION = "data_exfiltration"
#
#
# @dataclass
# class ThreatAlert:
#     """Detailed threat alert."""
#     level: ThreatLevel
#     category: ThreatCategory
#     description: str
#     timestamp: float
#     process_name: str = ""
#     process_id: int = 0
#     action_taken: str = ""
#     mitigated: bool = False
#     details: Dict = field(default_factory=dict)
#
#
# class FirewallPersona:
#     """
#     ZARA's security monitoring and defensive mode system.
#     Enhanced with:
#     - Advanced threat detection patterns
#     - Behavioral analysis
#     - Anomaly detection
#     - Automated responses
#     - Threat intelligence
#     - User protection messaging
#     """
#
#     def __init__(self, alert_callback: Optional[Callable] = None):
#         self.alert_callback = alert_callback
#         self.is_monitoring = False
#         self.threat_history: deque = deque(maxlen=500)
#         self.current_threat_level = ThreatLevel.NONE
#         self.defensive_mode = False
#
#         # Known threat signatures
#         self.suspicious_processes = {
#             # Malware patterns
#             "keylogger", "spyware", "trojan", "backdoor", "rat", "rootkit",
#             "mimikatz", "lazagne", "procdump", "pwdump",
#             # Suspicious command patterns
#             "powershell -enc", "powershell -e ", "cmd /c",
#             "wscript", "cscript", "mshta", "regsvr32 /s",
#             # Crypto miners
#             "xmrig", "minerd", "cgminer", "bfgminer",
#         }
#
#         # Process behavior baselines
#         self.process_baselines: Dict[str, Dict] = {}
#         self.baseline_window = 60  # seconds
#
#         # Network monitoring
#         self.allowed_destinations: Set[str] = {
#             "localhost", "127.0.0.1", "::1",
#             "python.org", "github.com", "huggingface.co",
#             "pypi.org", "googleapis.com", "microsoft.com"
#         }
#
#         self.suspicious_ports = {4444, 5555, 6666, 7777, 8888, 31337, 1337}
#
#         # Whitelisted safe processes (prevent false positives)
#         self.safe_processes = {
#             # NVIDIA/GPU
#             "nvcontainer.exe", "nvidia overlay.exe", "nvsphelper64.exe",
#             "nvdisplay.container.exe", "nvidia share.exe", "nvidia web helper.exe",
#             # Windows System
#             "wmiregistrationservice.exe", "wmiprvse.exe", "svchost.exe",
#             "csrss.exe", "lsass.exe", "services.exe", "smss.exe",
#             "powershell.exe", "cmd.exe", "conhost.exe", "explorer.exe",
#             # Development/IDE
#             "code.exe", "antigravity.exe", "python.exe", "node.exe",
#             "git.exe", "git-bash.exe", "devenv.exe", "idea64.exe",
#             # Common apps
#             "chrome.exe", "firefox.exe", "msedge.exe", "slack.exe",
#             "discord.exe", "spotify.exe", "steam.exe",
#         }
#
#         # Connection tracking
#         self.connection_history: deque = deque(maxlen=1000)
#
#         # Defensive responses
#         self.defensive_messages = {
#             ThreatLevel.LOW: [
#                 "Something seems a bit off. Keeping an eye on it.",
#                 "Minor anomaly detected. Don't worry, I'm watching.",
#             ],
#             ThreatLevel.MEDIUM: [
#                 "⚠️ I'm detecting some suspicious activity. Stay alert.",
#                 "Something doesn't feel right. I'm in protective mode now.",
#             ],
#             ThreatLevel.HIGH: [
#                 "🚨 Warning! I've detected a potential threat on your system!",
#                 "⚠️ High-risk activity detected! I'm switching to defensive mode.",
#             ],
#             ThreatLevel.CRITICAL: [
#                 "🚨 CRITICAL SECURITY ALERT! Immediate attention required!",
#                 "⛔ DANGER! I've detected critical security threats!",
#             ]
#         }
#
#         logger.info("Firewall Persona initialized.")
#
#     def enter_defensive_mode(self, reason: str = ""):
#         """Activate defensive behavior."""
#         if not self.defensive_mode:
#             self.defensive_mode = True
#             logger.warning(f"DEFENSIVE MODE ACTIVATED: {reason}")
#
#             if self.alert_callback:
#                 import random
#                 msg = random.choice(self.defensive_messages.get(
#                     self.current_threat_level, 
#                     self.defensive_messages[ThreatLevel.MEDIUM]
#                 ))
#                 self.alert_callback(msg + f"\n\nReason: {reason}")
#
#     def exit_defensive_mode(self):
#         """Deactivate defensive mode."""
#         if self.defensive_mode:
#             self.defensive_mode = False
#             logger.info("Defensive mode deactivated.")
#
#             if self.alert_callback:
#                 self.alert_callback(
#                     "✅ All clear! No more threats detected. "
#                     "Returning to normal mode. I'll keep watching."
#                 )
#
#     def get_defensive_response(self, normal_response: str) -> str:
#         """Modify response based on security state."""
#         if not self.defensive_mode:
#             return normal_response
#
#         prefixes = {
#             ThreatLevel.LOW: "[🔒 Vigilant] ",
#             ThreatLevel.MEDIUM: "[⚠️ Alert] ",
#             ThreatLevel.HIGH: "[🚨 High Alert] ",
#             ThreatLevel.CRITICAL: "[⛔ CRITICAL] ",
#         }
#
#         prefix = prefixes.get(self.current_threat_level, "[🔒] ")
#         return prefix + normal_response
#
#     def scan_processes(self) -> List[ThreatAlert]:
#         """Advanced process scanning."""
#         threats = []
#
#         try:
#             for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
#                 try:
#                     info = proc.info
#                     name = (info['name'] or "").lower()
#                     cmdline = " ".join(info['cmdline'] or []).lower()
#                     pid = info['pid']
#
#                     # Skip whitelisted safe processes
#                     if name in self.safe_processes:
#                         continue
#
#                     # Check against signatures
#                     for sig in self.suspicious_processes:
#                         if sig in name or sig in cmdline:
#                             threat = ThreatAlert(
#                                 level=ThreatLevel.HIGH,
#                                 category=ThreatCategory.SUSPICIOUS_PROCESS,
#                                 description=f"Suspicious process detected: {info['name']}",
#                                 timestamp=time.time(),
#                                 process_name=info['name'],
#                                 process_id=pid,
#                                 details={"cmdline": cmdline[:200]}
#                             )
#                             threats.append(threat)
#                             logger.warning(f"Threat: {info['name']} (PID: {pid})")
#                             break
#
#                     # Behavioral analysis
#                     cpu = info.get('cpu_percent', 0) or 0
#                     mem = info.get('memory_percent', 0) or 0
#
#                     self._update_baseline(name, cpu, mem)
#
#                     if self._is_anomalous(name, cpu, mem):
#                         threat = ThreatAlert(
#                             level=ThreatLevel.MEDIUM,
#                             category=ThreatCategory.RESOURCE_ABUSE,
#                             description=f"Unusual behavior from {info['name']}: CPU {cpu}%, Mem {mem}%",
#                             timestamp=time.time(),
#                             process_name=info['name'],
#                             process_id=pid
#                         )
#                         threats.append(threat)
#
#                 except (psutil.AccessDenied, psutil.NoSuchProcess):
#                     continue
#
#         except Exception as e:
#             logger.error(f"Process scan error: {e}")
#
#         return threats
#
#     def _update_baseline(self, process_name: str, cpu: float, mem: float):
#         """Update behavioral baseline for process."""
#         if process_name not in self.process_baselines:
#             self.process_baselines[process_name] = {
#                 "cpu_samples": deque(maxlen=60),
#                 "mem_samples": deque(maxlen=60),
#                 "first_seen": time.time()
#             }
#
#         baseline = self.process_baselines[process_name]
#         baseline["cpu_samples"].append(cpu)
#         baseline["mem_samples"].append(mem)
#
#     def _is_anomalous(self, process_name: str, cpu: float, mem: float) -> bool:
#         """Check if process behavior is anomalous."""
#         if process_name not in self.process_baselines:
#             return False
#
#         baseline = self.process_baselines[process_name]
#
#         if len(baseline["cpu_samples"]) < 10:
#             return False
#
#         avg_cpu = sum(baseline["cpu_samples"]) / len(baseline["cpu_samples"])
#         avg_mem = sum(baseline["mem_samples"]) / len(baseline["mem_samples"])
#
#         # Significant deviation from baseline
#         if cpu > avg_cpu * 5 and cpu > 50:
#             return True
#         if mem > avg_mem * 3 and mem > 20:
#             return True
#
#         return False
#
#     def scan_network(self) -> List[ThreatAlert]:
#         """Network connection analysis."""
#         threats = []
#
#         try:
#             connections = psutil.net_connections()
#             current_time = time.time()
#
#             for conn in connections:
#                 if conn.status == 'ESTABLISHED' and conn.raddr:
#                     remote_ip = conn.raddr.ip
#                     remote_port = conn.raddr.port
#
#                     # Track connection
#                     self.connection_history.append({
#                         "ip": remote_ip,
#                         "port": remote_port,
#                         "time": current_time
#                     })
#
#                     # Check suspicious ports
#                     if remote_port in self.suspicious_ports:
#                         threats.append(ThreatAlert(
#                             level=ThreatLevel.HIGH,
#                             category=ThreatCategory.NETWORK_ANOMALY,
#                             description=f"Connection to suspicious port: {remote_ip}:{remote_port}",
#                             timestamp=current_time,
#                             details={"remote_ip": remote_ip, "remote_port": remote_port}
#                         ))
#
#                     # Check for data exfiltration (high outbound volume)
#                     # This is simplified - real implementation would track bytes
#
#         except (psutil.AccessDenied, Exception) as e:
#             logger.error(f"Network scan error: {e}")
#
#         return threats
#
#     def check_resource_abuse(self) -> Optional[ThreatAlert]:
#         """Detect crypto miners and resource abuse."""
#         try:
#             cpu = psutil.cpu_percent(interval=0.5)
#
#             if cpu > 95:
#                 top_procs = sorted(
#                     psutil.process_iter(['pid', 'name', 'cpu_percent']),
#                     key=lambda p: p.info.get('cpu_percent', 0) or 0,
#                     reverse=True
#                 )[:3]
#
#                 top_info = [f"{p.info['name']} ({p.info.get('cpu_percent', 0)}%)" 
#                            for p in top_procs]
#
#                 return ThreatAlert(
#                     level=ThreatLevel.MEDIUM,
#                     category=ThreatCategory.RESOURCE_ABUSE,
#                     description=f"Extreme CPU usage ({cpu}%): {', '.join(top_info)}",
#                     timestamp=time.time()
#                 )
#
#         except Exception as e:
#             logger.error(f"Resource check error: {e}")
#
#         return None
#
#     def analyze_input(self, user_input: str) -> Optional[ThreatAlert]:
#         """Analyze user input for injection/malicious patterns."""
#         # Check for command injection attempts
#         injection_patterns = [
#             r";\s*rm\s+-rf",
#             r"\|\s*rm\s",
#             r"sudo\s+rm",
#             r"format\s+c:",
#             r"del\s+/[fqs]",
#             r"\$\(.*\)",  # Command substitution
#             r"`.*`",      # Backtick execution
#         ]
#
#         for pattern in injection_patterns:
#             if re.search(pattern, user_input, re.IGNORECASE):
#                 return ThreatAlert(
#                     level=ThreatLevel.HIGH,
#                     category=ThreatCategory.SUSPICIOUS_PROCESS,
#                     description="Potential command injection detected in input",
#                     timestamp=time.time(),
#                     details={"pattern": pattern}
#                 )
#
#         return None
#
#     def start_monitoring(self, interval: float = 30.0):
#         """Start background monitoring."""
#         if self.is_monitoring:
#             return
#
#         self.is_monitoring = True
#         self._monitor_interval = interval
#
#         thread = threading.Thread(target=self._monitor_loop, daemon=True)
#         thread.start()
#         logger.info("Security monitoring started.")
#
#     def stop_monitoring(self):
#         """Stop monitoring."""
#         self.is_monitoring = False
#         logger.info("Security monitoring stopped.")
#
#     def _monitor_loop(self):
#         """Main monitoring loop."""
#         while self.is_monitoring:
#             all_threats = []
#
#             # Run scans
#             all_threats.extend(self.scan_processes())
#             all_threats.extend(self.scan_network())
#
#             resource_threat = self.check_resource_abuse()
#             if resource_threat:
#                 all_threats.append(resource_threat)
#
#             # Process threats
#             for threat in all_threats:
#                 self.threat_history.append(threat)
#
#                 if threat.level.value >= ThreatLevel.HIGH.value:
#                     self.enter_defensive_mode(threat.description)
#                     self._alert_user(threat)
#
#             # Update threat level
#             if all_threats:
#                 max_threat = max(all_threats, key=lambda t: t.level.value)
#                 self.current_threat_level = max_threat.level
#             else:
#                 # Gradually reduce threat level when no threats
#                 if self.current_threat_level != ThreatLevel.NONE:
#                     # Stay alert for a bit longer
#                     pass
#                 else:
#                     if self.defensive_mode:
#                         self.exit_defensive_mode()
#
#             time.sleep(self._monitor_interval)
#
#     def _alert_user(self, threat: ThreatAlert):
#         """Send alert to user."""
#         if self.alert_callback:
#             severity_emoji = {
#                 ThreatLevel.LOW: "ℹ️",
#                 ThreatLevel.MEDIUM: "⚠️",
#                 ThreatLevel.HIGH: "🚨",
#                 ThreatLevel.CRITICAL: "⛔"
#             }
#
#             emoji = severity_emoji.get(threat.level, "⚠️")
#
#             message = (
#                 f"{emoji} SECURITY ALERT\n"
#                 f"━━━━━━━━━━━━━━━━━━━━\n"
#                 f"Level: {threat.level.name}\n"
#                 f"Type: {threat.category.value}\n"
#                 f"Details: {threat.description}"
#             )
#
#             if threat.process_name:
#                 message += f"\nProcess: {threat.process_name}"
#
#             self.alert_callback(message)
#
#     def get_security_report(self) -> Dict:
#         """Generate comprehensive security report."""
#         recent_threats = [t for t in self.threat_history 
#                         if time.time() - t.timestamp < 3600]  # Last hour
#
#         threat_counts = {}
#         for threat in recent_threats:
#             cat = threat.category.value
#             threat_counts[cat] = threat_counts.get(cat, 0) + 1
#
#         return {
#             "current_threat_level": self.current_threat_level.name,
#             "defensive_mode": self.defensive_mode,
#             "is_monitoring": self.is_monitoring,
#             "threats_last_hour": len(recent_threats),
#             "threat_breakdown": threat_counts,
#             "total_threats_recorded": len(self.threat_history),
#             "processes_tracked": len(self.process_baselines)
#         }
#
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#
#     firewall = FirewallPersona(
#         alert_callback=lambda msg: print(f"\n{msg}\n")
#     )
#
#     print("Initial report:", firewall.get_security_report())
#
#     # Test input analysis
#     test_input = "Can you run `rm -rf /`?"
#     threat = firewall.analyze_input(test_input)
#     if threat:
#         print(f"Input threat detected: {threat.description}")
