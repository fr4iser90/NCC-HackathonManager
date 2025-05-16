#!/bin/bash

# Import version
IMPORTS_VERSION="1.1.0"

# Guard against multiple loading
if [ -n "${_IMPORTS_LOADED+x}" ]; then
    return 0
fi
_IMPORTS_LOADED=1

# Load script header first (contains DOCKER_SCRIPTS_DIR)
if ! source "${DOCKER_SCRIPTS_DIR}/lib/core/script-header.sh"; then
    echo "ERROR: Failed to load script-header.sh" >&2
    exit 1
fi

# Import logging functions
source "${DOCKER_SCRIPTS_DIR}/lib/utils/format/output.sh"

# Core modules
CORE_MODULES=(
    "containers.sh"
    "path.sh"
)

for module in "${CORE_MODULES[@]}"; do
    if ! source "${DOCKER_SCRIPTS_DIR}/lib/core/${module}"; then
        print_status "Failed to load core module: ${module}" "error"
        exit 1
    fi
done

# Utility modules
UTILS=(
    "format/colors.sh"
    "input/prompt.sh"
    "input/validation.sh"
    "system/file.sh"
    "system/user.sh"
    "system/string.sh"
)

for util in "${UTILS[@]}"; do
    if ! source "${DOCKER_SCRIPTS_DIR}/lib/utils/${util}"; then
        print_status "Failed to load utility: ${util}" "error"
        exit 1
    fi
done

# Security modules
SECURITY_MODULES=(
    "credentials.sh"
    "crypto.sh"
    "hash.sh"
    "credentials-manager.sh"
)

for module in "${SECURITY_MODULES[@]}"; do
    if ! source "${DOCKER_SCRIPTS_DIR}/modules/security/${module}"; then
        print_status "Failed to load security module: ${module}" "error"
        exit 1
    fi
done

# Service modules
SERVICE_MODULES=(
    "docker.sh"
    "init-gateway.sh"
    "init-services.sh"
    "permissions.sh"
)

for module in "${SERVICE_MODULES[@]}"; do
    if ! source "${DOCKER_SCRIPTS_DIR}/modules/services/${module}"; then
        print_status "Failed to load service module: ${module}" "error"
        exit 1
    fi
done

# Network modules
NETWORK_MODULES=(
    "dns/dns-setup.sh"
    "dns/dns-providers-list.sh"
    "dns/dns-provider-select.sh"
    "dns/dns-companion-manager.sh"
    "router.sh"
    "ports.sh"
)

for module in "${NETWORK_MODULES[@]}"; do
    if ! source "${DOCKER_SCRIPTS_DIR}/modules/network/${module}"; then
        print_status "Failed to load network module: ${module}" "error"
        exit 1
    fi
done


# print_status "All imports loaded successfully" "success"
# verify_imports() {
#     local required_vars=(
#         "DOCKER_BASE_DIR"     # from path.sh
#         "SHOW_CREDENTIALS"    # from credentials.sh
#         "INFO"               # from colors.sh
#     )

#     for var in "${required_vars[@]}"; do
#         if [ -z "${!var}" ]; then
#             if type print_status >/dev/null 2>&1; then
#                 print_status "Required variable $var is not set" "error"
#             else
#                 echo "Error: Required variable $var is not set"
#             fi
#             exit 1
#         fi
#     done

#     if type print_status >/dev/null 2>&1; then
#         print_status "All required imports verified" "success"
#     fi
# }

# verify_imports
