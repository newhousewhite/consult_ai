require('dotenv').config();
const express = require('express');
const router = express.Router();
const axios = require('axios');

// POST /chat
router.post('/', async (req, res) => {
  const userMessage = req.body.message;

  try {
    // Python API 서버로 POST 요청
    const response = await axios.post('http://localhost:5001/generate', {
      prompt: userMessage
    });

    const botReply = response.data.response; // FastAPI가 반환한 텍스트
    res.json({ reply: botReply });
  } catch (error) {
    console.error('Python API 호출 오류:', error.message);
    res.status(500).json({ error: 'AI 서버 응답 오류' });
  }
});

module.exports = router;