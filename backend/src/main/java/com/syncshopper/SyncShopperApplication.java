package com.syncshopper;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.CacheManager;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.Bean;

import org.springframework.scheduling.annotation.EnableScheduling;

@EnableCaching
@EnableScheduling
@SpringBootApplication
@ConfigurationPropertiesScan
public class SyncShopperApplication {

	public static void main(String[] args) {
		loadDotEnv();
		SpringApplication.run(SyncShopperApplication.class, args);
	}

	private static void loadDotEnv() {
		java.nio.file.Path envPath = java.nio.file.Paths.get(".env");
		if (!java.nio.file.Files.exists(envPath)) {
			// If running from root directory, check backend/.env
			envPath = java.nio.file.Paths.get("backend", ".env");
		}
		if (java.nio.file.Files.exists(envPath)) {
			try {
				java.util.List<String> lines = java.nio.file.Files.readAllLines(envPath);
				for (String line : lines) {
					line = line.trim();
					if (line.isEmpty() || line.startsWith("#")) {
						continue;
					}
					int eqIndex = line.indexOf('=');
					if (eqIndex > 0) {
						String key = line.substring(0, eqIndex).trim();
						String value = line.substring(eqIndex + 1).trim();
						if (value.startsWith("\"") && value.endsWith("\"")) {
							value = value.substring(1, value.length() - 1);
						} else if (value.startsWith("'") && value.endsWith("'")) {
							value = value.substring(1, value.length() - 1);
						}
						// Only set if not already present in environment
						if (System.getProperty(key) == null && System.getenv(key) == null) {
							System.setProperty(key, value);
						}
					}
				}
			} catch (java.io.IOException e) {
				System.err.println("Failed to load .env file: " + e.getMessage());
			}
		}
	}

	@Bean
	public CacheManager cacheManager() {
		return new ConcurrentMapCacheManager("commerceSearch", "commerceTop3");
	}

}
