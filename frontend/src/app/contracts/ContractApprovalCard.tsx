import { Card } from "@/components/ui/Card";
import { ApprovalTimeline } from "@/components/ui/ApprovalTimeline";
import type { ApprovalStepOut } from "@/lib/types";
import { ContractAdvanceButton } from "./ContractApprovalActions";

export function ContractApprovalCard({ contractId, steps }: { contractId: string; steps: ApprovalStepOut[] }) {
  if (steps.length === 0) return null;
  const hasCurrentStep = steps.some((s) => s.state === "current");

  return (
    <Card>
      <div className="font-semibold text-[13.5px] mb-[14px]">Approval Routing</div>
      <ApprovalTimeline steps={steps} size="sm" />
      <ContractAdvanceButton contractId={contractId} hasCurrentStep={hasCurrentStep} />
    </Card>
  );
}
