import Link from "next/link";
import { Info } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { ApprovalTimeline } from "@/components/ui/ApprovalTimeline";
import type { ApprovalStepOut } from "@/lib/types";

export function ApprovalPreviewCard({ steps }: { steps: ApprovalStepOut[] }) {
  return (
    <Card>
      <div className="font-semibold text-[13.5px] mb-[4px]">Approval Routing</div>
      <div className="text-[11px] text-[#98a2b3] mb-[14px]">
        {steps.length > 0
          ? "This is the full chain that will apply once submitted — every stage, role, and named approver."
          : "Preview of who will approve this contract, before you submit."}
      </div>
      {steps.length > 0 ? (
        <ApprovalTimeline steps={steps} size="sm" />
      ) : (
        <div className="flex items-start gap-[8px] text-[12px] text-[#667085] leading-[1.5] bg-[#fafbfc] border border-[#f0f1f4] rounded-[7px] px-[10px] py-[9px]">
          <Info size={14} color="#98a2b3" strokeWidth={2} className="flex-none mt-[1px]" />
          <span>
            No approval flow is configured for this contract type yet — it will be approved in a single step.{" "}
            <Link href="/approval-flows" className="text-[#3a5bd9] font-semibold hover:underline">
              Configure one in Approval Flows
            </Link>
            .
          </span>
        </div>
      )}
    </Card>
  );
}
