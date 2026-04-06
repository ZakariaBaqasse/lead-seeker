# syntax=docker/dockerfile:1.7

FROM oven/bun:alpine

WORKDIR /app

# Install deps (cached layer)
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

# App code
COPY . ./

EXPOSE 5173

CMD ["bun", "run", "dev","--host"]