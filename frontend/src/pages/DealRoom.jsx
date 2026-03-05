import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Send, Paperclip, RefreshCw,
  Building2, Shield, Clock, FileText
} from "lucide-react";

function MessageBubble({ msg, isMe }) {
  const time = new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const date = new Date(msg.created_at).toLocaleDateString([], { month: "short", day: "numeric" });

  return (
    <div className={`flex gap-3 ${isMe ? "flex-row-reverse" : "flex-row"}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${
        msg.sender_role === "admin" ? "bg-[#C5A059]/20" : "bg-[#0A192F]/10"
      }`}>
        {msg.sender_role === "admin" ? (
          <Shield className="w-4 h-4 text-[#C5A059]" />
        ) : (
          <Building2 className="w-4 h-4 text-[#0A192F]" />
        )}
      </div>
      <div className={`max-w-[70%] ${isMe ? "items-end" : "items-start"} flex flex-col gap-1`}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-600">{msg.sender_name}</span>
          <span className="text-xs text-slate-400">{date} · {time}</span>
        </div>
        <div className={`px-4 py-3 rounded-sm text-sm leading-relaxed ${
          isMe
            ? "bg-[#0A192F] text-white"
            : "bg-white border border-slate-200 text-slate-700"
        }`}>
          {msg.content}
        </div>
        {msg.attachment_name && (
          <a
            href={msg.attachment_url || "#"}
            className="flex items-center gap-2 text-xs text-blue-600 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            <FileText className="w-3 h-3" />
            {msg.attachment_name}
          </a>
        )}
      </div>
    </div>
  );
}

export default function DealRoom() {
  const { dealId } = useParams();
  const { authAxios, user } = useAuth();
  const navigate = useNavigate();
  const bottomRef = useRef(null);

  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [content, setContent] = useState("");
  const [deal, setDeal] = useState(null);
  const [polling, setPolling] = useState(null);

  const fetchMessages = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await authAxios.get(`/deals/${dealId}/messages`);
      setMessages(res.data);
    } catch {
      if (!silent) toast.error("Failed to load messages");
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const fetchDeal = async () => {
    try {
      const res = await authAxios.get("/deals");
      const found = res.data.find(d => d.id === dealId);
      setDeal(found || null);
    } catch {}
  };

  useEffect(() => {
    fetchDeal();
    fetchMessages();
    // Poll every 8 seconds for new messages
    const interval = setInterval(() => fetchMessages(true), 8000);
    setPolling(interval);
    return () => clearInterval(interval);
  }, [dealId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = content.trim();
    if (!trimmed) return;
    setSending(true);
    try {
      await authAxios.post(`/deals/${dealId}/messages`, { content: trimmed });
      setContent("");
      await fetchMessages(true);
    } catch {
      toast.error("Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="font-display text-lg font-semibold text-[#0A192F]">
                Deal Room
                {deal && (
                  <span className="text-slate-400 font-normal text-base ml-2">
                    — {deal.opportunity_product}
                  </span>
                )}
              </h1>
              {deal && (
                <div className="flex items-center gap-3 mt-0.5">
                  <span className="text-xs text-slate-500">{deal.exporter_company}</span>
                  <Badge className="text-xs bg-emerald-100 text-emerald-700">{deal.stage}</Badge>
                </div>
              )}
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => fetchMessages(false)}>
            <RefreshCw className="w-3.5 h-3.5 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center h-full text-slate-400">
              Loading messages...
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                <Send className="w-5 h-5 text-slate-400" />
              </div>
              <p className="text-slate-500 font-medium">No messages yet</p>
              <p className="text-sm text-slate-400 mt-1">
                Start the conversation below. All messages are private to this deal.
              </p>
            </div>
          ) : (
            <>
              {/* Date grouping — simple sequential rendering */}
              {messages.map(msg => (
                <MessageBubble
                  key={msg.id}
                  msg={msg}
                  isMe={msg.sender_id === user?.id}
                />
              ))}
            </>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Compose area */}
        <div className="bg-white border-t border-slate-200 p-4 flex-shrink-0">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <Textarea
                placeholder="Type a message… (Ctrl+Enter to send)"
                value={content}
                onChange={e => setContent(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
                className="resize-none"
                data-testid="message-input"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Button
                variant="outline"
                size="sm"
                className="w-10 h-10 p-0"
                title="Attach file (coming soon)"
                disabled
              >
                <Paperclip className="w-4 h-4" />
              </Button>
              <Button
                onClick={handleSend}
                disabled={sending || !content.trim()}
                className="w-10 h-10 p-0 bg-[#0A192F] hover:bg-[#1E293B] text-white"
                title="Send (Ctrl+Enter)"
                data-testid="send-message-btn"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-1.5 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Messages auto-refresh every 8 seconds · Ctrl+Enter to send
          </p>
        </div>
      </main>
    </div>
  );
}
