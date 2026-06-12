<script setup>
</script>

<template>
  <footer>
    <div class="container">
      <div class="footer-grid">
        <div class="footer-col">
          <div class="footer-logo">로고</div>
          <p class="footer-desc">홈페이지에 대한 설명이 적혀있습니다. 당사는 모던하고 감각적인 디자인의 프리미엄 상품을 제공합니다.</p>
          <div class="footer-checks">
            <label><input type="checkbox" checked disabled> 주소: 서울특별시 강남구</label>
            <label><input type="checkbox" checked disabled> 이메일: contact@domain.com</label>
            <label><input type="checkbox" checked disabled> 핸드폰 번호: 010-1234-5678</label>
          </div>
        </div>
        <div class="footer-col">
          <h4>정보</h4>
          <ul>
            <li><a href="#">회사 소개 문장</a></li>
            <li><a href="#">이용약관 문장</a></li>
            <li><a href="#">개인정보처리방침 문장</a></li>
            <li><a href="#">채용 정보 문장</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>고객 서비스</h4>
          <ul>
            <li><a href="#">고객센터 문의 문장</a></li>
            <li><a href="#">배송 안내 문장</a></li>
            <li><a href="#">반품 및 교환 안내 문장</a></li>
            <li><a href="#">공지사항 / FAQ 문장</a></li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <p>카피라이터 Copyright © 2026 로고 All rights reserved.</p>
        <div class="socials">
          <a href="#"><i class="fa-brands fa-facebook-f"></i></a>
          <a href="#"><i class="fa-brands fa-twitter"></i></a>
          <a href="#"><i class="fa-brands fa-instagram"></i></a>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
footer {
  background-color: #111111;
  color: #ffffff;
  padding: 80px 0 40px;
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 50px;
  margin-bottom: 60px;
  border-bottom: 1px solid #333333;
  padding-bottom: 60px;
}

.footer-logo {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 20px;
  color: #ffffff;
}

.footer-desc {
  font-size: 14px;
  color: #999999;
  margin-bottom: 30px;
  line-height: 1.8;
  max-width: 90%;
}

.footer-checks label {
  display: block;
  margin-bottom: 10px;
  font-size: 14px;
  color: #cccccc;
  cursor: pointer;
}

.footer-checks input {
  margin-right: 8px;
  accent-color: var(--accent-color);
}

.footer-col h4 {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 25px;
  color: #ffffff;
}

.footer-col ul li {
  margin-bottom: 15px;
  font-size: 14px;
  color: #999999;
}

.footer-col ul li a:hover {
  color: #ffffff;
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #777777;
}

.socials {
  display: flex;
  gap: 15px;
}

.socials a {
  color: #777777;
  font-size: 18px;
}

.socials a:hover {
  color: #ffffff;
}
</style>
