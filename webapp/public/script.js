// 🎤 전역 상태
let isRecording = false;
let recognition;
const recordBtn = document.getElementById('recordBtn');
const statusDiv = document.getElementById('status');
const chatContainer = document.getElementById('chatContainer');

// 🎙️ 음성 인식 설정
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'ko-KR';

  recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript.trim();
    if (!transcript) return;

    addChatBubble(transcript, 'user');

    const response = await fetch('/chat-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: transcript,
        system_prompt: "You are a GPT-4o audio response bot acting as a youth counselor assistant.\n\
          Always respond in English with a soft, sincere, and comforting voice.\n\
          Speak to teenagers facing emotional, social, or personal challenges.\n\
          Your tone must be warm, caring, empathetic, and reassuring—like a safe, supportive friend.\n\
          Try to keep responses concise, clear, and kind.\n\
          If the assistant response is too long, truncate or revise before calling the model again.\n\
          Never judge — just listen, support, and gently guide with compassion.",
        voice: 'shimmer'
      })
    });

    const data = await response.json();
    if (data.text) {
      addChatBubble(data.text, 'bot');
      if (data.audio_base64) {
        const audio = new Audio("data:audio/mp3;base64," + data.audio_base64);
        audio.play();
      }
    } else {
      addChatBubble('❌ 챗봇 응답 오류', 'bot');
    }
  };

  recognition.onerror = (e) => {
    console.error('음성 인식 오류:', e);
    addChatBubble('❌ 음성 인식 실패', 'bot');
  };
} else {
  alert('이 브라우저는 음성 인식을 지원하지 않아요 😢');
}

function addChatBubble(message, from = 'user') {
  const container = document.createElement('div');
  container.className = `flex items-end gap-2 ${from === 'user' ? 'justify-end' : 'justify-start'}`;

  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-full flex items-center justify-center text-sm text-white';
  avatar.textContent = from === 'user' ? '🙂' : '🤖';
  avatar.classList.add(from === 'user' ? 'bg-gray-500' : 'bg-blue-500');

  const bubble = document.createElement('div');
  bubble.className = `rounded-xl p-3 shadow max-w-xs w-fit text-sm ${from === 'user' ? 'bg-green-100 text-right' : 'bg-white text-left'}`;
  bubble.innerHTML = message;

  if (from === 'user') {
    container.appendChild(bubble);
    container.appendChild(avatar);
  } else {
    container.appendChild(avatar);
    container.appendChild(bubble);
  }

  chatContainer.appendChild(container);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}
recordBtn.addEventListener('click', () => {
  if (!isRecording) {
    recognition?.start();
    recordBtn.textContent = 'Stop Recording';
    statusDiv.textContent = '🔴 Listening...';
    isRecording = true;
  } else {
    recognition?.stop();
    recordBtn.textContent = 'Start Recording';
    statusDiv.textContent = '⏹️ Stopped';
    isRecording = false;
  }
});
