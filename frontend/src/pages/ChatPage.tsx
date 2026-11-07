import React, { useRef, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Header } from '../components/common/Header';
import { useChatStore } from '../store/useChatStore';
import { ChatMessageItem } from '../components/chat/ChatMessageItem';
import { MessageComposer } from '../components/chat/MessageComposer';
import { Sparkles, ShieldCheck, Database, Globe } from 'lucide-react';

interface OutletContextType {
  onMobileMenuOpen: () => void;
}

export const ChatPage: React.FC = () => {
  const { onMobileMenuOpen } = useOutletContext<OutletContextType>();
  const { messages, sendMessage, isLoading } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const samplePrompts = [
    {
      title: 'Document Memory Systems',
      query: 'What is the difference between short-term memory and long-term memory in AI agents?',
      icon: ShieldCheck,
      route: 'Vector Docs',
    },
    {
      title: 'SQL Catalog Query',
      query: 'How many documents are uploaded in the system?',
      icon: Database,
      route: 'Structured SQL',
    },
    {
      title: 'Lexical vs Dense Trade-offs',
      query: 'What are the trade-offs of BM25 sparse retrieval vs dense embeddings?',
      icon: Sparkles,
      route: 'Hybrid BM25',
    },
    {
      title: 'External Web Knowledge',
      query: 'What are the latest 2026 features released in LangChain and LangGraph?',
      icon: Globe,
      route: 'Web Search',
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-background overflow-hidden">
      <Header
        title="AI Chat"
        subtitle="Adaptive multi-strategy retrieval with verified citations"
        onMobileMenuOpen={onMobileMenuOpen}
      />

      {/* Messages Scroll Region */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="py-12 text-center max-w-2xl mx-auto space-y-8 animate-fade-in">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-indigo-500/20 via-indigo-600/20 to-violet-700/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto shadow-glow-primary">
                <Sparkles className="w-8 h-8" />
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  VeriWeave Grounded Chat Engine
                </h2>
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                  Ask factual questions about reference documents, structured database metadata, or real-time external topics. Every response is verified with exact citations.
                </p>
              </div>

              {/* Sample Prompts Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
                {samplePrompts.map((sample) => {
                  const Icon = sample.icon;
                  return (
                    <button
                      key={sample.title}
                      onClick={() => sendMessage(sample.query)}
                      disabled={isLoading}
                      className="p-4 rounded-xl bg-surface-card border border-surface-border hover:border-indigo-500/50 hover:bg-surface-hover/70 transition-all text-left group shadow-sm flex flex-col justify-between"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors flex items-center gap-1.5">
                          <Icon className="w-3.5 h-3.5 text-indigo-400" />
                          {sample.title}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                          {sample.route}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2 italic font-mono">
                        "{sample.query}"
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {messages.map((message) => (
                <ChatMessageItem key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Message Composer */}
      <MessageComposer />
    </div>
  );
};
