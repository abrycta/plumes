# syntax=docker/dockerfile:1.10
# Plumes API as a GraalVM native image (DECISIONS S7: the JVM needed 78-96 s to /readyz at Render free's 0.1 CPU).
# Build context: the repository root (the OpenAPI document lives in contracts/):
#   docker build -f api/Dockerfile -t plumes-api .
# Stages: Maven + GraalVM CE (JDK 25; the code targets Java 17) -> native executable -> distroless runtime.

FROM maven:3.9.11-eclipse-temurin-25 AS maven

FROM ghcr.io/graalvm/native-image-community:25 AS build
COPY --from=maven /usr/share/maven /usr/share/maven
ENV PATH=/usr/share/maven/bin:$PATH MAVEN_OPTS="-XX:+UseParallelGC"
WORKDIR /src/api
COPY api/pom.xml ./
# Dependencies and the AOT/native plugins in their own layer (cached by CI between builds).
RUN mvn -B -q -Pnative dependency:go-offline -DexcludeReactor=false || true
COPY contracts/openapi.yaml /src/contracts/openapi.yaml
COPY api/src ./src
RUN mvn -B -Pnative -DskipTests native:compile \
 && ls -la target/plumes-api

FROM gcr.io/distroless/base-debian12:nonroot AS runtime
COPY --from=build /src/api/target/plumes-api /app/plumes-api
ARG COMMIT_SHA=unknown
ENV PLUMES_COMMIT=${COMMIT_SHA} PORT=8080
EXPOSE 8080
# The heap cap leaves room on Render free's 512 MB; -X options are read by the native runtime, not by main(), so
# `docker run <image> load <data> ...` still reaches the loader.
ENTRYPOINT ["/app/plumes-api", "-Xmx160m"]
