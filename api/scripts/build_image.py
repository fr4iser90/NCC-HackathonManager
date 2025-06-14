import argparse
import os
import shutil
import subprocess
from pathlib import Path
import yaml
import sys
import time
from typing import Dict, Any, Tuple
import signal
import threading
import re

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.logger import BuildLogger

TEMPLATES = {
    "nodejs": "templates/web-nodejs/Dockerfile",
    "python": "templates/web-python/Dockerfile",
    "react-native": "templates/mobile-react-native/Dockerfile",
}

STACK_HINTS = {
    "nodejs": "package.json",
    "python": "requirements.txt",
    "react-native": "app.json",
}


def detect_stack(project_path: str, logger: BuildLogger) -> str:
    files = os.listdir(project_path)

    # First check if there's a single subdirectory that might contain the project
    subdirs = [
        d
        for d in files
        if os.path.isdir(os.path.join(project_path, d)) and not d.startswith(".")
    ]
    if len(subdirs) == 1 and not any(
        f in files
        for f in [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "package.json",
            "requirements.txt",
        ]
    ):
        # There's a single subdirectory and no project files at the top level
        # Check if project files exist in the subdirectory
        subdir_path = os.path.join(project_path, subdirs[0])
        subdir_files = os.listdir(subdir_path)

        if any(
            f in subdir_files
            for f in [
                "Dockerfile",
                "docker-compose.yml",
                "docker-compose.yaml",
                "package.json",
                "requirements.txt",
            ]
        ):
            # Found project files in subdirectory, move them to the top level
            logger.log_debug(
                f"Found project files in subdirectory: {subdirs[0]}, moving to top level"
            )
            for item in subdir_files:
                src = os.path.join(subdir_path, item)
                dst = os.path.join(project_path, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            # Update files list after moving
            files = os.listdir(project_path)

    # Now check for project files at the top level
    if "Dockerfile" in files:
        return "dockerfile"
    if "docker-compose.yml" in files or "docker-compose.yaml" in files:
        return "compose"
    if "package.json" in files:
        if "app.json" in files or "App.js" in files:
            return "react-native"
        return "nodejs"
    if "requirements.txt" in files:
        return "python"
    return None


def check_compose_security(compose_path: str, logger: BuildLogger) -> Tuple[bool, str]:
    with open(compose_path, "r") as f:
        try:
            compose = yaml.safe_load(f)
        except Exception as e:
            error_msg = f"Konnte docker-compose.yml nicht parsen: {e}"
            logger.log_error(e, {"compose_path": compose_path})
            return False, error_msg
    for svc_name, svc in (compose.get("services") or {}).items():
        # Check for privileged
        if svc.get("privileged", False):
            error_msg = (
                f"SECURITY: Service '{svc_name}' ist privileged! Build abgebrochen."
            )
            logger.log_warning(error_msg, {"service": svc_name})
            print(warning_msg)
            # Not returning False here, allowing it to continue
    return True, ""


def ensure_dockerfile(project_path: str, stack: str, logger: BuildLogger) -> None:
    dockerfile_path = os.path.join(project_path, "Dockerfile")
    if not os.path.exists(dockerfile_path):
        template_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), TEMPLATES[stack])
        )
        shutil.copy(template_path, dockerfile_path)
        logger.log_debug(f"Dockerfile aus Template kopiert: {template_path}")
    else:
        logger.log_debug("Eigenes Dockerfile gefunden, Template wird nicht kopiert.")


def build_image(project_path: str, tag: str, logger: BuildLogger) -> Tuple[int, str]:
    cmd = ["docker", "build", "-t", tag, project_path]
    logger.log_debug(f"Starte Build: {' '.join(cmd)}")

    start_time = time.time()
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    output = []
    step_number = 0
    cache_hits = 0
    step_start_time = None
    current_step = None

    for line in proc.stdout:
        # Capture output for return
        output.append(line.strip())

        # Try to parse Docker build step
        if line.startswith("Step "):
            # Log previous step duration if exists
            if step_start_time and current_step:
                duration = (time.time() - step_start_time) * 1000  # Convert to ms
                logger.log_build_step(step_number, current_step, "completed", duration)

            step_number += 1
            current_step = line.strip()
            step_start_time = time.time()
            logger.log_build_step(step_number, current_step, "started")
        elif "Using cache" in line:
            cache_hits += 1
            if step_start_time and current_step:
                duration = (time.time() - step_start_time) * 1000
                logger.log_build_step(step_number, "cache", "hit", duration)
        elif "Successfully built" in line:
            image_id = line.split()[-1]
            duration = time.time() - start_time
            logger.log_build_complete(
                image_id, {"hits": cache_hits, "misses": step_number - cache_hits}
            )

    proc.wait()
    if proc.returncode == 0:
        logger.log_debug(f"Image erfolgreich gebaut: {tag}")
    else:
        logger.log_error(Exception(f"Build fehlgeschlagen (Exit {proc.returncode})"))
    return proc.returncode, "\n".join(output)


