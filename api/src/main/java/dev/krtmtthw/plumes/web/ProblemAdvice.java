package dev.krtmtthw.plumes.web;

import jakarta.servlet.http.HttpServletRequest;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.NoHandlerFoundException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

import dev.krtmtthw.plumes.catalogue.CatalogueService.InvalidQuery;
import dev.krtmtthw.plumes.catalogue.CatalogueService.NotFound;
import dev.krtmtthw.plumes.web.Problems.Code;

/** Every error becomes a problem document. */
@RestControllerAdvice
public class ProblemAdvice {

    private static final Logger log = LoggerFactory.getLogger(ProblemAdvice.class);

    @ExceptionHandler(InvalidQuery.class)
    ResponseEntity<String> invalid(InvalidQuery e, HttpServletRequest r) {
        return Problems.entity(Code.INVALID_PARAMETER, e.getMessage(), r);
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    ResponseEntity<String> mismatch(MethodArgumentTypeMismatchException e, HttpServletRequest r) {
        String type = e.getRequiredType() == null ? "value" : e.getRequiredType().getSimpleName();
        String hint = "LocalDate".equals(type) ? "a date (YYYY-MM-DD)" : "Double".equals(type) || "Integer".equals(type) ? "a number" : type;
        return Problems.entity(Code.INVALID_PARAMETER, e.getName() + ": must be " + hint, r);
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    ResponseEntity<String> missing(MissingServletRequestParameterException e, HttpServletRequest r) {
        return Problems.entity(Code.INVALID_PARAMETER, e.getParameterName() + ": required", r);
    }

    @ExceptionHandler(NotFound.class)
    ResponseEntity<String> notFound(NotFound e, HttpServletRequest r) {
        return Problems.entity(Code.NOT_FOUND, e.getMessage(), r);
    }

    @ExceptionHandler({NoHandlerFoundException.class, NoResourceFoundException.class})
    ResponseEntity<String> noRoute(Exception e, HttpServletRequest r) {
        return Problems.entity(Code.NOT_FOUND, null, r);
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    ResponseEntity<String> method(HttpRequestMethodNotSupportedException e, HttpServletRequest r) {
        return ResponseEntity.status(405).header("Allow", "GET, HEAD")
                .contentType(Problems.PROBLEM_JSON).header("Cache-Control", CachePolicy.NO_STORE)
                .body(Problems.body(Code.METHOD_NOT_ALLOWED, null, Problems.instance(r)));
    }

    @ExceptionHandler(DatasetCache.NotReady.class)
    ResponseEntity<String> notReady(DatasetCache.NotReady e, HttpServletRequest r) {
        return Problems.entity(Code.NOT_READY, e.getMessage(), r);
    }

    /** Neon scales to zero: while its compute resumes, say so (the edge turns this into "waking" and retries). */
    @ExceptionHandler(DataAccessException.class)
    ResponseEntity<String> database(DataAccessException e, HttpServletRequest r) {
        log.warn("database unavailable: {}", e.getMostSpecificCause().getClass().getSimpleName());
        return Problems.entity(Code.NOT_READY, "the database is not reachable yet; retry shortly", r);
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<String> other(Exception e, HttpServletRequest r) {
        log.error("unhandled", e);
        return Problems.entity(Code.INTERNAL, null, r);
    }
}
