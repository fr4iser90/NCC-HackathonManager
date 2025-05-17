#!/bin/bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"


source "${DOCKER_SCRIPTS_DIR}/lib/core/imports.sh"

# Guard gegen mehrfaches Laden
if [ -n "${_SERVICES_INIT_LOADED+x}" ]; then
    return 0
fi
_SERVICES_INIT_LOADED=1

# Service Initialization
initialize_services() {
    print_header "Portainer Setup"

    print_status "Initializing Portainer..." "info"
    export SERVICE_NAME="portainer"
    start_docker_container "portainer" || {
        print_status "Failed to start Portainer" "error"
        return 1
    }
    print_status "Portainer initialized successfully" "success"

    # Finalize credentials if Auto-Setup was active
    if [ "$AUTO_SETUP" -eq 1 ]; then
        finalize_credentials_file
    fi

    print_status "All required services have been initialized" "success"
    return 0
}

# Run if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    initialize_services
fi