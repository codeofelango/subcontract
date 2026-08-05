import { getContractSummary } from "@/lib/api";
import { Card, CardHeader } from "@/components/ui/Card";
import { PrintButton } from "@/components/ui/PrintButton";

export const dynamic = "force-dynamic";

export default async function ContractSummaryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const doc = await getContractSummary(id);

  return (
    <div className="flex flex-col gap-[18px] max-w-[900px] mx-auto print:max-w-none">
      <div className="flex items-center justify-between print:hidden">
        <div>
          <div className="text-[16.5px] font-semibold">Contract Summary — {doc.id}</div>
          <div className="text-[12px] text-[#667085]">Downloadable subcontract document</div>
        </div>
        <PrintButton />
      </div>

      <Card padding="0" className="overflow-hidden">
        <div className="p-[28px] border-b border-[#e6e8ec]">
          <div className="text-[20px] font-bold">Subcontract Agreement Summary</div>
          <div className="font-mono text-[14px] text-[#3a5bd9] mt-[4px]">{doc.id}</div>
          <div className="text-[11.5px] text-[#98a2b3] mt-[6px]">Generated {doc.createdAt} · Status: {doc.status}</div>
        </div>

        <div className="p-[28px] grid grid-cols-3 gap-x-[24px] gap-y-[16px] border-b border-[#e6e8ec]">
          {[
            { label: "Contractor Name", value: doc.vendor },
            { label: "Contractor No.", value: doc.contractorNo },
            { label: "Service Type", value: doc.serviceType },
            { label: "Project Name", value: doc.project },
            { label: "Project Number", value: doc.projectNo },
            { label: "Duration", value: `${doc.durationMonths} months` },
            { label: "Contract Value", value: doc.contractValue },
            { label: "Contract Budget", value: doc.contractBudget },
            { label: "Retention", value: doc.retentionPct },
            { label: "Advance Payment", value: doc.advancePct },
            { label: "Payable Terms", value: doc.payableTermsDays },
            { label: "Source PR (Oracle)", value: doc.sourcePr },
            { label: "Oracle PO", value: doc.oraclePo ?? "Not yet issued" },
            { label: "Oracle PO Revision", value: doc.oraclePoRev ?? "—" },
          ].map((f) => (
            <div key={f.label}>
              <div className="text-[11px] font-medium text-[#667085] mb-[3px]">{f.label}</div>
              <div className="text-[13.5px] font-mono">{f.value}</div>
            </div>
          ))}
        </div>

        <CardHeader>
          <span className="font-semibold text-[14px]">Line Items (BOQ)</span>
        </CardHeader>
        <table className="w-full border-collapse text-[12.5px]">
          <thead>
            <tr className="text-left text-[#667085] text-[10.5px] uppercase tracking-[.04em] bg-[#fafbfc]">
              <th className="px-[16px] py-[9px] font-semibold">Code</th>
              <th className="px-[16px] py-[9px] font-semibold">Oracle PR Line</th>
              <th className="px-[16px] py-[9px] font-semibold">Description</th>
              <th className="px-[16px] py-[9px] font-semibold text-right">Qty</th>
              <th className="px-[16px] py-[9px] font-semibold">UoM</th>
              <th className="px-[16px] py-[9px] font-semibold text-right">Unit Rate</th>
              <th className="px-[16px] py-[9px] font-semibold text-right">Total</th>
              <th className="px-[16px] py-[9px] font-semibold">SLA Package</th>
            </tr>
          </thead>
          <tbody>
            {doc.lineItems.map((li) => (
              <tr key={li.code + li.prLineRef} className="border-t border-[#f0f1f4]">
                <td className="px-[16px] py-[10px] font-mono text-[#475467]">{li.code}</td>
                <td className="px-[16px] py-[10px] font-mono text-[11.5px] text-[#3a5bd9]">{li.prLineRef}</td>
                <td className="px-[16px] py-[10px]">{li.description}</td>
                <td className="px-[16px] py-[10px] text-right">
                  <div className="font-mono">{li.qty}</div>
                  {li.revisedByCo && (
                    <div className="text-[10px] font-medium text-[#b45309] mt-[2px] whitespace-nowrap">
                      Rev via {li.revisedByCo} (was {li.previousQty})
                    </div>
                  )}
                </td>
                <td className="px-[16px] py-[10px] text-[#667085]">{li.uom}</td>
                <td className="px-[16px] py-[10px] text-right font-mono">{li.unitRate}</td>
                <td className="px-[16px] py-[10px] text-right font-mono font-semibold">{li.total}</td>
                <td className="px-[16px] py-[10px]">
                  <div className="flex flex-wrap gap-[5px]">
                    {li.slaTags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[10.5px] font-medium px-[8px] py-[3px] rounded-[20px] bg-[#3a5bd9]/[.08] text-[#3a5bd9]"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="p-[20px] text-[11px] text-[#98a2b3] leading-[1.5]">
          This document is generated from the subcontract management system for record-keeping and vendor-portal reference. It does
          not replace the signed contract or the corresponding Oracle Purchase Order.
        </div>
      </Card>
    </div>
  );
}
