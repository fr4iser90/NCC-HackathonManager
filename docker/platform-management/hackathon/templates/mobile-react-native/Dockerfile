# React Native (Expo) Dockerfile (für Web-Builds)
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 19006
CMD ["npm", "start"]
