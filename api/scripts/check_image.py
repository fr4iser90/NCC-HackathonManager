import argparse
import sys
from utils import get_logger, DockerHelper, ScriptError


def main():
    parser = argparse.ArgumentParser(
        description="Check Docker image for security and best practices."
    )
    parser.add_argument("--tag", required=True, help="Docker image tag to check")
    parser.add_argument(
        "--project-id", default="unknown", help="Project ID for logging"
    )
    parser.add_argument(
        "--version-id", default="unknown", help="Version ID for logging"
    )
    args = parser.parse_args()

    logger = get_logger(args.project_id, args.version_id)
    logger.log_build_start("check_image", args.tag, "check")

    rc, output = DockerHelper.scan_image(args.tag, logger=logger)
    print(output)
    if rc != 0:
        logger.log_error(ScriptError(f"Image scan failed for {args.tag}"))
        sys.exit(rc)
    else:
        logger.log_debug(f"Image scan successful for {args.tag}")
        logger.log_build_complete(args.tag, {"scan": "success"})
        sys.exit(0)


if __name__ == "__main__":
    main()
