import { FileText } from "lucide-react";
import { getPenalty } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { ApprovalTimeline } from "@/components/ui/ApprovalTimeline";
import { PenaltyAdvanceButton } from "./PenaltyActions";

export const dynamic = "force-dynamic";

const PENALTY_ID = "PN-2026-004";

export default async function PenaltyPage() {
  const data = await getPenalty(PENALTY_ID);
  const { fields, attachment, slaBreach, approvalSteps } = data;
  const hasCurrentStep = approvalSteps.some((s) => s.state === "current");

  return (
    <div className="grid grid-cols-[1fr_380px] gap-[22px] max-w-[1200px] items-start">
      <div className="flex flex-col gap-[18px]">
        {/* Penalty detail */}
        <Card padding="0" className="overflow-hidden">
          <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] flex items-center gap-[10px]">
            <span className="font-mono font-semibold text-[#3a5bd9]">{data.id}</span>
            <span className="font-semibold text-[14px]">{data.title}</span>
            <span className="ml-auto">
              <Pill color="#b45309" bg="#fbf1e3">
                {data.status}
              </Pill>
            </span>
          </div>
          <div className="p-[18px] grid grid-cols-2 gap-x-[22px] gap-y-[16px]">
            {fields.map((p) => (
              <div key={p.label}>
                <div className="text-[11.5px] text-[#667085] mb-[5px]">{p.label}</div>
                <div className="text-[14px]" style={{ fontWeight: p.weight, color: p.color }}>
                  {p.value}
                </div>
              </div>
            ))}
          </div>
          <div className="px-[18px] py-[14px] border-t border-[#e6e8ec] flex items-center gap-[9px] text-[12.5px] text-[#475467] bg-[#fafbfc]">
            <FileText size={16} color="#3a5bd9" strokeWidth={2} />
            <span className="font-semibold text-[#3a5bd9]">{attachment}</span>
            <span className="text-[#98a2b3]">· mandatory attachment provided</span>
          </div>
        </Card>

        {/* Linked SLA */}
        <Card>
          <div className="font-semibold text-[13.5px] mb-[12px]">Linked SLA Breach</div>
          <div className="flex gap-[14px] items-center px-[14px] py-[12px] bg-[#fbeceb] border border-[#f3d3d0] rounded-[8px]">
            <div className="text-[24px] font-bold font-mono text-[#c0362c]">{slaBreach.actualPct}</div>
            <div className="text-[12.5px] text-[#7a2b25]">
              <strong>{slaBreach.label}</strong> {slaBreach.detail}
            </div>
          </div>
        </Card>
      </div>

      {/* Approval chain */}
      <Card>
        <div className="font-semibold text-[14px] mb-[6px]">Approval Route</div>
        <div className="text-[12px] text-[#667085] mb-[18px]">Debited to supplier account only after CFO approval</div>
        <ApprovalTimeline steps={approvalSteps} />
        <PenaltyAdvanceButton penaltyId={data.id} hasCurrentStep={hasCurrentStep} />
      </Card>
    </div>
  );
}
