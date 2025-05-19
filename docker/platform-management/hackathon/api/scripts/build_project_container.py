import argparse
import os
import shutil
import subprocess
from pathlib import Path

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
    if "package.json" in files:
        # Unterscheide React Native von Node.js
        if "app.json" in files or "App.js" in files:
            return "react-native"
        return "nodejs"
    if "requirements.txt" in files:
        return "python"
    return None

def ensure_dockerfile(project_path, stack):
    dockerfile_path = os.path.join(project_path, "Dockerfile")
    if not os.path.exists(dockerfile_path):
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), TEMPLATES[stack]))
        shutil.copy(template_path, dockerfile_path)
        print(f"[INFO] Dockerfile aus Template kopiert: {template_path}")
    else:
        print("[INFO] Eigenes Dockerfile gefunden, Template wird nicht kopiert.")

def build_image(project_path, tag):
    cmd = ["docker", "build", "-t", tag, project_path]
    print(f"[INFO] Starte Build: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    if proc.returncode == 0:
        print(f"[SUCCESS] Image gebaut: {tag}")
    else:
        print(f"[ERROR] Build fehlgeschlagen (Exit {proc.returncode})")
    return proc.returncode

def main():
    parser = argparse.ArgumentParser(description="Dockerize User Project")
    parser.add_argument("--project-path", required=True, help="Pfad zum User-Projekt")
    parser.add_argument("--tag", required=True, help="Docker Image Tag")
    args = parser.parse_args()

    project_path = os.path.abspath(args.project_path)
    if not os.path.isdir(project_path):
        print(f"[ERROR] Projektpfad nicht gefunden: {project_path}")
        exit(1)

    stack = detect_stack(project_path)
    if not stack:
        print("[ERROR] Konnte Stack nicht erkennen (Node.js, Python, React Native)")
        exit(2)
    print(f"[INFO] Erkannter Stack: {stack}")

    ensure_dockerfile(project_path, stack)
    rc = build_image(project_path, args.tag)
    exit(rc)

if __name__ == "__main__":
    main() 