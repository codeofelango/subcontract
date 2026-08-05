"use client";

import { useEffect, useState } from "react";
import { getEvaluation } from "@/lib/api";
import type { EvaluationResponse } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";

export function EvaluationsClient({ initial }: { initial: EvaluationResponse }) {
  const [tab, setTab] = useState(initial.activeTab);
  const [data, setData] = useState(initial);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (tab === initial.activeTab) {
      setData(initial);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getEvaluation(tab).then((d) => {
      if (!cancelled) {
        setData(d);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  return (
    <div className="flex flex-col gap-[18px] max-w-[1280px]">
      {/* Tabs */}
      <div className="flex gap-[4px] bg-[#eef0f3] rounded-[9px] p-[4px] w-fit">
        {data.tabs.map((t) => {
          const active = t.id === tab;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className="rounded-[7px] px-[16px] py-[8px] text-[13px] font-semibold"
              style={{
                background: active ? "#fff" : "transparent",
                color: active ? "#3a5bd9" : "#667085",
                boxShadow: active ? "0 1px 2px rgba(0,0,0,.08)" : "none",
              }}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-[1fr_300px] gap-[20px] items-start" style={{ opacity: loading ? 0.6 : 1 }}>
        {/* Scorecard */}
        <div className="flex flex-col gap-[16px]">
          <Card className="flex gap-[26px] flex-wrap" padding="16px 18px">
            {data.meta.map((m) => (
              <div key={m.k}>
                <div className="text-[11px] text-[#98a2b3]">{m.k}</div>
                <div className="font-semibold text-[13.5px] mt-[2px]">{m.v}</div>
              </div>
            ))}
          </Card>

          <Card padding="0" className="overflow-hidden">
            <table className="w-full border-collapse text-[12.5px]">
              <thead>
                <tr className="text-left text-[#667085] text-[10px] uppercase tracking-[.03em] bg-[#fafbfc]">
                  <th className="px-[14px] py-[10px] font-semibold">Category</th>
                  <th className="px-[14px] py-[10px] font-semibold">KPI</th>
                  <th className="px-[10px] py-[10px] font-semibold text-center">SLA Target</th>
                  <th className="px-[10px] py-[10px] font-semibold text-right">Weight</th>
                  <th className="px-[10px] py-[10px] font-semibold text-right">Actual</th>
                  <th className="px-[10px] py-[10px] font-semibold text-right">Score</th>
                  <th className="px-[14px] py-[10px] font-semibold text-right">Weighted</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r, i) => (
                  <tr key={i} className="border-t border-[#f0f1f4]">
                    <td className="px-[14px] py-[9px]" style={{ color: "#101828", fontWeight: r.catWeight }}>
                      {r.cat}
                    </td>
                    <td className="px-[14px] py-[9px] text-[#344054]">{r.kpi}</td>
                    <td className="px-[10px] py-[9px] text-center font-mono text-[#667085]">{r.target}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono text-[#667085]">{r.weight}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono">{r.actual}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono font-semibold" style={{ color: r.scoreColor }}>
                      {r.score}
                    </td>
                    <td className="px-[14px] py-[9px] text-right font-mono">{r.weighted}</td>
                  </tr>
                ))}
                <tr className="border-t-2 border-[#e6e8ec] bg-[#fafbfc] font-bold">
                  <td colSpan={3} className="px-[14px] py-[12px]">
                    Total Weighted Score
                  </td>
                  <td className="px-[10px] py-[12px] text-right font-mono">100</td>
                  <td />
                  <td />
                  <td className="px-[14px] py-[12px] text-right font-mono text-[14px]">{data.total}</td>
                </tr>
              </tbody>
            </table>
          </Card>
        </div>

        {/* Rating rail */}
        <div className="flex flex-col gap-[16px] sticky top-[90px]">
          <Card padding="20px" className="text-center">
            <div className="text-[12px] text-[#667085] mb-[10px]">Overall Score</div>
            <div className="text-[44px] font-bold font-mono leading-none" style={{ color: data.rating.color }}>
              {data.total}
            </div>
            <div
              className="inline-block mt-[12px] text-[12.5px] font-semibold px-[14px] py-[5px] rounded-[20px]"
              style={{ color: data.rating.color, background: data.rating.bg }}
            >
              {data.rating.label}
            </div>
            <div className="mt-[16px] flex flex-col gap-[9px] text-left">
              {data.cats.map((c) => (
                <div key={c.label}>
                  <div className="flex justify-between text-[11.5px] mb-[4px]">
                    <span className="text-[#475467]">{c.label}</span>
                    <span className="font-mono text-[#667085]">{c.val}</span>
                  </div>
                  <ProgressBar width={c.width} color={c.color} height={6} />
                </div>
              ))}
            </div>
          </Card>
          <Card padding="16px">
            <div className="font-semibold text-[12.5px] mb-[10px]">Penalty / Incentive</div>
            {data.adj.map((a) => (
              <div key={a.k} className="flex justify-between py-[5px] text-[12.5px]">
                <span className="text-[#667085]">{a.k}</span>
                <span className="font-mono" style={{ fontWeight: a.w, color: a.c }}>
                  {a.v}
                </span>
              </div>
            ))}
          </Card>
          <Card padding="14px 16px" className="bg-[#fafbfc]">
            <div className="font-semibold text-[11.5px] text-[#667085] mb-[8px] uppercase tracking-[.04em]">Rating Guide</div>
            {data.ratingGuide.map((g) => (
              <div key={g.label} className="flex items-center gap-[8px] py-[3px] text-[12px]">
                <span className="w-[9px] h-[9px] rounded-[2px]" style={{ background: g.color }} />
                <span className="font-mono text-[#667085] w-[64px]">{g.range}</span>
                <span className="text-[#475467]">{g.label}</span>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
