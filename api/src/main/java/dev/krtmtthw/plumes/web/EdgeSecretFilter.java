package dev.krtmtthw.plumes.web;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * When {@code PLUMES_EDGE_SECRET} is set, {@code /v1/*} answers only requests that carry it in {@code X-Edge-Secret}
 * (the Pages function adds it). Reads that skip the edge cache would spend Render's shared 5 GB of egress, so they
 * get a 200-byte 403 instead. {@code /healthz} and {@code /readyz} stay open.
 */
@Component
public class EdgeSecretFilter extends OncePerRequestFilter {

    public static final String HEADER = "X-Edge-Secret";
    private final byte[] secret;

    public EdgeSecretFilter(@Value("${plumes.edge-secret:}") String secret) {
        this.secret = secret.getBytes(StandardCharsets.UTF_8);
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return secret.length == 0 || !request.getRequestURI().startsWith("/v1/");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String given = request.getHeader(HEADER);
        if (given == null || !MessageDigest.isEqual(secret, given.getBytes(StandardCharsets.UTF_8))) {
            Problems.write(response, Problems.Code.FORBIDDEN, null, request);
            return;
        }
        chain.doFilter(request, response);
    }
}
