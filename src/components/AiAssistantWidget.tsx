import React, { useState, useEffect, useRef } from 'react';
import { User } from '../types';
import { AiAgentService, AgentExecutionResult, ActionTraceStep } from '../store/aiAgentService';
import { SheffieldLogo } from './SheffieldLogo';

interface MessageItem {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  trace?: ActionTraceStep[];
  actionType?: string;
}

interface AiAssistantWidgetProps {
  user: User | null;
  onNavigate: (page: string) => void;
  onToast: (msg: string, isError?: boolean) => void;
}

export const AiAssistantWidget: React.FC<AiAssistantWidgetProps> = ({ user, onNavigate, onToast }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [inputText, setInputText] = useState<string>('');
  const [isListening, setIsListening] = useState<boolean>(false);
  const [speechSupported, setSpeechSupported] = useState<boolean>(true);
  const [voiceSpeechEnabled, setVoiceSpeechEnabled] = useState<boolean>(true);
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);

  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'welcome-1',
      sender: 'assistant',
      text: 'Hello! I am your Sheffield AI Agent. You can speak into the microphone or type any task in English, Hindi, or Hinglish (e.g. "Book 3 days leave", "Approve Daniel\'s timesheet", "Create G7 vacancy", or "Run October payroll").',
      timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const recognitionRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  // Support opening via custom event from Topbar or anywhere in the app
  useEffect(() => {
    const handleOpenEvent = () => setIsOpen(true);
    window.addEventListener('open-sheffield-ai', handleOpenEvent);
    return () => window.removeEventListener('open-sheffield-ai', handleOpenEvent);
  }, []);

  // Setup Web Speech API for voice dictation
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-GB';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const current = event.resultIndex;
        const transcript = event.results[current][0].transcript;
        setInputText(transcript);
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        setIsListening(false);
        if (event.error === 'not-allowed') {
          onToast('Microphone access was denied. Please allow microphone permissions or type instead.', true);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } catch (e) {
      console.warn('Speech recognition setup error:', e);
      setSpeechSupported(false);
    }
  }, [onToast]);

  const toggleListening = () => {
    if (!speechSupported || !recognitionRef.current) {
      onToast('Speech recognition is not supported in this browser. Please type your query.', true);
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
        onToast('Listening... Speak your task now (English, Hindi or Hinglish)', false);
      } catch (e) {
        console.warn('Could not start recognition:', e);
      }
    }
  };

  const speakText = (text: string) => {
    if (!voiceSpeechEnabled || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      // Remove URLs, markdown asterisks and bullet points for cleaner speech
      const clean = text.replace(/[*_#•]/g, '').slice(0, 180);
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis error:', e);
    }
  };

  const handleSend = (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query) return;

    if (!user) {
      onToast('Please sign in first to run workplace tasks.', true);
      return;
    }

    // Stop listening if active
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    const userMsgId = `user-${Date.now()}`;
    const userMsg: MessageItem = {
      id: userMsgId,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');

    // Execute via AI Agent Service
    setTimeout(() => {
      const result: AgentExecutionResult = AiAgentService.executeCommand(query, user);

      const assistantMsgId = `asst-${Date.now()}`;
      const assistantMsg: MessageItem = {
        id: assistantMsgId,
        sender: 'assistant',
        text: result.message,
        timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
        trace: result.trace,
        actionType: result.actionType,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setExpandedTraceId(assistantMsgId);

      // Speak feedback
      speakText(result.message);

      // Trigger navigation if agent transitioned views
      if (result.targetPage) {
        onNavigate(result.targetPage);
        onToast(result.success ? `AI Agent navigated to: ${result.targetPage.toUpperCase()}` : result.message, !result.success);
      }
    }, 350);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  const quickPrompts = [
    '📅 Book 3 days leave for Aisha',
    "✓ Approve Daniel's leave",
    '⏱ Submit timesheet 37 hours',
    '💼 Create G7 vacancy for Care Coordinator',
    '£ Run October payroll',
    '👤 Switch to Helen (Manager)',
  ];

  return (
    <>
      {/* Floating Widget Launcher (Bottom Right) */}
      {!isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 9000,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: 8,
          }}
        >
          <button
            onClick={() => setIsOpen(true)}
            type="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '12px 20px',
              background: 'linear-gradient(135deg, #005A36, #0D3826)',
              color: '#FFFFFF',
              border: '1px solid #1E7B50',
              borderRadius: 30,
              boxShadow: '0 8px 24px rgba(0, 90, 54, 0.35)',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 14,
              fontFamily: 'Manrope, sans-serif',
              transition: 'transform 0.15s ease, box-shadow 0.15s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
            title="Open Sheffield AI Voice & Task Assistant"
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: '#4ADE80',
                boxShadow: '0 0 8px #4ADE80',
                animation: 'pulse 2s infinite',
              }}
            />
            <span style={{ fontSize: 16 }}>✦</span>
            <span>Sheffield AI Assistant</span>
          </button>
        </div>
      )}

      {/* Expanded AI Drawer */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: 20,
            right: 20,
            width: 'min(440px, 94vw)',
            height: 'min(620px, 86vh)',
            background: '#FFFFFF',
            borderRadius: 16,
            boxShadow: '0 20px 50px rgba(10, 35, 60, 0.22), 0 0 0 1px rgba(0, 90, 54, 0.12)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            fontFamily: "'DM Sans', sans-serif",
            animation: 'fadeInUp 0.2s ease-out',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '14px 18px',
              background: 'linear-gradient(135deg, #005A36, #0A2F1F)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #165637',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <SheffieldLogo size="sm" variant="white" showText={false} />
              <div>
                <strong style={{ display: 'block', fontSize: 14, fontFamily: 'Manrope, sans-serif' }}>
                  Sheffield AI Agent
                </strong>
                <span style={{ fontSize: 11, color: '#A3D9BE', display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: isListening ? '#EF4444' : '#4ADE80',
                    }}
                  />
                  {isListening ? 'Listening via Microphone...' : 'Active · English, Hindi & Hinglish'}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {/* Voice toggle */}
              <button
                type="button"
                onClick={() => setVoiceSpeechEnabled(!voiceSpeechEnabled)}
                title={voiceSpeechEnabled ? 'Mute AI voice output' : 'Enable AI voice output'}
                style={{
                  background: 'rgba(255,255,255,0.12)',
                  border: 'none',
                  color: '#FFFFFF',
                  borderRadius: 6,
                  padding: '6px 8px',
                  cursor: 'pointer',
                  fontSize: 13,
                }}
              >
                {voiceSpeechEnabled ? '🔊' : '🔇'}
              </button>

              {/* Close */}
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Minimize AI Assistant"
                style={{
                  background: 'rgba(255,255,255,0.12)',
                  border: 'none',
                  color: '#FFFFFF',
                  borderRadius: 6,
                  padding: '6px 10px',
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 'bold',
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Quick Prompts Carousel */}
          <div
            style={{
              padding: '8px 12px',
              background: '#F4F7FB',
              borderBottom: '1px solid #E2E8F0',
              display: 'flex',
              gap: 6,
              overflowX: 'auto',
              whiteSpace: 'nowrap',
              scrollbarWidth: 'none',
            }}
          >
            {quickPrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(p.replace(/^[^\s]+\s/, ''))}
                style={{
                  padding: '4px 10px',
                  background: '#FFFFFF',
                  border: '1px solid #D5E1EC',
                  borderRadius: 14,
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#1E3A5F',
                  cursor: 'pointer',
                  flexShrink: 0,
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#E8F3EE')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#FFFFFF')}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Messages Stream */}
          <div
            style={{
              flex: 1,
              padding: 14,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
              background: '#FAFCFE',
            }}
          >
            {messages.map((m) => {
              const isUser = m.sender === 'user';
              return (
                <div
                  key={m.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '86%',
                      padding: '10px 14px',
                      borderRadius: isUser ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                      background: isUser ? '#005A36' : '#FFFFFF',
                      color: isUser ? '#FFFFFF' : '#172C46',
                      border: isUser ? 'none' : '1px solid #E2E8F0',
                      boxShadow: isUser
                        ? '0 2px 6px rgba(0,90,54,0.2)'
                        : '0 2px 6px rgba(20,50,80,0.04)',
                      fontSize: 13,
                      lineHeight: 1.5,
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {m.text}
                  </div>

                  <span
                    style={{
                      fontSize: 10,
                      color: '#8A99AD',
                      marginTop: 3,
                      padding: '0 4px',
                    }}
                  >
                    {m.timestamp}
                  </span>

                  {/* Action Execution Trace Box */}
                  {m.trace && m.trace.length > 0 && (
                    <div
                      style={{
                        marginTop: 8,
                        width: '100%',
                        maxWidth: '92%',
                        background: '#F1F6F3',
                        border: '1px solid #D1E5DC',
                        borderRadius: 10,
                        overflow: 'hidden',
                      }}
                    >
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedTraceId(expandedTraceId === m.id ? null : m.id)
                        }
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '8px 12px',
                          background: '#E4EFEA',
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: 11,
                          fontWeight: 700,
                          color: '#08482B',
                          fontFamily: 'Manrope, sans-serif',
                        }}
                      >
                        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span>⚡</span> Action Execution Flow ({m.trace.length} steps)
                        </span>
                        <span>{expandedTraceId === m.id ? '▲ Hide' : '▼ View Trace'}</span>
                      </button>

                      {expandedTraceId === m.id && (
                        <div style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {m.trace.map((step, idx) => (
                            <div
                              key={idx}
                              style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: 8,
                                fontSize: 11,
                                paddingBottom: 6,
                                borderBottom: idx < m.trace!.length - 1 ? '1px dashed #D1E5DC' : 'none',
                              }}
                            >
                              <div
                                style={{
                                  width: 18,
                                  height: 18,
                                  borderRadius: '50%',
                                  background:
                                    step.status === 'success'
                                      ? '#005A36'
                                      : step.status === 'error'
                                      ? '#DC2626'
                                      : '#D97706',
                                  color: '#FFFFFF',
                                  display: 'grid',
                                  placeItems: 'center',
                                  fontSize: 10,
                                  fontWeight: 'bold',
                                  flexShrink: 0,
                                  marginTop: 1,
                                }}
                              >
                                {step.status === 'success' ? '✓' : step.status === 'error' ? '✕' : '!'}
                              </div>
                              <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 700, color: '#102C50' }}>{step.title}</div>
                                <div style={{ color: '#4B637D', marginTop: 1 }}>{step.detail}</div>
                              </div>
                              <span style={{ fontSize: 9, color: '#7E91A6' }}>{step.timestamp}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Voice Pulse Wave Bar (When Listening) */}
          {isListening && (
            <div
              style={{
                padding: '8px 16px',
                background: '#FEF2F2',
                borderTop: '1px solid #FCA5A5',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                color: '#991B1B',
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: '#DC2626',
                  animation: 'pulse 1s infinite',
                }}
              />
              <span>Listening to speech... speak now!</span>
              <button
                type="button"
                onClick={() => {
                  if (recognitionRef.current) recognitionRef.current.stop();
                  setIsListening(false);
                }}
                style={{
                  marginLeft: 'auto',
                  padding: '3px 8px',
                  background: '#DC2626',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: 4,
                  fontSize: 11,
                  cursor: 'pointer',
                }}
              >
                Stop
              </button>
            </div>
          )}

          {/* Input Area */}
          <div
            style={{
              padding: 12,
              background: '#FFFFFF',
              borderTop: '1px solid #E2E8F0',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            {/* Microphone Dictation Button */}
            <button
              type="button"
              onClick={toggleListening}
              title={isListening ? 'Stop listening' : 'Start voice speech dictation'}
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                border: 'none',
                background: isListening ? '#DC2626' : '#E8F3EE',
                color: isListening ? '#FFFFFF' : '#005A36',
                cursor: 'pointer',
                display: 'grid',
                placeItems: 'center',
                fontSize: 16,
                flexShrink: 0,
                transition: 'background 0.2s',
                boxShadow: isListening ? '0 0 12px rgba(220,38,38,0.5)' : 'none',
              }}
            >
              {isListening ? '⏹' : '🎤'}
            </button>

            {/* Text Input */}
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isListening ? 'Listening...' : 'Type or speak a task...'}
              style={{
                flex: 1,
                padding: '10px 14px',
                border: '1px solid #D5E1EC',
                borderRadius: 22,
                outline: 'none',
                fontSize: 13,
                background: '#F9FBFC',
              }}
            />

            {/* Send Button */}
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={!inputText.trim()}
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                border: 'none',
                background: inputText.trim() ? '#005A36' : '#E2E8F0',
                color: inputText.trim() ? '#FFFFFF' : '#94A3B8',
                cursor: inputText.trim() ? 'pointer' : 'default',
                display: 'grid',
                placeItems: 'center',
                fontSize: 14,
                flexShrink: 0,
                transition: 'background 0.15s',
              }}
              title="Send task to Sheffield AI"
            >
              ➔
            </button>
          </div>
        </div>
      )}
    </>
  );
};
