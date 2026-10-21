package dev.krtmtthw.plumes.persistence;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.TreeSet;

import org.apache.ibatis.cache.decorators.FifoCache;
import org.apache.ibatis.cache.decorators.LruCache;
import org.apache.ibatis.cache.decorators.SoftCache;
import org.apache.ibatis.cache.decorators.WeakCache;
import org.apache.ibatis.cache.impl.PerpetualCache;
import org.apache.ibatis.javassist.util.proxy.ProxyFactory;
import org.apache.ibatis.javassist.util.proxy.RuntimeSupport;
import org.apache.ibatis.logging.Log;
import org.apache.ibatis.logging.commons.JakartaCommonsLoggingImpl;
import org.apache.ibatis.logging.jdk14.Jdk14LoggingImpl;
import org.apache.ibatis.logging.log4j2.Log4j2Impl;
import org.apache.ibatis.logging.nologging.NoLoggingImpl;
import org.apache.ibatis.logging.slf4j.Slf4jImpl;
import org.apache.ibatis.logging.stdout.StdOutImpl;
import org.apache.ibatis.reflection.TypeParameterResolver;
import org.apache.ibatis.scripting.defaults.RawLanguageDriver;
import org.apache.ibatis.scripting.xmltags.XMLLanguageDriver;
import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.springframework.aot.hint.MemberCategory;
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;

import dev.krtmtthw.plumes.catalogue.CatalogueRepository;
import dev.krtmtthw.plumes.catalogue.Model;

/**
 * Reflection and proxy metadata MyBatis needs in a native image (after the MyBatis native sample,
 * github.com/mybatis/spring-boot-starter, mybatis-spring-boot-sample-graalvm): the mapper's JDK proxy and its
 * annotations, the classes MyBatis instantiates by name, and the result records it builds by constructor.
 */
class MyBatisNativeHints implements RuntimeHintsRegistrar {

    private static final MemberCategory[] ALL = MemberCategory.values();

    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.proxies().registerJdkProxy(CatalogueMapper.class);
        hints.reflection().registerType(CatalogueMapper.class, ALL);
        for (Class<?> c : new Class<?>[] {
                RawLanguageDriver.class, XMLLanguageDriver.class, RuntimeSupport.class, ProxyFactory.class,
                Slf4jImpl.class, Log.class, JakartaCommonsLoggingImpl.class, Log4j2Impl.class, Jdk14LoggingImpl.class,
                StdOutImpl.class, NoLoggingImpl.class, SqlSessionFactory.class, SqlSessionFactoryBean.class,
                PerpetualCache.class, FifoCache.class, LruCache.class, SoftCache.class, WeakCache.class,
                ArrayList.class, HashMap.class, LinkedHashMap.class, HashSet.class, TreeSet.class,
                TypeParameterResolver.class}) {
            hints.reflection().registerType(c, ALL);
        }
        for (Class<?> c : Model.class.getDeclaredClasses()) {
            hints.reflection().registerType(c, ALL);
        }
        hints.reflection().registerType(CatalogueRepository.EventQuery.class, ALL);
    }
}
