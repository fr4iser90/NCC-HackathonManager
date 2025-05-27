import subprocess
import sys
from typing import Optional, Tuple, List
from app.logger import BuildLogger


class ScriptError(Exception):
    """Custom exception for script errors."""

    pass


def get_logger(project_id: str = "unknown", version_id: str = "unknown") -> BuildLogger:
    """Return a BuildLogger instance for consistent logging."""
    return BuildLogger(project_id, version_id)


class DockerHelper:
    """Helper class for common Docker operations."""

    @staticmethod
    def run_command(
        cmd: List[str], cwd: Optional[str] = None, timeout: int = 120
    ) -> Tuple[int, str]:
        """Run a shell command and return (exit_code, output)."""
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            out, _ = proc.communicate(timeout=timeout)
            return proc.returncode, out
        except subprocess.TimeoutExpired:
            proc.kill()
            return 1, "Command timed out: " + " ".join(cmd)
        except Exception as e:
            return 2, f"Command failed: {e}"

    @staticmethod
    def build_image(
        path: str, tag: str, logger: Optional[BuildLogger] = None
    ) -> Tuple[int, str]:
        cmd = ["docker", "build", "-t", tag, path]
        if logger:
            logger.log_debug(f"Running: {' '.join(cmd)}")
        return DockerHelper.run_command(cmd, cwd=path)

    @staticmethod
    def tag_image(
        source: str, target: str, logger: Optional[BuildLogger] = None
    ) -> Tuple[int, str]:
        cmd = ["docker", "tag", source, target]
        if logger:
            logger.log_debug(f"Running: {' '.join(cmd)}")
        return DockerHelper.run_command(cmd)

    @staticmethod
    def push_image(tag: str, logger: Optional[BuildLogger] = None) -> Tuple[int, str]:
        cmd = ["docker", "push", tag]
        if logger:
            logger.log_debug(f"Running: {' '.join(cmd)}")
        return DockerHelper.run_command(cmd)

    @staticmethod
    def pull_image(tag: str, logger: Optional[BuildLogger] = None) -> Tuple[int, str]:
        cmd = ["docker", "pull", tag]
        if logger:
            logger.log_debug(f"Running: {' '.join(cmd)}")
        return DockerHelper.run_command(cmd)

    @staticmethod
    def scan_image(tag: str, logger: Optional[BuildLogger] = None) -> Tuple[int, str]:
        # Example: use trivy if available, fallback to docker scan
        try:
            cmd = ["trivy", "image", "--no-progress", tag]
            if logger:
                logger.log_debug(f"Running: {' '.join(cmd)}")
            return DockerHelper.run_command(cmd)
        except FileNotFoundError:
            cmd = ["docker", "scan", tag]
            if logger:
                logger.log_debug(f"Running: {' '.join(cmd)}")
            return DockerHelper.run_command(cmd)
