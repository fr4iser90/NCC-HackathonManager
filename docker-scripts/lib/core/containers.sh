#!/bin/bash

# Guard gegen mehrfaches Laden
if [ -n "${_CONTAINERS_LOADED+x}" ]; then
    return 0
fi
_CONTAINERS_LOADED=1

# Container Kategorien
declare -gA MANAGEMENT_CATEGORIES=(
    ["gateway-management"]="traefik-crowdsec ddns-updater"
    ["system-management"]="portainer"
)

# Get container category
get_container_category() {
    local container="$1"
    
    for category in "${!MANAGEMENT_CATEGORIES[@]}"; do
        if [[ "${MANAGEMENT_CATEGORIES[$category]}" =~ $container ]]; then
            echo "$category"
            return 0
        fi
    done
    
    return 1
}
