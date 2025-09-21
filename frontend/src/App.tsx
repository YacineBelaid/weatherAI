import React, { useState, useEffect } from "react";
import "./App.css";
import WeatherService from "./services/WeatherService";
import { WeatherResponse } from "./types";

interface ChatMessage {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  requiresLocation?: boolean;
  suggestedActions?: string[];
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [userLocation, setUserLocation] = useState<string | null>(null);

  useEffect(() => {
    // Add welcome message
    setMessages([
      {
        id: "1",
        type: "assistant",
        content: "Hello! I'm your weather assistant. How can I help you today?",
        timestamp: new Date(),
      },
    ]);
  }, []);

  const addMessage = (
    type: "user" | "assistant",
    content: string,
    requiresLocation?: boolean,
    suggestedActions?: string[]
  ) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
      requiresLocation,
      suggestedActions,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = inputValue.trim();
    addMessage("user", userMessage);
    setInputValue("");
    setLoading(true);

    try {
      const result = await WeatherService.askWeather(userMessage, userLocation);

      if (result.requires_location && !userLocation) {
        addMessage(
          "assistant",
          result.response,
          true,
          result.suggested_actions || []
        );
      } else {
        addMessage("assistant", result.response);
      }
    } catch (err) {
      addMessage(
        "assistant",
        `Sorry, I encountered an error: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSubmit = (location: string) => {
    setUserLocation(location);
    addMessage("user", `I'm in ${location}`);

    // Re-process the last message that required location
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.requiresLocation) {
      handleSubmit(new Event("submit") as any);
    }
  };

  const exampleQueries = [
    "Weather in Paris",
    "Best beach today",
    "Temperature in Madrid",
    "Outdoor activities",
  ];

  return (
    <div className="App">
      <header className="App-header">
        <h1>Weather AI</h1>
        <p>Intelligent weather assistant</p>
        {userLocation && <div className="location-info">📍 {userLocation}</div>}
      </header>

      <main className="App-main">
        <div className="chat-container">
          <div className="messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-content">{message.content}</div>
                {message.suggestedActions &&
                  message.suggestedActions.length > 0 && (
                    <div className="suggested-actions">
                      {message.suggestedActions.map((action, index) => (
                        <button
                          key={index}
                          className="suggestion-button"
                          onClick={() =>
                            handleLocationSubmit(
                              action.replace(/[^\w\s]/g, "").trim()
                            )
                          }
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  )}
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-group">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type your message here..."
                disabled={loading}
                className="message-input"
              />
              <button
                type="submit"
                className="submit-button"
                disabled={loading || !inputValue.trim()}
              >
                Send
              </button>
            </div>
          </form>

          <div className="examples">
            <p>Try these examples:</p>
            <div className="example-buttons">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  className="example-button"
                  onClick={() => setInputValue(example)}
                  disabled={loading}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>

      <footer className="App-footer">
        <p>Powered by Weather AI Agent</p>
      </footer>
    </div>
  );
}

export default App;
