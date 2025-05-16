#!/bin/bash
# Prevent multiple sourcing
if [ -n "${_PATH_LOADED+x}" ]; then
    return 0
fi
_PATH_LOADED=1

# Base installation paths
BASE_DIR="${HOME}"
DOCKER_BASE_DIR="${BASE_DIR}/docker"         # For Containers

# Resolve script path and set DOCKER_SCRIPTS_DIR
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
if [ -z "${SCRIPT_PATH}" ]; then
    echo "Error: Failed to resolve script path" >&2
    return 1
fi

DOCKER_SCRIPTS_DIR="$(dirname "$(dirname "$(dirname "${SCRIPT_PATH}")")")"
if [ -z "${DOCKER_SCRIPTS_DIR}" ]; then
    echo "Error: Failed to resolve Docker scripts directory" >&2
    return 1
fi

# Derived paths
DOCKER_LIB_DIR="${DOCKER_SCRIPTS_DIR}/lib"   # For Libraries
DOCKER_MODULES_DIR="${DOCKER_SCRIPTS_DIR}/modules"   # For Modules

# Export paths for other scripts
export DOCKER_SCRIPTS_DIR
export DOCKER_BASE_DIR
export DOCKER_LIB_DIR
export DOCKER_MODULES_DIR


# Path helper functions
get_docker_dir() {
    local container=$1
    local category
    
    if [ -z "${MANAGEMENT_CATEGORIES[*]}" ]; then
        print_status "MANAGEMENT_CATEGORIES not defined" "error"
        return 1
    fi
    
    category=$(get_container_category "$container")
    if [ $? -eq 0 ]; then
        echo "$DOCKER_BASE_DIR/$category/$container"
        return 0
    fi
    
    print_status "Container $container not found" "error"
    return 1
}
