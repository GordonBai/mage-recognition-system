FROM node:16-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

# 创建缓存目录并设置权限
RUN mkdir -p /app/node_modules/.cache && chmod -R 777 /app/node_modules/.cache

COPY . .
RUN npm run build

FROM nginx:1.21-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"] 