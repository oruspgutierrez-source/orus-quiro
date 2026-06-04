# Stage 1: Build the Vite application
FROM node:18-alpine AS build

WORKDIR /app

# Copiamos archivos de dependencias
COPY package.json package-lock.json* ./

# Instalamos las dependencias
RUN npm ci

# Copiamos todo el codigo fuente
COPY . .

# Variables de entorno en build time, en caso de requerirlas, se inyectarian aqui
# Construimos la app para produccion
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Limpiar archivos estaticos predeterminados de nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar build desde el stage de compilacion
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuracion de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
