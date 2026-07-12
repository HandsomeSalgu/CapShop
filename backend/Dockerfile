# 1. Build Stage
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /app

# 의존성 캐싱을 위해 pom.xml을 먼저 복사하고 종속성 다운로드
COPY pom.xml .
RUN mvn dependency:go-offline -B

# 소스코드 복사 및 빌드 (테스트 건너뜀)
COPY src ./src
RUN mvn clean package -DskipTests -B

# 2. Run Stage
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

# 빌드 스테이지에서 생성된 jar 파일 복사
COPY --from=build /app/target/*.jar app.jar

# 애플리케이션 포트 노출
EXPOSE 8080

# 실행 명령어 설정
ENTRYPOINT ["java", "-jar", "app.jar"]
