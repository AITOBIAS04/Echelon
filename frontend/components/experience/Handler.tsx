"use client";

import { useState, useRef, useEffect } from "react";
import { Send, X, Minimize2, Maximize2 } from "lucide-react";
import { Handler, HandlerMessage, HandlerContext } from "@/lib/handlers/types";

interface HandlerProps {
  handler: Handler;
  context: HandlerContext;
  onSendMessage: (message: string) => Promise<string>;
  defaultExpanded?: boolean;
}

export default function Handler({
  handler,
  context,
  onSendMessage,
  defaultExpanded = false,
}: HandlerProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [messages, setMessages] = useState<HandlerMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  const handleSend = async () => {
    if (!inputValue.trim() || isThinking) return;

    const userMessage: HandlerMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsThinking(true);

    try {
      const response = await onSendMessage(userMessage.content);

      const handlerMessage: HandlerMessage = {
        id: `msg-${Date.now() + 1}`,
        role: "handler",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, handlerMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage: HandlerMessage = {
        id: `msg-${Date.now() + 1}`,
        role: "handler",
        content: "Error: Unable to process request. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isExpanded ? (
        // Collapsed state
        <button
          onClick={() => setIsExpanded(true)}
          className="flex items-center gap-3 px-4 py-3 bg-[#12121a]/90 backdrop-blur-md border border-slate-700/50 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
        >
          <div className="text-2xl">{handler.avatar}</div>
          <div className="flex flex-col items-start">
            <span className="text-sm font-mono text-slate-200">
              {handler.name}
            </span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-[#22c55e] rounded-full animate-pulse" />
              <span className="text-xs text-slate-400">Online</span>
            </div>
          </div>
        </button>
      ) : (
        // Expanded state
        <div className="w-96 h-[600px] bg-[#12121a]/95 backdrop-blur-md border border-slate-700/50 rounded-lg shadow-2xl flex flex-col transition-all duration-300">
          {/* Header */}
          <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-2xl">{handler.avatar}</div>
              <div>
                <div className="text-sm font-mono text-slate-200 font-semibold">
                  {handler.name}
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#22c55e] rounded-full animate-pulse" />
                  <span className="text-xs text-slate-400">Online</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className="p-1.5 hover:bg-slate-700/30 rounded transition-all duration-300"
            >
              <Minimize2 className="w-4 h-4 text-slate-400" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-slate-400 text-sm py-8">
                <div className="text-4xl mb-2">{handler.avatar}</div>
                <div className="font-mono">{handler.name}</div>
                <div className="text-xs mt-2 text-slate-500">
                  {handler.description}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 ${
                    message.role === "user"
                      ? "bg-[#6366f1] text-white"
                      : "bg-[#0a0a0f] border border-slate-700/50 text-slate-200"
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">
                    {message.content}
                  </div>
                  <div
                    className={`text-xs mt-1 ${
                      message.role === "user"
                        ? "text-blue-200"
                        : "text-slate-500"
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {isThinking && (
              <div className="flex justify-start">
                <div className="bg-[#0a0a0f] border border-slate-700/50 rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-[#6366f1] rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-[#6366f1] rounded-full animate-pulse delay-75" />
                    <div className="w-2 h-2 bg-[#6366f1] rounded-full animate-pulse delay-150" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="px-4 py-3 border-t border-slate-700/50">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask CONTROL..."
                disabled={isThinking}
                className="flex-1 px-3 py-2 bg-[#0a0a0f] border border-slate-700/50 rounded-lg text-slate-200 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#6366f1] disabled:opacity-50 transition-all duration-300"
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isThinking}
                className="px-4 py-2 bg-[#6366f1] hover:bg-[#6366f1]/80 disabled:bg-[#12121a] disabled:text-slate-500 text-white rounded-lg transition-all duration-300"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


