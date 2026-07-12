# 1. Base 이미지 지정 (pom.xml의 Java 23 버전에 맞춤)
FROM eclipse-temurin:23-jdk

# 2. 빌드된 jar 파일의 위치를 변수로 지정 (Gradle -> Maven 경로로 수정, 프로젝트 폴더 반영)
ARG JAR_FILE=backend/target/*-SNAPSHOT.jar

# 3. jar 파일을 컨테이너 내부로 복사하며 이름을 app.jar로 변경
COPY ${JAR_FILE} app.jar

# 4. 컨테이너 실행 시 애플리케이션 구동 명령어 정의
ENTRYPOINT ["java", "-jar", "/app.jar"]
