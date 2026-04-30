import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  Download,
  LogOut,
  MessageSquare,
  Moon,
  Search,
  Send,
  Sun,
  UserRound,
} from "lucide-react";
import { api, setAuthToken, WS_URL } from "./api/client";

function roomId(a, b) {
  return [String(a), String(b)].sort().join("_");
}

function looksLikeCode(text) {
  return /```|def |function |const |let |class |import |from /.test(text);
}

function extensionForLanguage(language) {
  const normalized = (language || "txt").toLowerCase();
  const extensions = {
    html: "html",
    css: "css",
    javascript: "js",
    js: "js",
    python: "py",
    py: "py",
    json: "json",
    text: "txt",
    txt: "txt",
  };
  return extensions[normalized] || "txt";
}

function parseDownloadableFiles(text) {
  const files = [];
  const fencePattern = /```([a-zA-Z0-9_-]+)?(?:\s+filename=["']?([^"'\n]+)["']?)?\n([\s\S]*?)```/g;
  let match;

  while ((match = fencePattern.exec(text)) !== null) {
    const language = match[1] || "txt";
    const extension = extensionForLanguage(language);
    const filename = (match[2] || `response-${files.length + 1}.${extension}`).trim();
    const content = match[3].trimEnd();

    if (content) {
      files.push({ filename, content });
    }
  }

  return files;
}

function downloadText(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [me, setMe] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ username: "", password: "" });
  const [authError, setAuthError] = useState("");
  const [query, setQuery] = useState("");
  const [users, setUsers] = useState([]);
  const [activeUser, setActiveUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState("");
  const [chatStatus, setChatStatus] = useState("");
  const [aiEvents, setAiEvents] = useState([]);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiStatus, setAiStatus] = useState("");
  const [dark, setDark] = useState(localStorage.getItem("theme") === "dark");
  const chatSocket = useRef(null);
  const aiSocket = useRef(null);
  const messageEndRef = useRef(null);
  const aiEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  const currentRoomId = useMemo(() => {
    if (!me || !activeUser) return "";
    return roomId(me.id, activeUser.id);
  }, [me, activeUser]);

  useEffect(() => {
    setAuthToken(token);
    if (!token) return;
    api
      .get("/auth/me")
      .then((res) => setMe(res.data))
      .catch(() => handleLogout());
  }, [token]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    if (!token || !me) return;
    const delay = setTimeout(() => {
      api.get(`/users/search?query=${encodeURIComponent(query)}`).then((res) => setUsers(res.data));
    }, 160);
    return () => clearTimeout(delay);
  }, [query, token, me]);

  useEffect(() => {
    if (!token || !activeUser) return;
    api.get(`/messages/${activeUser.id}`).then((res) => setMessages(res.data));

    chatSocket.current?.close();
    const ws = new WebSocket(`${WS_URL}/ws/chat/${activeUser.id}?token=${encodeURIComponent(token)}`);
    chatSocket.current = ws;
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "chat_message") {
        setMessages((existing) => [...existing, data]);
      }
      if (data.type === "ai_prompt") {
        setAiPrompt(data.prompt);
      }
      if (data.type === "typing") {
        if (Number(data.user_id) !== Number(me?.id)) {
          setChatStatus(data.is_typing ? `${data.username} is typing...` : "");
        }
      }
    };
    return () => {
      clearTimeout(typingTimeoutRef.current);
      ws.close();
    };
  }, [activeUser, token, me?.id]);

  useEffect(() => {
    if (!token || !currentRoomId) return;
    aiSocket.current?.close();
    const ws = new WebSocket(`${WS_URL}/ws/ai/${currentRoomId}?token=${encodeURIComponent(token)}`);
    aiSocket.current = ws;
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "ai_typing") {
        setAiStatus(data.is_typing ? data.message : "");
      }
      if (data.type === "ai_response") {
        setAiEvents((existing) => [...existing, data]);
      }
      if (data.type === "ai_busy") {
        setAiStatus(data.message);
      }
    };
    return () => ws.close();
  }, [currentRoomId, token]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    aiEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [aiEvents]);

  async function submitAuth(event) {
    event.preventDefault();
    setAuthError("");
    try {
      if (authMode === "register") {
        await api.post("/auth/register", authForm);
      }
      const res = await api.post("/auth/login", authForm);
      localStorage.setItem("token", res.data.access_token);
      setToken(res.data.access_token);
      setAuthForm({ username: "", password: "" });
    } catch (error) {
      if (error.response?.data?.detail) {
        setAuthError(error.response.data.detail);
      } else if (error.request) {
        setAuthError("Backend not reachable. Start FastAPI on http://127.0.0.1:8000.");
      } else {
        setAuthError("Authentication failed. Please try again.");
      }
    }
  }

  function handleLogout() {
    localStorage.removeItem("token");
    setAuthToken("");
    setToken("");
    setMe(null);
    setActiveUser(null);
    setMessages([]);
    setAiEvents([]);
  }

  function sendMessage(event) {
    event.preventDefault();
    const text = messageText.trim();
    if (!text || chatSocket.current?.readyState !== WebSocket.OPEN) return;

    sendTyping(false);
    chatSocket.current.send(JSON.stringify({ type: "chat_message", message: text }));
    if (text.toLowerCase().startsWith("@ai")) {
      setAiPrompt(text.slice(3).trim());
    }
    setMessageText("");
  }

  function sendTyping(isTyping) {
    if (chatSocket.current?.readyState !== WebSocket.OPEN) return;
    chatSocket.current.send(JSON.stringify({ type: "typing", is_typing: isTyping }));
  }

  function handleMessageTextChange(event) {
    setMessageText(event.target.value);
    sendTyping(true);
    clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => sendTyping(false), 1200);
  }

  function sendAiPrompt(event) {
    event.preventDefault();
    const prompt = aiPrompt.trim();
    if (!prompt || aiSocket.current?.readyState !== WebSocket.OPEN) return;
    aiSocket.current.send(JSON.stringify({ type: "ai_query", prompt }));
    setAiPrompt("");
  }

  if (!token || !me) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <div>
            <p className="eyebrow">CollabChat AI</p>
            <h1>Real-time chat with a shared AI workspace</h1>
          </div>
          <form onSubmit={submitAuth} className="auth-form">
            <label>
              Username
              <input
                value={authForm.username}
                onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })}
                minLength={3}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={authForm.password}
                onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })}
                minLength={6}
                required
              />
            </label>
            {authError && <p className="error">{authError}</p>}
            <button type="submit">{authMode === "login" ? "Log in" : "Create account"}</button>
          </form>
          <button className="text-button" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>
            {authMode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <header className="brand-row">
          <div>
            <p className="eyebrow">Hi, {me.username}</p>
            <h1>CollabChat AI</h1>
          </div>
          <button className="icon-button" onClick={() => setDark(!dark)} title="Toggle theme">
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>

        <label className="search-box">
          <Search size={18} />
          <input placeholder="Search users" value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>

        <div className="user-list">
          {users.map((user) => (
            <button
              key={user.id}
              className={`user-row ${activeUser?.id === user.id ? "active" : ""}`}
              onClick={() => setActiveUser(user)}
            >
              <span className="avatar">
                <UserRound size={17} />
              </span>
              <span>{user.username}</span>
            </button>
          ))}
          {!users.length && <p className="empty">Search for someone to start chatting.</p>}
        </div>

        <button className="logout-button" onClick={handleLogout}>
          <LogOut size={18} />
          Logout / switch account
        </button>
      </aside>

      <section className="chat-panel">
        {activeUser ? (
          <>
            <header className="panel-header">
              <div className="avatar">
                <MessageSquare size={18} />
              </div>
              <div>
                <h2>{activeUser.username}</h2>
                <p>{chatStatus || aiStatus || "Messages sync instantly"}</p>
              </div>
            </header>

            <div className="message-list">
              {messages.map((message, index) => {
                const mine = Number(message.sender_id || message.user_id) === Number(me.id);
                return (
                  <div key={`${message.id || index}-${message.timestamp || index}`} className={`bubble ${mine ? "mine" : ""}`}>
                    <p>{message.content || message.message}</p>
                    <span>
                      {message.timestamp
                        ? new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                        : "now"}
                    </span>
                  </div>
                );
              })}
              <div ref={messageEndRef} />
            </div>

            <form className="composer" onSubmit={sendMessage}>
              <input
                placeholder="Message or @ai ask something"
                value={messageText}
                onChange={handleMessageTextChange}
              />
              <button className="icon-button primary" type="submit" title="Send message">
                <Send size={18} />
              </button>
            </form>
          </>
        ) : (
          <div className="blank-state">
            <MessageSquare size={42} />
            <h2>Select a user to start chatting</h2>
          </div>
        )}
      </section>

      <aside className="ai-panel">
        <header className="panel-header">
          <div className="avatar ai">
            <Bot size={18} />
          </div>
          <div>
            <h2>Shared AI</h2>
            <p>{currentRoomId ? `Room ${currentRoomId}` : "Open a chat first"}</p>
          </div>
        </header>

        <div className="ai-feed">
          {aiEvents.map((event, index) => {
            const downloadableFiles = parseDownloadableFiles(event.response);

            return (
              <article className="ai-response" key={`${event.timestamp}-${index}`}>
                <p className="prompt">@ai {event.prompt}</p>
                <pre>{event.response}</pre>
                {downloadableFiles.length > 0 ? (
                  <div className="download-list">
                    {downloadableFiles.map((file) => (
                      <button
                        key={file.filename}
                        className="download-button"
                        onClick={() => downloadText(file.filename, file.content)}
                      >
                        <Download size={16} />
                        {file.filename}
                      </button>
                    ))}
                  </div>
                ) : (
                  looksLikeCode(event.response) && (
                    <button
                      className="download-button"
                      onClick={() => downloadText("collabchat-ai-response.txt", event.response)}
                    >
                      <Download size={16} />
                      response.txt
                    </button>
                  )
                )}
              </article>
            );
          })}
          {!aiEvents.length && <p className="empty">Type `@ai` in chat or ask here once a chat is open.</p>}
          <div ref={aiEndRef} />
        </div>

        <form className="ai-composer" onSubmit={sendAiPrompt}>
          <textarea
            placeholder="Ask AI together"
            value={aiPrompt}
            onChange={(event) => setAiPrompt(event.target.value)}
            disabled={!currentRoomId}
          />
          <button disabled={!currentRoomId} type="submit">
            <Bot size={18} />
            Ask AI
          </button>
        </form>
      </aside>
    </main>
  );
}
