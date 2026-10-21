package dev.krtmtthw.plumes.persistence;

import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.SqlSessionTemplate;
import org.mybatis.spring.boot.autoconfigure.ConfigurationCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportRuntimeHints;

/**
 * MyBatis setup that works the same on the JVM and in a GraalVM native image: the mapper is registered by hand
 * (no {@code @MapperScan}, whose factory beans need extra AOT processing), results map to records by constructor
 * argument name, and {@link MyBatisNativeHints} declares what MyBatis reaches by reflection.
 */
@Configuration(proxyBeanMethods = false)
@ImportRuntimeHints(MyBatisNativeHints.class)
public class MyBatisConfig {

    @Bean
    ConfigurationCustomizer plumesMyBatis() {
        return c -> {
            c.setMapUnderscoreToCamelCase(true);
            c.setArgNameBasedConstructorAutoMapping(true);
            c.setDefaultStatementTimeout(5);
            c.setCacheEnabled(false);
            c.setLazyLoadingEnabled(false);
        };
    }

    @Bean
    CatalogueMapper catalogueMapper(SqlSessionFactory factory, SqlSessionTemplate template) {
        if (!factory.getConfiguration().hasMapper(CatalogueMapper.class)) {
            factory.getConfiguration().addMapper(CatalogueMapper.class);
        }
        return template.getMapper(CatalogueMapper.class);
    }
}
