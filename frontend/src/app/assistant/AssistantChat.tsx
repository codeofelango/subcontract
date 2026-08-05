"use client";

import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { askActivity } from "@/lib/api";
import type { ActivityEntry } from "@/lib/types";

const ACTION_COLORS: Record<string, [string, string]> = {
  created: ["#2c7fb0", "#e7f1f8"],
  approved: ["#12805c", "#e6f4ee"],
  certified: ["#12805c", "#e6f4ee"],
  step_advanced: ["#3a5bd9", "#eef1fd"],
  raised: ["#b45309", "#fbf1e3"],
  approved_matched: ["#12805c", "#e6f4ee"],
  dispute_raised: ["#c0362c", "#fbeceb"],
};

function ActivityCard({ entry }: { entry: ActivityEntry }) {
  const [color, bg] = ACTION_COLORS[entry.action] ?? ["#667085", "#f0f1f4"];
  return (
    <div className="border border-[#e6e8ec] rounded-[8px] px-[12px] py-[10px] bg-white">
      <div className="flex items-center gap-[8px] mb-[5px] flex-wrap">
        <span className="text-[10.5px] font-semibold px-[8px] py-[2px] rounded-[6px]" style={{ color, background: bg }}>
          {entry.entityType} · {entry.action.replace(/_/g, " ")}
        </span>
        {entry.contractId && <span className="font-mono text-[11px] text-[#3a5bd9]">{entry.contractId}</span>}
        <span className="text-[11px] text-[#98a2b3] ml-auto">{entry.createdAt}</span>
      </div>
      <div className="text-[13px] text-[#101828] leading-[1.4]">{entry.summary}</div>
    </div>
  );
}

interface ChatTurn {
  question: string;
  answer: string;
  matches: ActivityEntry[];
}

export function AssistantChat({ initialActivity }: { initialActivity: ActivityEntry[] }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);

  async function ask() {
    const q = question.trim();
    if (!q || asking) return;
    setAsking(true);
    setQuestion("");
    try {
      const res = await askActivity(q);
      setTurns((t) => [...t, { question: q, answer: res.answer, matches: res.matches }]);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex flex-col gap-[18px] max-w-[900px]">
      <div className="flex flex-col gap-[16px]">
        {turns.length === 0 && (
          <div className="flex flex-col gap-[10px]">
            <div className="flex items-center gap-[8px] text-[12.5px] font-semibold text-[#667085]">
              <Sparkles size={15} color="#3a5bd9" strokeWidth={2} />
              Recent activity across all contracts
            </div>
            <div className="flex flex-col gap-[8px]">
              {initialActivity.map((e) => (
                <ActivityCard key={e.id} entry={e} />
              ))}
            </div>
          </div>
        )}

        {turns.map((turn, i) => (
          <div key={i} className="flex flex-col gap-[10px]">
            <div className="self-end max-w-[80%] bg-[#3a5bd9] text-white rounded-[10px] px-[14px] py-[9px] text-[13.5px]">
              {turn.question}
            </div>
            <div className="flex flex-col gap-[8px]">
              <div className="text-[12.5px] text-[#667085]">{turn.answer}</div>
              {turn.matches.map((e) => (
                <ActivityCard key={e.id} entry={e} />
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="sticky bottom-[20px] bg-white border border-[#e6e8ec] rounded-[10px] p-[10px] flex items-center gap-[10px] shadow-[0_2px_10px_rgba(16,24,40,.06)]">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              ask();
            }
          }}
          placeholder="Ask about a contract, vendor, IPC, change order, or penalty…"
          className="flex-1 text-[13.5px] px-[8px] py-[6px] focus:outline-none"
        />
        <button
          type="button"
          onClick={ask}
          disabled={asking || !question.trim()}
          className="flex items-center gap-[7px] bg-[#3a5bd9] text-white rounded-[8px] px-[14px] py-[9px] text-[13px] font-semibold hover:brightness-[1.08] disabled:opacity-50"
        >
          <Send size={14} strokeWidth={2.2} />
          {asking ? "Asking…" : "Ask"}
        </button>
      </div>
    </div>
  );
}
