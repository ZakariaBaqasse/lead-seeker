FROM oven/bun:alpine AS deps
WORKDIR /app

COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

FROM oven/bun:alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 5173
ENV PORT=5173
CMD ["bun", "run", "dev", "--host"]

FROM oven/bun:alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN bun run build

FROM node:20-alpine AS prod
WORKDIR /app
COPY --from=build /app/build ./build
EXPOSE 5173
ENV PORT=5173
ENV HOST=0.0.0.0
CMD ["node", "build"]