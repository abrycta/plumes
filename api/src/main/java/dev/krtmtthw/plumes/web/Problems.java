package dev.krtmtthw.plumes.web;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

/**
 * RFC 9457 problem documents, the same shape as Replay's backends and edge: {@code type, title, status, detail,
 * instance, code}. Never a stack trace or SQL.
 */
public final class Problems {

    public static final String BASE = "https://plumes.krtmtthw.dev/problems/";
    public static final MediaType PROBLEM_JSON = MediaType.parseMediaType("application/problem+json");
    private static final ObjectMapper JSON = new ObjectMapper();

    public enum Code {
        NOT_FOUND("not-found", 404, "Not found"),
        INVALID_PARAMETER("invalid-parameter", 400, "Invalid query parameter"),
        METHOD_NOT_ALLOWED("method-not-allowed", 405, "Method not allowed"),
        FORBIDDEN("forbidden", 403, "Requests must come through the site's edge proxy"),
        NOT_READY("not-ready", 503, "Not ready"),
        INTERNAL("internal", 500, "Internal error");

        final String code;
        final int status;
        final String title;

        Code(String code, int status, String title) {
            this.code = code;
            this.status = status;
            this.title = title;
        }
    }

    private Problems() { }

    public static String body(Code c, String detail, String instance) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("type", BASE + c.code);
        m.put("title", c.title);
        m.put("status", c.status);
        if (detail != null) m.put("detail", detail);
        if (instance != null) m.put("instance", instance);
        m.put("code", c.code);
        try {
            return JSON.writeValueAsString(m);
        } catch (JacksonException e) {
            throw new IllegalStateException(e);
        }
    }

    /** 404s on data paths are cacheable for a while (they change only with a data version); the rest are not. */
    static String cacheControl(Code c, String path) {
        return c == Code.NOT_FOUND && path.startsWith("/v1/") ? CachePolicy.NOT_FOUND : CachePolicy.NO_STORE;
    }

    public static ResponseEntity<String> entity(Code c, String detail, HttpServletRequest request) {
        ResponseEntity.BodyBuilder b = ResponseEntity.status(HttpStatus.valueOf(c.status))
                .contentType(PROBLEM_JSON)
                .header(HttpHeaders.CACHE_CONTROL, cacheControl(c, request.getRequestURI()));
        if (c == Code.NOT_READY) b.header(HttpHeaders.RETRY_AFTER, "5");
        return b.body(body(c, detail, instance(request)));
    }

    public static void write(HttpServletResponse response, Code c, String detail, HttpServletRequest request) throws IOException {
        response.setStatus(c.status);
        response.setContentType(PROBLEM_JSON.toString());
        response.setCharacterEncoding("UTF-8");
        response.setHeader(HttpHeaders.CACHE_CONTROL, cacheControl(c, request.getRequestURI()));
        response.getWriter().write(body(c, detail, instance(request)));
    }

    static String instance(HttpServletRequest request) {
        String q = request.getQueryString();
        String path = request.getRequestURI();
        String s = q == null ? path : path + "?" + q;
        return s.length() > 300 ? s.substring(0, 300) : s;
    }
}
