# The day-5 Tron lab page: the worksheet, the query page with the snapshot, and the saved results, served by nginx.
# Build context: dynamic-labs/tron. The query page is built here, so the image needs no outside network to run.
FROM node:22-alpine AS build
WORKDIR /lab/query-page
COPY query-page/package.json query-page/package-lock.json ./
RUN npm ci --ignore-scripts
COPY query-page/ ./
COPY queries/ /lab/queries/
COPY snapshot/ /lab/snapshot/
RUN node build.mjs

FROM nginx:alpine
COPY gateway/default.conf /etc/nginx/conf.d/default.conf
COPY static/ /usr/share/nginx/html/
COPY --from=build /lab/query-page/dist/ /usr/share/nginx/html/query/
COPY snapshot/ /usr/share/nginx/html/snapshot/
