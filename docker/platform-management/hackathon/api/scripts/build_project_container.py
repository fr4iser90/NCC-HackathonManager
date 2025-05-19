import argparse
import os
import shutil
import subprocess
from pathlib import Path
import yaml
import sys

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.logger import get_logger

# Initialize logger
logger = get_logger("build_project_container")

TEMPLATES = {
    "nodejs": "../../templates/web-nodejs/Dockerfile",
    "python": "../../templates/web-python/Dockerfile",
    "react-native": "../../templates/mobile-react-native/Dockerfile",
}

STACK_HINTS = {
    "nodejs": "package.json",
    "python": "requirements.txt",
    "react-native": "app.json",
}

def detect_stack(project_path):
    files = os.listdir(project_path)
    
    # First check if there's a single subdirectory that might contain the project
    subdirs = [d for d in files if os.path.isdir(os.path.join(project_path, d)) and not d.startswith('.')]
    if len(subdirs) == 1 and not any(f in files for f in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "package.json", "requirements.txt"]):
        # There's a single subdirectory and no project files at the top level
        # Check if project files exist in the subdirectory
        subdir_path = os.path.join(project_path, subdirs[0])
        subdir_files = os.listdir(subdir_path)
        
        if any(f in subdir_files for f in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "package.json", "requirements.txt"]):
            # Found project files in subdirectory, move them to the top level
            logger.info(f"Found project files in subdirectory: {subdirs[0]}, moving to top level")
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

def check_compose_security(compose_path):
    with open(compose_path, 'r') as f:
        try:
            compose = yaml.safe_load(f)
        except Exception as e:
            error_msg = f"Konnte docker-compose.yml nicht parsen: {e}"
            logger.error(error_msg)
            return False, error_msg
    for svc_name, svc in (compose.get('services') or {}).items():
        # Check for privileged
        if svc.get('privileged', False):
            error_msg = f"SECURITY: Service '{svc_name}' ist privileged! Build abgebrochen."
            logger.error(error_msg)
            return False, error_msg
        
        # Check for docker.sock - but allow it if it's in a controlled environment
        # This is necessary for Docker-outside-of-Docker (DooD) functionality
        mounts = svc.get('volumes', [])
        for mount in mounts:
            if isinstance(mount, str) and '/var/run/docker.sock' in mount:
                # We're allowing docker.sock mounts for now, but logging it as a warning
                warning_msg = f"WARNING: Service '{svc_name}' mountet docker.sock. Dies ist potenziell unsicher, aber für DooD notwendig."
                logger.warning(warning_msg)
                print(warning_msg)
                # Not returning False here, allowing it to continue
    return True, ""

def ensure_dockerfile(project_path, stack):
    dockerfile_path = os.path.join(project_path, "Dockerfile")
    if not os.path.exists(dockerfile_path):
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), TEMPLATES[stack]))
        shutil.copy(template_path, dockerfile_path)
        logger.info(f"Dockerfile aus Template kopiert: {template_path}")
    else:
        logger.info("Eigenes Dockerfile gefunden, Template wird nicht kopiert.")

def build_image(project_path, tag):
    cmd = ["docker", "build", "-t", tag, project_path]
    logger.info(f"Starte Build: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        # Still print Docker build output to console but also log it
        print(line, end="")
        logger.debug(line.strip())
    proc.wait()
    if proc.returncode == 0:
        logger.info(f"Image erfolgreich gebaut: {tag}")
    else:
        logger.error(f"Build fehlgeschlagen (Exit {proc.returncode})")
    return proc.returncode

def build_compose(project_path):
    compose_path = os.path.join(project_path, "docker-compose.yml")
    if not os.path.exists(compose_path):
        compose_path = os.path.join(project_path, "docker-compose.yaml")
    if not os.path.exists(compose_path):
        logger.error("docker-compose.yml nicht gefunden!")
        return 2
    ok, msg = check_compose_security(compose_path)
    if not ok:
        logger.error(msg)
        return 3
    cmd = ["docker", "compose", "-f", compose_path, "build"]
    logger.info(f"Starte Compose-Build: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        # Still print Docker build output to console but also log it
        print(line, end="")
        logger.debug(line.strip())
    proc.wait()
    if proc.returncode == 0:
        logger.info("Compose-Build erfolgreich!")
    else:
        logger.error(f"Compose-Build fehlgeschlagen (Exit {proc.returncode})")
    return proc.returncode

def main():
    parser = argparse.ArgumentParser(description="Dockerize User Project")
    parser.add_argument("--project-path", required=True, help="Pfad zum User-Projekt")
    parser.add_argument("--tag", required=True, help="Docker Image Tag")
    args = parser.parse_args()

    logger.info(f"Starte Containerisierung für Projekt: {args.project_path} mit Tag: {args.tag}")
    
    project_path = os.path.abspath(args.project_path)
    if not os.path.isdir(project_path):
        logger.error(f"Projektpfad nicht gefunden: {project_path}")
        exit(1)

    stack = detect_stack(project_path)
    if not stack:
        logger.error("Konnte Stack nicht erkennen (Node.js, Python, React Native, Dockerfile, Compose)")
        exit(2)
    logger.info(f"Erkannter Stack: {stack}")

    if stack == "dockerfile":
        logger.info("Verwende vorhandenes Dockerfile")
        rc = build_image(project_path, args.tag)
        exit(rc)
    elif stack == "compose":
        logger.info("Verwende vorhandenes docker-compose.yml")
        rc = build_compose(project_path)
        exit(rc)
    else:
        logger.info(f"Verwende {stack}-Template")
        ensure_dockerfile(project_path, stack)
        rc = build_image(project_path, args.tag)
        exit(rc)

if __name__ == "__main__":
    main()
