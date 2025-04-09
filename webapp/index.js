const livereload = require('livereload');
const connectLivereload = require('connect-livereload');

const liveReloadServer = livereload.createServer();
liveReloadServer.watch(__dirname + "/views");
liveReloadServer.watch(__dirname + "/public");

const express = require('express');
const path = require('path');
const app = express();
const PORT = 3000;

// OpenAI 라우터 연결을 위한 추가
require('dotenv').config();  // ← 환경변수 불러오기
const chatRouter = require('./routes/chat'); // ← chat.js 불러오기

// Express에 미들웨어 추가
app.use(connectLivereload());

// EJS 템플릿 설정
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 정적 파일 제공
app.use(express.static(path.join(__dirname, 'public')));

// JSON 요청 처리 (OpenAI와 주고받기 위해 꼭 필요)
app.use(express.json());

// 기본 라우팅
app.get('/', (req, res) => {
  res.render('index');
});

// /chat 경로에 chat 라우터 연결
app.use('/chat', chatRouter);

app.listen(3000, '0.0.0.0', () => {
  console.log('✅ Server running on http://0.0.0.0:3000');
});

// .ejs 파일 변경 시 자동 새로고침 트리거
liveReloadServer.server.once("connection", () => {
  setTimeout(() => {
    liveReloadServer.refresh("/");
  }, 100);
});
