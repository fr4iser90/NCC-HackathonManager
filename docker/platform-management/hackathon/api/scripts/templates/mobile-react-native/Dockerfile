# React Native (Expo) Dockerfile (für Web-Builds)
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 19006

# Set up non-root user
RUN adduser -D appuser && chown -R appuser /app
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --spider -q http://localhost:19006 || exit 1

CMD ["npm", "start"]
