import argparse
import sys
from utils import get_logger, DockerHelper, ScriptError

def main():
    parser = argparse.ArgumentParser(description="Manage Docker image storage and registry operations.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser("push", help="Push image to registry")
    push_parser.add_argument("--tag", required=True, help="Image tag to push")
    push_parser.add_argument("--project-id", default="unknown", help="Project ID for logging")
    push_parser.add_argument("--version-id", default="unknown", help="Version ID for logging")

    pull_parser = subparsers.add_parser("pull", help="Pull image from registry")
    pull_parser.add_argument("--tag", required=True, help="Image tag to pull")
    pull_parser.add_argument("--project-id", default="unknown", help="Project ID for logging")
    pull_parser.add_argument("--version-id", default="unknown", help="Version ID for logging")

    # Placeholders for future features
    subparsers.add_parser("list", help="List images in registry (not implemented)")
    subparsers.add_parser("cleanup", help="Cleanup old/unused images (not implemented)")

    args = parser.parse_args()

    logger = get_logger(getattr(args, "project_id", "unknown"), getattr(args, "version_id", "unknown"))

    if args.command == "push":
        logger.log_build_start("image_storage", args.tag, "push")
        rc, output = DockerHelper.push_image(args.tag, logger=logger)
        print(output)
        if rc != 0:
            logger.log_error(ScriptError(f"Image push failed: {args.tag}"))
            sys.exit(rc)
        logger.log_debug(f"Image pushed successfully: {args.tag}")
        logger.log_build_complete(args.tag, {"push": "success"})
        sys.exit(0)

    elif args.command == "pull":
        logger.log_build_start("image_storage", args.tag, "pull")
        rc, output = DockerHelper.pull_image(args.tag, logger=logger)
        print(output)
        if rc != 0:
            logger.log_error(ScriptError(f"Image pull failed: {args.tag}"))
            sys.exit(rc)
        logger.log_debug(f"Image pulled successfully: {args.tag}")
        logger.log_build_complete(args.tag, {"pull": "success"})
        sys.exit(0)

    elif args.command == "list":
        print("Listing images is not yet implemented.")
        sys.exit(1)

    elif args.command == "cleanup":
        print("Cleanup is not yet implemented.")
        sys.exit(1)

if __name__ == "__main__":
    main()
