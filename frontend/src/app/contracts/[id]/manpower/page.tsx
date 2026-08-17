import { getContractApprovalFlow, getContractApprovalSteps, getContractAttachments, getManpowerContractSummary } from "@/lib/api";
import { BackLink } from "@/components/ui/BackLink";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { PrintButton } from "@/components/ui/PrintButton";
import { ContractApprovalCard } from "../../ContractApprovalCard";
import { AttachmentsCard } from "../../AttachmentsCard";

export const dynamic = "force-dynamic";

export default async function ManpowerContractSummaryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [c, approvalSteps, approvalFlow, attachments] = await Promise.all([
    getManpowerContractSummary(id),
    getContractApprovalSteps(id),
    getContractApprovalFlow(id),
    getContractAttachments(id),
  ]);

  return (
    <div className="flex flex-col gap-[18px] max-w-[1200px] print:max-w-none">
      <BackLink href="/contracts" label="Back to Contracts" />
      <Card padding="18px 20px" className="flex items-center gap-[20px] flex-wrap">
        <div>
          <div className="flex items-center gap-[10px]">
            <span className="font-mono font-semibold text-[15px] text-[#3a5bd9]">{c.id}</span>
            <Pill color={c.status === "Active" ? "#12805c" : "#b45309"} bg={c.status === "Active" ? "#e6f4ee" : "#fbf1e3"}>
              {c.status}
            </Pill>
            <span className="text-[11px] font-semibold px-[9px] py-[3px] rounded-[6px] text-[#2c7fb0] bg-[#e7f1f8]">Manpower Supply</span>
          </div>
          <div className="text-[17px] font-semibold mt-[4px]">{c.vendorName}</div>
          <div className="text-[12.5px] text-[#667085]">
            {c.contractorNo} · {c.serviceType}
          </div>
        </div>
        <div className="flex-1" />
        <div className="flex gap-[26px]">
          <div>
            <div className="text-[11px] text-[#98a2b3]">Contract Value</div>
            <div className="text-[20px] font-bold font-mono">{c.contractValue}</div>
          </div>
          <div>
            <div className="text-[11px] text-[#98a2b3]">Contract Budget</div>
            <div className="text-[20px] font-bold font-mono">{c.contractBudget}</div>
          </div>
        </div>
        <PrintButton label="Download Contract Form" />
      </Card>

      <ContractApprovalCard contractId={c.id} steps={approvalSteps} workflowName={approvalFlow.workflowName} />
      <AttachmentsCard attachments={attachments} />

      <div className="grid grid-cols-4 gap-[14px]">
        {[
          { label: "Issue Date", value: c.issueDate },
          { label: "Expiry / Renewal Terms", value: c.expiryTerms },
          { label: "Termination Notice", value: c.terminationNotice },
          { label: "Payment Terms", value: c.paymentTermsNote },
          { label: "Email Address", value: c.emailAddress },
          { label: "Account Number", value: c.accountNumber },
        ].map((f) => (
          <Card key={f.label} padding="14px 16px">
            <div className="text-[11px] text-[#98a2b3] mb-[6px]">{f.label}</div>
            <div className="text-[13.5px] font-medium break-words">{f.value}</div>
          </Card>
        ))}
      </div>

      <Card padding="0" className="overflow-hidden">
        <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] font-semibold text-[14px]">Position Rate Card</div>
        <table className="w-full border-collapse text-[12.5px]">
          <thead>
            <tr className="text-left text-[#667085] text-[10.5px] uppercase tracking-[.04em] bg-[#fafbfc]">
              <th className="px-[16px] py-[10px] font-semibold">Category Position</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Total Staff</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Working Hrs</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Basic Salary</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">H Allow.</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">T Allow.</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">F Allow.</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Share</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Total Cost</th>
              <th className="px-[16px] py-[10px] font-semibold">Leave Treatment</th>
              <th className="px-[16px] py-[10px] font-semibold">Absence Treatment</th>
            </tr>
          </thead>
          <tbody>
            {c.positionLines.map((li, i) => (
              <tr key={i} className="border-t border-[#f0f1f4]">
                <td className="px-[16px] py-[11px] font-semibold">{li.categoryPosition}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{li.totalStaff}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{li.workingHours}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{li.basicSalary}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{li.hAllowance}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{li.tAllowance}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{li.fAllowance}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{li.share}</td>
                <td className="px-[16px] py-[11px] text-right font-mono font-semibold">{li.totalCost}</td>
                <td className="px-[16px] py-[11px] text-[#475467]">{li.leaveTreatment}</td>
                <td className="px-[16px] py-[11px] text-[#475467]">{li.absenceTreatment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
