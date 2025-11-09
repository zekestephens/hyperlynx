import React, { useState, useRef, useEffect } from 'react';

const CHAT_API_URL = '/api/chat/'; // Your Django endpoint

function Chatbot() {
    // State to hold the conversation history
    const [messages, setMessages] = useState([
        { sender: 'Sparky', text: "Hello! I'm your Gemini assistant. How can I help you?" }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    // Ref for auto-scrolling the chat window
    const messagesEndRef = useRef(null);

    // Auto-scroll to the latest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Function to get the CSRF token from the cookie (essential for Django POST)
    const getCookie = (name) => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };


    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        // 1. Add user message to state
        setMessages(prev => [...prev, { sender: 'You', text: userMessage }]);
        setInput('');
        setIsLoading(true);

        try {
            const csrfToken = getCookie('csrftoken');

            // 2. Send request to Django backend
            const response = await fetch(CHAT_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken, // Use the CSRF token
                },
                body: JSON.stringify({ message: userMessage })
            });

            const data = await response.json();

            // 3. Add bot response to state
            if (response.ok) {
                setMessages(prev => [...prev, { sender: 'Sparky', text: data.response }]);
            } else {
                setMessages(prev => [...prev, { sender: 'System Error', text: data.error || "Received an unknown error from the server." }]);
            }

        } catch (error) {
            console.error("Fetch error:", error);
            setMessages(prev => [...prev, { sender: 'System Error', text: "Could not connect to the Django server." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: '600px', margin: '0 auto', border: '1px solid #ccc', borderRadius: '8px', overflow: 'hidden' }}>
            <h2>Gemini Chatbot</h2>

            {/* Chat Window */}
            <div style={{ height: '400px', overflowY: 'scroll', padding: '10px', backgroundColor: '#f9f9f9' }}>
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        style={{
                            marginBottom: '10px',
                            textAlign: msg.sender === 'You' ? 'right' : 'left'
                        }}
                    >
                        <span
                            style={{
                                display: 'inline-block',
                                padding: '8px 12px',
                                borderRadius: '15px',
                                backgroundColor: msg.sender === 'You' ? '#007bff' : '#e0e0e0',
                                color: msg.sender === 'You' ? 'white' : 'black'
                            }}
                        >
                            {msg.text}
                        </span>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <form onSubmit={handleSend} style={{ display: 'flex', padding: '10px', borderTop: '1px solid #ccc' }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={isLoading}
                    placeholder={isLoading ? "Waiting for response..." : "Type your message..."}
                    style={{ flexGrow: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '5px 0 0 5px' }}
                />
                <button
                    type="submit"
                    disabled={isLoading}
                    style={{ padding: '10px 15px', backgroundColor: isLoading ? '#6c757d' : '#28a745', color: 'white', border: 'none', borderRadius: '0 5px 5px 0', cursor: 'pointer' }}
                >
                    {isLoading ? 'Sending...' : 'Send'}
                </button>
            </form>
        </div>
    );
}

export default Chatbot;