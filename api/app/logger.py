import structlog
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Mapping for short log level tags
def short_level_tag(level):
    return {
        "info": "[i]",
        "debug": "[d]",
        "warning": "[w]",
        "error": "[e]",
        "critical": "[c]"
    }.get(level.lower(), f"[{level[:1].lower()}]")

# Custom processor to inject short level tag

def add_short_level_tag(logger, method_name, event_dict):
    event_dict["short_level"] = short_level_tag(method_name)
    return event_dict

# Custom renderer for pretty output

def custom_console_renderer(logger, method_name, event_dict):
    ts = event_dict.get("timestamp", "")
    lvl = event_dict.get("short_level", "")
    msg = event_dict.get("event", "")
    return f"{ts} {lvl} {msg}"

def configure_logger():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            add_short_level_tag,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            custom_console_renderer
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=True,
    )

# Call configure_logger on import so it's always set up
configure_logger()

def get_logger(name: str):
    return structlog.get_logger(name)

class BuildLogger:
    def __init__(self, project_id: str, version_id: str):
        self.logger = get_logger("build")
        self.project_id = project_id
        self.version_id = version_id
        self.start_time = time.time()
        self.step_times: Dict[int, float] = {}
        self.total_steps = 0
        self.current_step = 0
    
    def _format_step(self, step: int, total: int) -> str:
        return f"[{step}/{total}]" if total > 0 else f"[{step}]"
    
    def _format_duration(self, duration_ms: float) -> str:
        if duration_ms < 1000:
            return f"{duration_ms:.0f}ms"
        return f"{duration_ms/1000:.1f}s"
    
    def _print(self, message: str, color: str = Fore.WHITE):
        print(f"{color}{message}{Style.RESET_ALL}")
    
    def log_build_start(self, project_path: str, tag: str, stack: str):
        self._print(f"\n🚀 Starte Build für {stack.upper()}", Fore.CYAN)
    
    def log_build_step(self, step: int, name: str, status: str, duration_ms: Optional[float] = None, progress: Optional[str] = None):
        if status == "started":
            self.step_times[step] = time.time()
            self.current_step = step
            # Extract step number from name if possible
            if "Step " in name and "/" in name:
                try:
                    current, total = name.split("Step ")[1].split(" : ")[0].split("/")
                    self.total_steps = int(total)
                except (ValueError, IndexError):
                    pass
            
            step_info = self._format_step(step, self.total_steps)
            self._print(f"{step_info} {name}", Fore.YELLOW)
            
        elif status == "completed":
            start_time = self.step_times.get(step)
            if start_time and duration_ms:
                duration = self._format_duration(duration_ms)
                self._print(f"   ✓ Fertig in {duration}", Fore.GREEN)
    
    def log_build_complete(self, image_id: str, metrics: Dict[str, Any]):
        duration = time.time() - self.start_time
        hits = metrics.get("hits", 0)
        misses = metrics.get("misses", 0)
        
        self._print("\n✨ Build erfolgreich!", Fore.GREEN)
        self._print(f"   • Dauer: {self._format_duration(duration * 1000)}", Fore.WHITE)
        self._print(f"   • Cache: {hits} Hits, {misses} Misses", Fore.WHITE)
        self._print(f"   • Image: {image_id[:12]}", Fore.WHITE)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        self._print(f"\n❌ Fehler: {str(error)}", Fore.RED)
        if context:
            for key, value in context.items():
                self._print(f"   • {key}: {value}", Fore.RED)
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        self._print(f"\n⚠️  Warnung: {message}", Fore.YELLOW)
        if context:
            for key, value in context.items():
                self._print(f"   • {key}: {value}", Fore.YELLOW)
    
    def log_debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        if "Found project files in subdirectory" in message:
            self._print(f"\n📦 {message}", Fore.BLUE)
        elif "Verwende" in message:
            self._print(f"\n🔧 {message}", Fore.BLUE)
        elif "Starte Build" in message:
            self._print(f"\n🔨 {message}", Fore.BLUE)
        elif "Image erfolgreich gebaut" in message:
            self._print(f"\n✅ {message}", Fore.GREEN)
        else:
            self._print(f"\nℹ️  {message}", Fore.BLUE)
