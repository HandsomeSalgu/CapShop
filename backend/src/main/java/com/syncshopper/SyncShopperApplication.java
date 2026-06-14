package com.syncshopper;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class SyncShopperApplication {

	public static void main(String[] args) {
		SpringApplication.run(SyncShopperApplication.class, args);
	}

}
