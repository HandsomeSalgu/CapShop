package com.syncshopper.security;

import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Date;
import java.util.HexFormat;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class JwtBlacklistService {

    private final Map<String, Long> blacklistedTokens = new ConcurrentHashMap<>();

    public void blacklist(String token, Date expiresAt) {
        if (token == null || expiresAt == null) {
            return;
        }

        cleanupExpiredTokens();

        long expirationMillis = expiresAt.getTime();
        if (expirationMillis <= Instant.now().toEpochMilli()) {
            return;
        }

        blacklistedTokens.put(hash(token), expirationMillis);
    }

    public boolean isBlacklisted(String token) {
        if (token == null) {
            return false;
        }

        Long expirationMillis = blacklistedTokens.get(hash(token));
        if (expirationMillis == null) {
            return false;
        }

        if (expirationMillis <= Instant.now().toEpochMilli()) {
            blacklistedTokens.remove(hash(token), expirationMillis);
            return false;
        }

        return true;
    }

    private void cleanupExpiredTokens() {
        long now = Instant.now().toEpochMilli();
        blacklistedTokens.entrySet().removeIf(entry -> entry.getValue() <= now);
    }

    private String hash(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(token.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 algorithm is not available.", e);
        }
    }
}
