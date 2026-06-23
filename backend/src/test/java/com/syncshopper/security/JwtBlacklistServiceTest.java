package com.syncshopper.security;

import org.junit.jupiter.api.Test;

import java.util.Date;

import static org.assertj.core.api.Assertions.assertThat;

class JwtBlacklistServiceTest {

    private final JwtBlacklistService jwtBlacklistService = new JwtBlacklistService();

    @Test
    void blacklistedTokenIsRejectedUntilItExpires() {
        jwtBlacklistService.blacklist("token", new Date(System.currentTimeMillis() + 60_000));

        assertThat(jwtBlacklistService.isBlacklisted("token")).isTrue();
    }

    @Test
    void expiredBlacklistedTokenIsIgnored() {
        jwtBlacklistService.blacklist("expired-token", new Date(System.currentTimeMillis() - 1_000));

        assertThat(jwtBlacklistService.isBlacklisted("expired-token")).isFalse();
    }
}
