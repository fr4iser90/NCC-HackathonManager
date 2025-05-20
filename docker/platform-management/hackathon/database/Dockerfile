FROM postgres:16-alpine

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Set locale
ENV LANG en_US.utf8

# Add non-root user (Postgres image already uses 'postgres' user by default)
USER postgres

# Add HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD pg_isready -U postgres || exit 1
