# 1. Build Stage
FROM node:20-alpine AS build
WORKDIR /app

# 의존성 캐싱을 위해 package.json과 package-lock.json 복사
COPY package*.json ./
RUN npm ci

# 소스코드 전체 복사 및 빌드 실행
COPY . .
RUN npm run build

# 2. Run Stage (Nginx 배포)
FROM nginx:alpine

# 빌드 산출물 복사
COPY --from=build /app/dist /usr/share/nginx/html

# 커스텀 Nginx 설정 파일 적용
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 80 포트 노출
EXPOSE 80

# Nginx 백그라운드 구동 방지
CMD ["nginx", "-g", "daemon off;"]
