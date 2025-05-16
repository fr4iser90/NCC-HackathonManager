FROM postgres:16-alpine

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Set locale
ENV LANG en_US.utf8
