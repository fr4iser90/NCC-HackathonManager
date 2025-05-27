import argparse
import sys
from utils import get_logger, DockerHelper, ScriptError


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Docker image to registry and/or environment."
    )
    parser.add_argument("--tag", required=True, help="Docker image tag to deploy")
    parser.add_argument(
        "--target-tag", required=True, help="Target image tag (e.g., registry/repo:tag)"
    )
    parser.add_argument(
        "--project-id", default="unknown", help="Project ID for logging"
    )
    parser.add_argument(
        "--version-id", default="unknown", help="Version ID for logging"
    )
    parser.add_argument(
        "--label",
        action="append",
        help="Label to add to the container (key=value). Can be specified multiple times.",
    )
    parser.add_argument("--network", help="Docker network to connect the container to")
    parser.add_argument("--container-name", help="Name for the running container")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the container after push with labels/network",
    )
    parser.add_argument(
        "--domain", help="Base domain for Traefik label generation (optional)"
    )
    parser.add_argument(
        "--hackathon-id", help="Hackathon ID for Traefik label generation (optional)"
    )
    parser.add_argument(
        "--username", help="Username for Traefik label generation (optional)"
    )
    args = parser.parse_args()

    logger = get_logger(args.project_id, args.version_id)
    logger.log_build_start("deploy_image", args.tag, "deploy")

    # Tag image
    rc, output = DockerHelper.tag_image(args.tag, args.target_tag, logger=logger)
    print(output)
    if rc != 0:
        logger.log_error(
            ScriptError(f"Image tag failed: {args.tag} -> {args.target_tag}")
        )
        sys.exit(rc)

    # Push image
    rc, output = DockerHelper.push_image(args.target_tag, logger=logger)
    print(output)
    if rc != 0:
        logger.log_error(ScriptError(f"Image push failed: {args.target_tag}"))
        sys.exit(rc)

    # Optionally run the container with labels and network
    if args.run:
        run_cmd = ["docker", "run", "-d", "--restart=unless-stopped"]
        if args.container_name:
            run_cmd += ["--name", args.container_name]
        if args.network:
            run_cmd += ["--network", args.network]
        # Handle labels
        labels = args.label or []
        # Traefik label generation
        if args.domain and args.hackathon_id and args.username:
            traefik_host = f"{args.hackathon_id}.{args.username}.{args.domain}"
            labels += [
                f"traefik.enable=true",
                f"traefik.http.routers.{args.hackathon_id}_{args.username}.rule=Host(`{traefik_host}`)",
                f"traefik.http.routers.{args.hackathon_id}_{args.username}.entrypoints=websecure",
                f"traefik.http.routers.{args.hackathon_id}_{args.username}.tls.certresolver=letsencrypt",
            ]
        for label in labels:
            run_cmd += ["--label", label]
        run_cmd.append(args.target_tag)
        logger.log_debug(f"Running container: {' '.join(run_cmd)}")
        rc, output = DockerHelper.run_command(run_cmd)
        print(output)
        if rc != 0:
            logger.log_error(ScriptError(f"Container run failed: {args.target_tag}"))
            sys.exit(rc)
        logger.log_debug(f"Container started successfully: {args.target_tag}")

    logger.log_debug(f"Image deployed successfully: {args.target_tag}")
    logger.log_build_complete(args.target_tag, {"deploy": "success"})
    sys.exit(0)


if __name__ == "__main__":
    main()
