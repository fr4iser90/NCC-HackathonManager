#!/bin/bash

# Guard gegen mehrfaches Laden
if [ -n "${_SYSTEM_USER_LOADED+x}" ]; then
    return 0
fi
_SYSTEM_USER_LOADED=1

# Get user information
get_user_info() {
    # Get current user
    USER_NAME=${VIRT_USER:-$(whoami)}
    USER_UID=$(id -u "$USER_NAME")
    USER_GID=$(id -g "$USER_NAME")
    USER_HOME=${VIRT_HOME:-$(eval echo ~$USER_NAME)}

    # Export variables
    export USER_NAME
    export USER_UID
    export USER_GID
    export USER_HOME

    return 0
}

# Get homelab domain information
get_homelab_domain() {
    # Check if DOMAIN is already set
    if [ -z "${DOMAIN}" ]; then
        # Try to get domain from system config
        if [ -f "/etc/nixos/system-config.nix" ]; then
            DOMAIN=$(grep -oP 'domain\s*=\s*"\K[^"]+' /etc/nixos/system-config.nix)
        fi
    fi

    # Verify domain with user
    if [ -n "${DOMAIN}" ]; then
        if prompt_confirmation "Is ${DOMAIN} the correct domain?"; then
            export DOMAIN
            return 0
        fi
    fi

    # Get new domain from user
    while true; do
        echo -n "Enter domain name (e.g. example.com): "
        read -r NEW_DOMAIN
        if [[ "${NEW_DOMAIN}" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            if prompt_confirmation "Is ${NEW_DOMAIN} correct?"; then
                DOMAIN="${NEW_DOMAIN}"
                export DOMAIN
                return 0
            fi
        else
            echo "Invalid domain format. Please try again."
        fi
    done
}
