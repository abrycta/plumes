FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src src
RUN mvn -q -B package -DskipTests && java -Djarmode=tools -jar target/app.jar extract --destination /out

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /out /app
# CDS training run (Spring Boot 3.3+): stops after context refresh, writes the class archive
RUN java -XX:ArchiveClassesAtExit=app.jsa -Dspring.context.exit=onRefresh -jar app.jar || true
ENV JAVA_TOOL_OPTIONS="-XX:SharedArchiveFile=app.jsa -XX:MaxRAMPercentage=60 -XX:+UseSerialGC -XX:TieredStopAtLevel=1 -Xss512k"
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