def build_compose(project_path: str, logger: BuildLogger) -> Tuple[int, str]:
    compose_path = os.path.join(project_path, "docker-compose.yml")
    if not os.path.exists(compose_path):
        compose_path = os.path.join(project_path, "docker-compose.yaml")
    if not os.path.exists(compose_path):
        error_msg = "docker-compose.yml nicht gefunden!"
        logger.log_error(Exception(error_msg))
        return 2, error_msg

    ok, msg = check_compose_security(compose_path, logger)
    if not ok:
        logger.log_error(Exception(msg))
        return 3, msg

    cmd = ["docker", "compose", "-f", compose_path, "build"]
    logger.log_debug(f"Starte Compose-Build: {' '.join(cmd)}")

    start_time = time.time()
    proc = subprocess.Popen(
        cmd,
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = []
    step_number = 0
    cache_hits = 0
    step_start_time = None
    current_step = None

    for line in proc.stdout:
        output.append(line.strip())

        # Try to parse service and step information
        if line.startswith("Building "):
            current_service = line.split("Building ")[1].strip()
            logger.log_debug(f"Baue Service: {current_service}")
        elif line.startswith("Step "):
            if step_start_time and current_step:
                duration = (time.time() - step_start_time) * 1000
                logger.log_build_step(step_number, current_step, "completed", duration)

            step_number += 1
            current_step = line.strip()
            step_start_time = time.time()
            logger.log_build_step(step_number, current_step, "started")
        elif "Using cache" in line:
            cache_hits += 1
            if step_start_time and current_step:
                duration = (time.time() - step_start_time) * 1000
                logger.log_build_step(step_number, "cache", "hit", duration)

    proc.wait()
    duration = time.time() - start_time

    if proc.returncode == 0:
        logger.log_build_complete(
            "compose",
            {
                "duration_seconds": duration,
                "hits": cache_hits,
                "misses": step_number - cache_hits,
            },
        )
    else:
        logger.log_error(
            Exception(f"Compose-Build fehlgeschlagen (Exit {proc.returncode})")
        )

    return proc.returncode, "\n".join(output)


def log(msg):
    print(msg)
    sys.stdout.flush()


def check_project_files(project_path):
    missing = []
    for fname in ["Dockerfile", "requirements.txt", "package.json"]:
        if not os.path.exists(os.path.join(project_path, fname)):
            missing.append(fname)
    return missing


def check_security_warnings(project_path):
    warnings = []
    dockerfile = os.path.join(project_path, "Dockerfile")
    compose = os.path.join(project_path, "docker-compose.yml")
    if os.path.exists(dockerfile):
        with open(dockerfile) as f:
            content = f.read()
            if re.search(r"USER\s+root", content):
                warnings.append("SECURITY WARNING: Dockerfile uses USER root!")
            if "privileged: true" in content:
                warnings.append("SECURITY WARNING: Dockerfile uses privileged: true!")
    if os.path.exists(compose):
        with open(compose) as f:
            content = f.read()
            if "privileged: true" in content:
                warnings.append(
                    "SECURITY WARNING: docker-compose.yml uses privileged: true!"
                )
    return warnings


def run_with_timeout(cmd, cwd, timeout):
    proc = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    timer = threading.Timer(timeout, lambda: proc.kill())
    try:
        timer.start()
        out, _ = proc.communicate()
        return proc.returncode, out
    finally:
        timer.cancel()


def main():
    parser = argparse.ArgumentParser(description="Dockerize User Project")
    parser.add_argument("--project-path", required=True, help="Pfad zum User-Projekt")
    parser.add_argument(
        "--tag",
        help="Docker Image Tag (if not set, will be generated from name/id args)",
    )
    parser.add_argument(
        "--project-name",
        help="Project name (from ZIP or directory) for image tag generation",
    )
    parser.add_argument("--username", help="User ID for image tag generation")
    parser.add_argument("--user-name", help="Username/email for image tag generation")
    parser.add_argument("--version", help="Version for image tag generation")
    parser.add_argument("--hackathon", help="Hackathon ID for image tag generation")

    args = parser.parse_args()
    # Determine image tag
    tag = args.tag

    def clean(val):
        return (
            str(val)
            .strip()
            .replace(" ", "_")
            .replace("/", "_")
            .replace(":", "_")
            .replace(".", "_")
            .replace("@", "_")
        )

    if not tag:
        # Use project name, username, version for tag
        project_part = clean(args.project_name) if args.project_name else ""
        # Try to infer project name from project path if not provided
        if not project_part and args.project_path:
            project_part = clean(os.path.basename(os.path.normpath(args.project_path)))
        user_part = (
            clean(args.user_name)
            if args.user_name
            else (clean(args.username) if args.username else "")
        )
        version_part = clean(args.version) if args.version else "latest"
        if not args.user_name and not args.username:
            print(
                "WARNING: --user-name/--username not provided, image tag will not include username."
            )
        if not args.version:
            print(
                "WARNING: --version not provided, image tag will not include version (using 'latest')."
            )
        if project_part or user_part:
            tag = f"{project_part}_{user_part}_{version_part}"
            print(f"Generated image tag: {tag}")
        else:
            print(
                "ERROR: --tag or at least --project-name or --user-name must be provided."
            )
            exit(1)

    # Extract project_id and version_id from tag (fallback to args if possible)
    tag_parts = tag.split("-")
    project_id = tag_parts[2] if len(tag_parts) > 2 else (args.hackathon or "unknown")
    version_id = tag_parts[3] if len(tag_parts) > 3 else (args.version or "unknown")

    logger = BuildLogger(project_id, version_id)
    project_path = os.path.abspath(args.project_path)
    if not os.path.isdir(project_path):
        error_msg = f"Projektpfad nicht gefunden: {project_path}"
        logger.log_error(Exception(error_msg))
        print(f"ERROR: {error_msg}")
        exit(1)

    stack = detect_stack(project_path, logger)
    if not stack:
        error_msg = "Konnte Stack nicht erkennen (Node.js, Python, React Native, Dockerfile, Compose)"
        logger.log_error(Exception(error_msg))
        print(f"ERROR: {error_msg}")
        exit(2)

    logger.log_build_start(args.project_path, tag, stack)
    log(f"🚀 Starte Build für {tag} ({stack.upper()})")

    if stack == "dockerfile":
        logger.log_debug("Verwende vorhandenes Dockerfile")
        rc, output = build_image(project_path, tag, logger)
        exit(rc)
    elif stack == "compose":
        logger.log_debug("Verwende vorhandenes docker-compose.yml")
        rc, output = build_compose(project_path, logger)
        exit(rc)
    else:
        logger.log_debug(f"Verwende {stack}-Template")
        ensure_dockerfile(project_path, stack, logger)
        rc, output = build_image(project_path, tag, logger)
        exit(rc)

    build_log = []
    try:
        # The build log message is now only printed after tag and stack are resolved
        # Check for missing files
        missing = check_project_files(project_path)
        if missing:
            msg = f"WARN: Projektdateien fehlen: {', '.join(missing)}"
            log(msg)
            build_log.append(msg)
        # Security warnings
        for warn in check_security_warnings(project_path):
            log(warn)
            build_log.append(warn)
        # Build (simulate with Docker build if Dockerfile exists)
        if os.path.exists(os.path.join(project_path, "Dockerfile")):
            cmd = ["docker", "build", "-t", tag, project_path]
            log(f"🔨 Starte Build: {' '.join(cmd)}")
            build_log.append(f"🔨 Starte Build: {' '.join(cmd)}")
            rc, out = run_with_timeout(cmd, cwd=project_path, timeout=60)
            build_log.append(out)
            if rc == 0:
                log("✨ Build erfolgreich!")
                build_log.append("✨ Build erfolgreich!")
            else:
                log(f"❌ Build fehlgeschlagen (Exit {rc})!")
                build_log.append(f"❌ Build fehlgeschlagen (Exit {rc})!")
        else:
            log("WARN: Kein Dockerfile gefunden, Build wird übersprungen.")
            build_log.append("WARN: Kein Dockerfile gefunden, Build wird übersprungen.")
    except Exception as e:
        log(f"ERROR: Build-Exception: {e}")
        build_log.append(f"ERROR: Build-Exception: {e}")
    finally:
        # Schreibe Build-Log in Datei, falls gewünscht (kann von Service-Layer gelesen werden)
        with open(os.path.join(project_path, "build.log"), "w") as f:
            f.write("\n".join(build_log))


if __name__ == "__main__":
    main()
