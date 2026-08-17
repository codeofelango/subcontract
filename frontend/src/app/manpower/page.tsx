import { TriangleAlert } from "lucide-react";
import { getManpower } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { ManpowerActions } from "./ManpowerActions";

export const dynamic = "force-dynamic";

const CONTRACT_ID = "SC-2024-0155";
const PERIOD = "February 2026";

export default async function ManpowerPage() {
  const data = await getManpower(CONTRACT_ID, PERIOD);
  const { context, rows, total, varianceNote, matchedTotal } = data;

  return (
    <div className="flex flex-col gap-[18px] max-w-[1320px]">
      {/* Context bar */}
      <Card padding="16px 20px" className="flex items-center gap-[22px] flex-wrap">
        <div>
          <div className="text-[11px] text-[#98a2b3]">Contract</div>
          <div className="font-semibold text-[14px]">
            <span className="font-mono text-[#3a5bd9]">{context.contractId}</span> · {context.vendor}
          </div>
        </div>
        <div className="w-px h-[34px] bg-[#e6e8ec]" />
        <div>
          <div className="text-[11px] text-[#98a2b3]">Period</div>
          <div className="font-semibold text-[14px]">{context.period}</div>
        </div>
        <div className="w-px h-[34px] bg-[#e6e8ec]" />
        <div>
          <div className="text-[11px] text-[#98a2b3]">Source</div>
          <div className="font-semibold text-[14px]">{context.source}</div>
        </div>
        <div className="flex-1" />
        <div className="text-right">
          <div className="text-[11px] text-[#98a2b3]">Net Variance</div>
          <div className="font-bold text-[18px] font-mono" style={{ color: context.netVarianceColor }}>
            {context.netVariance}
          </div>
        </div>
      </Card>

      <div className="flex gap-[11px] text-[12.5px] text-[#667085] items-center">
        <span className="flex items-center gap-[6px]">
          <span className="w-[10px] h-[10px] rounded-[3px] bg-[#12805c]" />
          Matched to contract rate
        </span>
        <span className="flex items-center gap-[6px]">
          <span className="w-[10px] h-[10px] rounded-[3px] bg-[#b45309]" />
          Variance — review
        </span>
        <span className="ml-auto italic">Contract rates (incl. OT) are the baseline for all calculations</span>
      </div>

      {/* Reconciliation table */}
      <Card padding="0" className="overflow-hidden">
        <table className="w-full border-collapse text-[12.5px]">
          <thead>
            <tr className="text-[#667085] text-[10px] uppercase tracking-[.03em] bg-[#fafbfc]">
              <th className="px-[14px] py-[10px] font-semibold text-left">Job Title</th>
              <th className="px-[10px] py-[10px] font-semibold text-left border-l border-[#e6e8ec]">Nationality</th>
              <th className="px-[10px] py-[10px] font-semibold text-right">Employees</th>
              <th className="px-[10px] py-[10px] font-semibold text-right border-l border-[#e6e8ec]">Reg Hrs</th>
              <th className="px-[10px] py-[10px] font-semibold text-right">Rate</th>
              <th className="px-[10px] py-[10px] font-semibold text-right">OT Hrs</th>
              <th className="px-[10px] py-[10px] font-semibold text-right">OT Rate</th>
              <th className="px-[12px] py-[10px] font-semibold text-right bg-[#f2f6fc]">Contract Amount</th>
              <th className="px-[12px] py-[10px] font-semibold text-right border-l border-[#e6e8ec]">Invoiced</th>
              <th className="px-[12px] py-[10px] font-semibold text-right">Variance</th>
              <th className="px-[14px] py-[10px] font-semibold text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((m) => (
              <tr key={`${m.title}-${m.nationality}`} className="border-t border-[#f0f1f4]">
                <td className="px-[14px] py-[11px] font-semibold">{m.title}</td>
                <td className="px-[10px] py-[11px] border-l border-[#f0f1f4] text-[#475467]">{m.nationality}</td>
                <td className="px-[10px] py-[11px] text-right font-mono">{m.employeeCount}</td>
                <td className="px-[10px] py-[11px] text-right font-mono">{m.reg}</td>
                <td className="px-[10px] py-[11px] text-right font-mono text-[#667085]">{m.regRate}</td>
                <td className="px-[10px] py-[11px] text-right font-mono">{m.ot}</td>
                <td className="px-[10px] py-[11px] text-right font-mono text-[#667085]">{m.otRate}</td>
                <td className="px-[12px] py-[11px] text-right font-mono font-semibold bg-[#f8fafd]">{m.contract}</td>
                <td className="px-[12px] py-[11px] text-right font-mono border-l border-[#f0f1f4]">{m.invoiced}</td>
                <td className="px-[12px] py-[11px] text-right font-mono font-semibold" style={{ color: m.varColor }}>
                  {m.variance}
                </td>
                <td className="px-[14px] py-[11px] text-center">
                  <Pill color={m.color} bg={m.bg}>
                    {m.status}
                  </Pill>
                </td>
              </tr>
            ))}
            <tr className="border-t-2 border-[#e6e8ec] bg-[#fafbfc] font-bold">
              <td className="px-[14px] py-[12px]">Total</td>
              <td className="border-l border-[#e6e8ec]" />
              <td className="px-[10px] py-[12px] text-right font-mono">{total.employeeCount}</td>
              <td colSpan={4} />
              <td className="px-[12px] py-[12px] text-right font-mono bg-[#f2f6fc]">{total.contract}</td>
              <td className="px-[12px] py-[12px] text-right font-mono border-l border-[#e6e8ec]">{total.invoiced}</td>
              <td className="px-[12px] py-[12px] text-right font-mono text-[#c0362c]">{total.variance}</td>
              <td />
            </tr>
          </tbody>
        </table>
      </Card>

      <div className="flex gap-[12px] items-center">
        {varianceNote && (
          <div className="flex-1 bg-[#fbf1e3] border border-[#f0dcc0] rounded-[10px] px-[16px] py-[13px] text-[12.5px] text-[#7a4a12] flex gap-[10px] items-center">
            <TriangleAlert size={17} color="#b45309" strokeWidth={2} />
            <span>{varianceNote}</span>
          </div>
        )}
      </div>
      <ManpowerActions contractId={context.contractId} period={context.period} matchedTotal={matchedTotal} />
    </div>
  );
}
