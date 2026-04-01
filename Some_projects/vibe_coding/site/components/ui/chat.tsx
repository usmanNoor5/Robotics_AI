"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "ai/react";
import { MessageCircle, X, Send, Bot, User } from "lucide-react";
import { Button } from "./button";

export function Chat() {
  const [isOpen, setIsOpen] = useState(false);
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end sm:bottom-6 sm:right-6">
      {isOpen && (
        <div className="mb-4 flex h-[500px] w-[350px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border border-white/10 bg-card shadow-glow sm:w-[400px]">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/10 bg-card2 p-4">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-accent" />
              <h3 className="font-medium text-fg">Digital Twin</h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-md p-1.5 text-fg/60 transition-colors hover:bg-white/5 hover:text-fg"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center text-fg/60">
                <Bot className="mb-2 h-8 w-8 text-accent/50" />
                <p className="text-sm">Hi! I&apos;m Usman&apos;s digital twin.</p>
                <p className="mt-1 text-xs">Ask me anything about his career!</p>
              </div>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex items-start gap-2 ${
                    m.role === "user" ? "flex-row-reverse" : ""
                  }`}
                >
                  <div
                    className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${
                      m.role === "user"
                        ? "bg-accent text-bg"
                        : "border border-white/10 bg-card2 text-accent"
                    }`}
                  >
                    {m.role === "user" ? (
                      <User className="h-3 w-3" />
                    ) : (
                      <Bot className="h-3 w-3" />
                    )}
                  </div>
                  <div
                    className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                      m.role === "user"
                        ? "rounded-tr-none bg-accent text-bg"
                        : "rounded-tl-none border border-white/10 bg-white/5 text-fg"
                    }`}
                  >
                    {m.content}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex items-start gap-2">
                <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-white/10 bg-card2 text-accent">
                  <Bot className="h-3 w-3" />
                </div>
                <div className="rounded-2xl rounded-tl-none border border-white/10 bg-white/5 px-3 py-2 text-sm text-fg/60">
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-white/10 bg-card2 p-4">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                value={input}
                onChange={handleInputChange}
                placeholder="Ask a question..."
                className="flex-1 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-fg placeholder:text-fg/40 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
              />
              <Button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="flex h-10 w-10 shrink-0 items-center justify-center gap-0 rounded-full p-0"
              >
                <Send className="h-4 w-4" />
                <span className="sr-only">Send</span>
              </Button>
            </form>
          </div>
        </div>
      )}

      {/* FAB Toggle */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-accent text-bg shadow-glow transition-all hover:scale-105 active:scale-95"
        >
          <MessageCircle className="h-6 w-6" />
          <span className="sr-only">Open Chat</span>
        </button>
      )}
    </div>
  );
}
