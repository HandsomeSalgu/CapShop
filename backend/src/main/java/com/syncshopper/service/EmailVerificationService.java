package com.syncshopper.service;

import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;

import java.util.Map;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class EmailVerificationService {

    private final JavaMailSender mailSender;
    
    @Value("${spring.mail.username}")
    private String fromAddress;
    
    // 이메일을 키로, [인증코드, 만료시간(ms)] 객체를 값으로 저장하는 인메모리 맵
    private final Map<String, VerificationInfo> verificationMap = new ConcurrentHashMap<>();
    private static final long EXPIRE_DURATION_MS = 5 * 60 * 1000; // 5분

    public EmailVerificationService(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }

    public void sendVerificationCode(String email) {
        String code = generateRandomCode();
        
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromAddress);
        message.setTo(email);
        message.setSubject("[SyncShopper] 회원가입 이메일 인증 안내");
        message.setText("안녕하세요.\n\n요청하신 인증번호는 [" + code + "] 입니다.\n5분 내에 입력해 주세요.");
        
        mailSender.send(message);
        
        long expireAt = System.currentTimeMillis() + EXPIRE_DURATION_MS;
        verificationMap.put(email, new VerificationInfo(code, expireAt));
    }

    public void sendTemporaryPassword(String email, String tempPassword) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromAddress);
        message.setTo(email);
        message.setSubject("[SyncShopper] 임시 비밀번호 발급 안내");
        message.setText("안녕하세요.\n\n요청하신 임시 비밀번호는 [" + tempPassword + "] 입니다.\n로그인 후 반드시 비밀번호를 변경해 주세요.");
        
        mailSender.send(message);
    }

    public boolean verifyCode(String email, String code) {
        VerificationInfo info = verificationMap.get(email);
        if (info == null) {
            return false;
        }
        
        if (System.currentTimeMillis() > info.expireAt) {
            verificationMap.remove(email); // 만료된 코드 삭제
            return false;
        }
        
        if (info.code.equals(code)) {
            verificationMap.remove(email); // 인증 성공 후 삭제
            return true;
        }
        
        return false;
    }

    private String generateRandomCode() {
        Random random = new Random();
        int code = 100000 + random.nextInt(900000); // 100000 ~ 999999
        return String.valueOf(code);
    }
    
    private static class VerificationInfo {
        String code;
        long expireAt;

        VerificationInfo(String code, long expireAt) {
            this.code = code;
            this.expireAt = expireAt;
        }
    }
}
