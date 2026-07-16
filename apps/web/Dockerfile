# Build context is the repository root so the npm workspaces (root manifest,
# packages/contracts, apps/web) all resolve.
FROM node:20-slim AS build

WORKDIR /repo

COPY package.json package-lock.json ./
COPY packages/contracts/package.json packages/contracts/package.json
COPY apps/web/package.json apps/web/package.json
RUN npm ci

COPY packages/contracts ./packages/contracts
COPY apps/web ./apps/web
RUN npm run build --workspace=apps/web

FROM nginx:1.27-alpine
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/apps/web/dist /usr/share/nginx/html
EXPOSE 80
