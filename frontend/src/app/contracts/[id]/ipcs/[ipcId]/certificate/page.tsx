import { getIpcCertificate } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { PrintButton } from "@/components/ui/PrintButton";

export const dynamic = "force-dynamic";

export default async function IpcCertificatePage({ params }: { params: Promise<{ id: string; ipcId: string }> }) {
  const { id, ipcId } = await params;
  const cert = await getIpcCertificate(id, Number(ipcId));

  return (
    <div className="flex flex-col gap-[18px] max-w-[820px] mx-auto print:max-w-none">
      <div className="flex items-center justify-between print:hidden">
        <div>
          <div className="text-[16.5px] font-semibold">IPC Certificate — {cert.ipcNumber}</div>
          <div className="text-[12px] text-[#667085]">Downloadable progress payment certificate</div>
        </div>
        <PrintButton />
      </div>

      <Card padding="0" className="overflow-hidden">
        <div className="p-[28px] border-b border-[#e6e8ec]">
          <div className="text-[11px] font-semibold tracking-[.08em] uppercase text-[#98a2b3]">Interim Payment Certificate</div>
          <div className="text-[20px] font-bold mt-[4px]">{cert.ipcNumber}</div>
          <div className="font-mono text-[14px] text-[#3a5bd9] mt-[3px]">{cert.contractId}</div>
          <div className="text-[11.5px] text-[#98a2b3] mt-[6px]">Certified {cert.createdAt} · Status: {cert.status}</div>
        </div>

        <div className="p-[28px] grid grid-cols-2 gap-x-[24px] gap-y-[16px] border-b border-[#e6e8ec]">
          {[
            { label: "Contractor Name", value: cert.vendor },
            { label: "Contractor No.", value: cert.contractorNo },
            { label: "Project Name", value: cert.project },
            { label: "Project Number", value: cert.projectNo },
            { label: "Oracle PO", value: cert.oraclePo ?? "Not yet issued" },
            { label: "Oracle PO Revision", value: cert.oraclePoRev ?? "—" },
            { label: "Billing Period", value: cert.period },
            { label: "Payable Terms", value: cert.payableTermsDays },
          ].map((f) => (
            <div key={f.label}>
              <div className="text-[11px] font-medium text-[#667085] mb-[3px]">{f.label}</div>
              <div className="text-[13.5px] font-mono">{f.value}</div>
            </div>
          ))}
        </div>

        <div className="p-[28px]">
          <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">Certified Amounts</div>
          <div className="flex flex-col gap-[2px]">
            {[
              { label: "Work Done", value: cert.workDonePct, weight: 500, color: "#101828" },
              { label: "Gross Amount Certified", value: cert.gross, weight: 700, color: "#101828" },
              { label: `Retention Held (${cert.retentionPct})`, value: `− ${cert.retention}`, weight: 500, color: "#b45309" },
              { label: "Advance Recovered", value: `− ${cert.advanceRecovered}`, weight: 500, color: "#2c7fb0" },
              { label: "Net Payable to Contractor", value: cert.netPayable, weight: 700, color: "#12805c" },
            ].map((r) => (
              <div key={r.label} className="flex justify-between items-center py-[10px] border-b border-[#f4f5f7] text-[14px]">
                <span className="text-[#667085]">{r.label}</span>
                <span className="font-mono" style={{ fontWeight: r.weight, color: r.color }}>
                  {r.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="p-[20px] text-[11px] text-[#98a2b3] leading-[1.5] border-t border-[#e6e8ec]">
          This certificate confirms the progress payment amount certified against contract {cert.contractId} for the billing period
          above. It is issued to the contractor for record purposes and does not itself trigger payment — disbursement follows the
          contract's payable terms from the certification date shown above.
        </div>
      </Card>
    </div>
  );
}
