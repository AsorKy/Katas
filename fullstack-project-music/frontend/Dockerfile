# etapa 1: construir (Node no viajará a la imagen final)
FROM node:22-slim AS build
WORKDIR /app
# (1) los dos archivos de dependencias de npm
COPY package.json package-lock.json ./
# (2) instala exactamente lo que dice el lock
RUN npm ci
COPY . .
RUN npm run build

# etapa 2: servir solo estáticos
FROM nginx:alpine
# trae dist/ desde la etapa anterior, por su nombre
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
