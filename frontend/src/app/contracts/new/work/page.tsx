import Link from "next/link";
import { ArrowLeft, FileSpreadsheet } from "lucide-react";
import { getApprovalPreview, getNewContractDraft, listOraclePrs } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { NewContractForm } from "../NewContractForm";

export const dynamic = "force-dynamic";

export default async function NewWorkContractPage({ searchParams }: { searchParams: Promise<{ pr?: string }> }) {
  const { pr } = await searchParams;

  if (!pr) {
    const prs = await listOraclePrs();
    return (
      <div className="max-w-[880px]">
        <Link href="/contracts/new" className="flex items-center gap-[6px] text-[12.5px] font-semibold text-[#475467] hover:text-[#3a5bd9] mb-[14px] w-fit">
          <ArrowLeft size={15} strokeWidth={2.2} />
          Back
        </Link>
        <div className="text-[13px] text-[#667085] mb-[18px]">
          Select the approved Oracle PR that triggers this contract. Its BOQ, payment terms, and SLA package flow
          in from Oracle and can be edited before submission.
        </div>
        {prs.length === 0 ? (
          <Card>
            <div className="text-[13px] text-[#98a2b3]">No approved Oracle PR available to draft a contract from.</div>
          </Card>
        ) : (
          <div className="flex flex-col gap-[10px]">
            {prs.map((p) => (
              <Link key={p.id} href={`/contracts/new/work?pr=${p.id}`}>
                <Card
                  className="flex items-center gap-[14px] flex-wrap hover:border-[#3a5bd9] transition-colors cursor-pointer"
                  padding="14px 18px"
                >
                  <div className="w-[34px] h-[34px] rounded-[8px] bg-[#3a5bd9]/[.1] flex items-center justify-center flex-none">
                    <FileSpreadsheet size={16} color="#3a5bd9" strokeWidth={2} />
                  </div>
                  <div className="flex-1 min-w-[160px]">
                    <div className="font-mono font-semibold text-[13px] text-[#3a5bd9]">{p.id}</div>
                    <div className="text-[12.5px] text-[#475467] truncate">
                      {p.vendorName} · {p.projectName} · {p.serviceType}
                    </div>
                  </div>
                  <div className="font-mono font-semibold text-[13px]">{p.contractValueFmt}</div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    );
  }

  const [draft, approvalPreview] = await Promise.all([getNewContractDraft(pr), getApprovalPreview("contract_scope")]);
  return <NewContractForm draft={draft} approvalPreview={approvalPreview} />;
}
