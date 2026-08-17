import { Card } from "@/components/ui/Card";
import type { ApprovalStepOut } from "@/lib/types";
import { ContractApprovalPanel } from "./ContractApprovalActions";

export function ContractApprovalCard({
  contractId,
  steps,
  workflowName,
}: {
  contractId: string;
  steps: ApprovalStepOut[];
  workflowName?: string | null;
}) {
  if (steps.length === 0) return null;

  return (
    <Card>
      <div className="flex items-center justify-between mb-[14px]">
        <div className="font-semibold text-[13.5px]">Approval Routing</div>
        {workflowName && (
          <span className="text-[10.5px] font-semibold px-[9px] py-[3px] rounded-[6px] text-[#7a5bd9] bg-[#f0ecfb]">
            {workflowName}
          </span>
        )}
      </div>
      <ContractApprovalPanel contractId={contractId} steps={steps} size="sm" />
    </Card>
  );
}
