package dev.krtmtthw.plumes.web;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Identity of this build: the contract it serves (contracts/openapi.yaml info.version) and its own version. */
@Component
public class ApiInfo {

    /** Must equal info.version in contracts/openapi.yaml (checked by a test). */
    public static final String CONTRACT = "1.0.0";
    public static final String IMPL = "java";

    private final String implVersion;
    private final String commit;

    public ApiInfo(@Value("${plumes.impl-version}") String implVersion, @Value("${plumes.commit}") String commit) {
        this.implVersion = implVersion;
        this.commit = commit;
    }

    public String implVersion() { return implVersion; }
    public String commit() { return commit; }

    public String etag(String dataVersion) {
        return Etags.of(CONTRACT, IMPL, implVersion, dataVersion);
    }
}
