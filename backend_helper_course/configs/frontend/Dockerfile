FROM node:25.0.0 AS build

WORKDIR /app
COPY frontend_helper_course/package.json frontend_helper_course/package-lock.json ./
RUN npm ci

COPY frontend_helper_course/ ./

RUN npm run build