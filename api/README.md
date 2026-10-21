# api

The read-only Java 17 Spring Boot (MyBatis) API on PostGIS, built as a GraalVM native image, pushed to a private GHCR image and run on Render free (DECISIONS Q3, Q20, S7). Owned by the API agent.

Its JSON for a volcano must equal the static read model (`../contracts/schemas/volcano.schema.json`); the contract test compares them. The pipeline publishes each data version first; loading it into Neon is a separate step.
