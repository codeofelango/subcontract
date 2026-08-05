import { getChangeOrders } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { ApprovalTimeline } from "@/components/ui/ApprovalTimeline";
import { ChangeOrderAdvanceButton } from "./ChangeOrderActions";

export const dynamic = "force-dynamic";

const CONTRACT_ID = "SC-2024-0142";

export default async function ChangeOrdersPage() {
  const data = await getChangeOrders(CONTRACT_ID);
  const { context, affectedLineItems, history, valueRows, approvalSteps } = data;
  const hasCurrentStep = approvalSteps.some((s) => s.state === "current");

  return (
    <div className="grid grid-cols-[1fr_330px] gap-[22px] max-w-[1280px] items-start">
      <div className="flex flex-col gap-[18px]">
        {/* CO context */}
        <Card padding="16px 20px" className="flex items-center gap-[20px] flex-wrap">
          <div>
            <div className="flex items-center gap-[10px]">
              <span className="font-mono font-semibold text-[#3a5bd9]">{context.id}</span>
              <Pill color="#b45309" bg="#fbf1e3">
                {context.status}
              </Pill>
            </div>
            <div className="text-[15px] font-semibold mt-[3px]">{context.title}</div>
            <div className="text-[12.5px] text-[#667085]">
              Contract <span className="font-mono text-[#3a5bd9]">{context.contractId}</span> · {context.vendor} · PO{" "}
              <span className="font-mono">{context.po}</span>
            </div>
          </div>
          <div className="flex-1" />
          <button type="button" className="bg-[#3a5bd9] rounded-[8px] px-[15px] py-[10px] text-[13px] font-semibold text-white">
            + New Change Order
          </button>
        </Card>

        {/* Affected line items */}
        <Card padding="0" className="overflow-hidden">
          <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] flex items-center gap-[10px]">
            <span className="font-semibold text-[14px]">Affected Line Items</span>
            <span className="text-[11px] text-[#98a2b3]">Unit rates locked to contract baseline</span>
          </div>
          <table className="w-full border-collapse text-[12.5px]">
            <thead>
              <tr className="text-left text-[#667085] text-[10px] uppercase tracking-[.03em] bg-[#fafbfc]">
                <th className="px-[14px] py-[10px] font-semibold">Code</th>
                <th className="px-[14px] py-[10px] font-semibold">Description</th>
                <th className="px-[12px] py-[10px] font-semibold text-right">Original Qty</th>
                <th className="px-[12px] py-[10px] font-semibold text-right">Revised Qty</th>
                <th className="px-[12px] py-[10px] font-semibold text-right">Δ Qty</th>
                <th className="px-[12px] py-[10px] font-semibold text-right">Contract Rate</th>
                <th className="px-[14px] py-[10px] font-semibold text-right">Value Impact</th>
              </tr>
            </thead>
            <tbody>
              {affectedLineItems.map((c) => (
                <tr key={c.code} className="border-t border-[#f0f1f4]">
                  <td className="px-[14px] py-[11px] font-mono text-[#475467]">{c.code}</td>
                  <td className="px-[14px] py-[11px]">{c.desc}</td>
                  <td className="px-[12px] py-[11px] text-right font-mono text-[#667085]">{c.orig}</td>
                  <td className="px-[12px] py-[11px] text-right font-mono font-semibold">{c.rev}</td>
                  <td className="px-[12px] py-[11px] text-right font-mono font-semibold" style={{ color: c.deltaColor }}>
                    {c.delta}
                  </td>
                  <td className="px-[12px] py-[11px] text-right font-mono text-[#667085]">{c.rate}</td>
                  <td className="px-[14px] py-[11px] text-right font-mono font-semibold" style={{ color: c.impactColor }}>
                    {c.impact}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* CO History */}
        <Card padding="0" className="overflow-hidden">
          <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] font-semibold text-[14px]">Change Order History — {context.contractId}</div>
          <table className="w-full border-collapse text-[12.5px]">
            <thead>
              <tr className="text-left text-[#667085] text-[10px] uppercase tracking-[.03em] bg-[#fafbfc]">
                <th className="px-[14px] py-[10px] font-semibold">CO #</th>
                <th className="px-[14px] py-[10px] font-semibold">Reason</th>
                <th className="px-[14px] py-[10px] font-semibold text-right">Impact</th>
                <th className="px-[14px] py-[10px] font-semibold">PO Revision</th>
                <th className="px-[14px] py-[10px] font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id} className="border-t border-[#f0f1f4]">
                  <td className="px-[14px] py-[11px] font-mono font-semibold text-[#3a5bd9]">{h.id}</td>
                  <td className="px-[14px] py-[11px] text-[#344054]">{h.reason}</td>
                  <td className="px-[14px] py-[11px] text-right font-mono font-semibold" style={{ color: h.impactColor }}>
                    {h.impact}
                  </td>
                  <td className="px-[14px] py-[11px] text-[#667085] font-mono text-[11.5px]">{h.po}</td>
                  <td className="px-[14px] py-[11px]">
                    <Pill color={h.color} bg={h.bg}>
                      {h.status}
                    </Pill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      {/* CO rail */}
      <div className="flex flex-col gap-[16px] sticky top-[90px]">
        <Card>
          <div className="font-semibold text-[14px] mb-[14px]">Revised Contract Value</div>
          {valueRows.map((r) => (
            <div key={r.k} className="flex justify-between py-[8px] border-b border-[#f4f5f7] text-[13px]">
              <span className="text-[#667085]">{r.k}</span>
              <span className="font-mono" style={{ fontWeight: r.w, color: r.c }}>
                {r.v}
              </span>
            </div>
          ))}
        </Card>
        <Card>
          <div className="font-semibold text-[14px] mb-[4px]">Approval &amp; PO Revision</div>
          <div className="text-[12px] text-[#667085] mb-[16px]">Approved CO revises the Oracle PO</div>
          <ApprovalTimeline steps={approvalSteps} size="sm" />
          <ChangeOrderAdvanceButton coId={context.id} hasCurrentStep={hasCurrentStep} />
        </Card>
      </div>
    </div>
  );
}
