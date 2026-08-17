import { getDashboard } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { ProgressBar } from "@/components/ui/ProgressBar";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const data = await getDashboard();

  return (
    <div className="flex flex-col gap-[20px] max-w-[1280px]">
      {/* KPI ROW */}
      <div className="grid grid-cols-6 gap-[14px]">
        {data.kpis.map((k) => (
          <Card key={k.label} padding="16px 16px 15px">
            <div className="text-[11.5px] text-[#667085] font-medium mb-[9px]">{k.label}</div>
            <div className="text-[22px] font-bold tracking-[-0.02em] font-mono">{k.value}</div>
            <div className="text-[11px] font-semibold mt-[6px]" style={{ color: k.deltaColor }}>
              {k.delta}
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-[1.55fr_1fr] gap-[20px]">
        {/* ALERTS */}
        <Card padding="0" className="overflow-hidden">
          <div className="px-[18px] py-[15px] border-b border-[#e6e8ec] flex items-center justify-between">
            <div className="font-semibold text-[14px]">Alerts &amp; Attention</div>
            <span className="text-[11px] text-[#98a2b3] font-medium">Auto-generated</span>
          </div>
          <div>
            {data.alerts.length === 0 && <div className="px-[18px] py-[20px] text-[13px] text-[#667085]">No alerts right now.</div>}
            {data.alerts.map((a, i) => (
              <div key={i} className="flex gap-[13px] px-[18px] py-[13px] border-b border-[#f0f1f4] items-start">
                <div className="w-[8px] h-[8px] rounded-full mt-[5px] flex-none" style={{ background: a.color }} />
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-semibold">{a.title}</div>
                  <div className="text-[12px] text-[#667085] mt-[1px]">{a.detail}</div>
                </div>
                <Pill color={a.color} bg={a.bg}>
                  {a.tag}
                </Pill>
              </div>
            ))}
          </div>
        </Card>

        {/* SERVICE MIX */}
        <Card>
          <div className="font-semibold text-[14px] mb-[4px]">Committed Value by Service Type</div>
          <div className="text-[12px] text-[#667085] mb-[16px]">Share of portfolio value</div>
          <div className="flex flex-col gap-[14px]">
            {data.serviceMix.map((s) => (
              <div key={s.label}>
                <div className="flex justify-between text-[12.5px] mb-[5px]">
                  <span className="font-medium">{s.label}</span>
                  <span className="font-mono text-[#475467]">
                    {s.amount} · {s.pct}
                  </span>
                </div>
                <ProgressBar width={s.width} color={s.color} />
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* PENDING ACTIONS */}
      <Card padding="0" className="overflow-hidden">
        <div className="px-[18px] py-[15px] border-b border-[#e6e8ec] font-semibold text-[14px]">Pending My Action</div>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-left text-[#667085] text-[11px] uppercase tracking-[.05em]">
              <th className="px-[18px] py-[10px] font-semibold">Reference</th>
              <th className="px-[18px] py-[10px] font-semibold">Item</th>
              <th className="px-[18px] py-[10px] font-semibold">Vendor</th>
              <th className="px-[18px] py-[10px] font-semibold">Stage</th>
              <th className="px-[18px] py-[10px] font-semibold text-right">Amount</th>
              <th className="px-[18px] py-[10px] font-semibold">Waiting</th>
            </tr>
          </thead>
          <tbody>
            {data.pendingActions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-[18px] py-[20px] text-[13px] text-[#667085]">
                  Nothing pending your action right now.
                </td>
              </tr>
            )}
            {data.pendingActions.map((p, i) => (
              <tr key={i} className="border-t border-[#f0f1f4]">
                <td className="px-[18px] py-[12px] font-mono font-medium text-[#3a5bd9]">{p.ref}</td>
                <td className="px-[18px] py-[12px]">{p.item}</td>
                <td className="px-[18px] py-[12px] text-[#475467]">{p.vendor}</td>
                <td className="px-[18px] py-[12px] text-[#475467]">{p.stage}</td>
                <td className="px-[18px] py-[12px] text-right font-mono">{p.amount}</td>
                <td className="px-[18px] py-[12px]">
                  <Pill color={p.color} bg={p.bg}>
                    {p.age}
                  </Pill>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* VENDORS */}
      <Card padding="0" className="overflow-hidden">
        <div className="px-[18px] py-[15px] border-b border-[#e6e8ec] flex items-center justify-between">
          <div className="font-semibold text-[14px]">Vendor Overview</div>
          <span className="text-[11px] text-[#98a2b3] font-medium">By portfolio value</span>
        </div>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-left text-[#667085] text-[11px] uppercase tracking-[.05em]">
              <th className="px-[18px] py-[10px] font-semibold">Vendor</th>
              <th className="px-[18px] py-[10px] font-semibold">Contractor No.</th>
              <th className="px-[18px] py-[10px] font-semibold text-right">Contracts</th>
              <th className="px-[18px] py-[10px] font-semibold text-right">Total Value</th>
              <th className="px-[18px] py-[10px] font-semibold">Avg Progress</th>
              <th className="px-[18px] py-[10px] font-semibold">Rating</th>
            </tr>
          </thead>
          <tbody>
            {data.vendors.map((v) => (
              <tr key={v.vendor} className="border-t border-[#f0f1f4]">
                <td className="px-[18px] py-[12px] font-medium">{v.vendor}</td>
                <td className="px-[18px] py-[12px] font-mono text-[#475467]">{v.contractorNo}</td>
                <td className="px-[18px] py-[12px] text-right font-mono">
                  {v.activeCount} active / {v.contractsCount} total
                </td>
                <td className="px-[18px] py-[12px] text-right font-mono font-semibold">{v.totalValue}</td>
                <td className="px-[18px] py-[12px]">
                  <div className="flex items-center gap-[8px]">
                    <div className="w-[70px]">
                      <ProgressBar width={v.avgProgress} color={v.progressColor} height={6} />
                    </div>
                    <span className="font-mono text-[12px] text-[#475467]">{v.avgProgress}</span>
                  </div>
                </td>
                <td className="px-[18px] py-[12px]">
                  <Pill color={v.ratingColor} bg={v.ratingBg}>
                    {v.rating}
                  </Pill>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
