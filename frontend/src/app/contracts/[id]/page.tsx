import Link from "next/link";
import { FileDown, FileSpreadsheet, PackageCheck, Receipt } from "lucide-react";
import { getContractApprovalFlow, getContractApprovalSteps, getContractAttachments, getContractTracking, getVendorSubmissions } from "@/lib/api";
import { BackLink } from "@/components/ui/BackLink";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { CertifyButton } from "./VendorPortalActions";
import { ContractApprovalCard } from "../ContractApprovalCard";
import { AttachmentsCard } from "../AttachmentsCard";

export const dynamic = "force-dynamic";

export default async function ContractTrackingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [data, vendorSubmissions, approvalSteps, approvalFlow, attachments] = await Promise.all([
    getContractTracking(id),
    getVendorSubmissions(id),
    getContractApprovalSteps(id),
    getContractApprovalFlow(id),
    getContractAttachments(id),
  ]);
  const { header, finance, trackers, ipcs } = data;

  return (
    <div className="flex flex-col gap-[18px] max-w-[1280px]">
      <BackLink href="/contracts" label="Back to Contracts" />
      {/* Header card */}
      <Card padding="18px 20px" className="flex items-center gap-[20px] flex-wrap">
        <div>
          <div className="flex items-center gap-[10px]">
            <span className="font-mono font-semibold text-[15px] text-[#3a5bd9]">{header.id}</span>
            <Pill color="#12805c" bg="#e6f4ee">
              {header.status}
            </Pill>
          </div>
          <div className="text-[17px] font-semibold mt-[4px]">{header.vendor}</div>
          <div className="text-[12.5px] text-[#667085]">
            {header.type} · {header.project}
          </div>
          <div className="flex gap-[8px] mt-[10px] flex-wrap">
            <span className="flex items-center gap-[6px] text-[11.5px] font-medium px-[10px] py-[4px] rounded-[7px] bg-[#3a5bd9]/[.08] text-[#3a5bd9]">
              Oracle PO <span className="font-mono font-semibold">{header.po ?? "—"}</span> · {header.poRev ?? "—"}
            </span>
            <span className="flex items-center gap-[6px] text-[11.5px] font-medium px-[10px] py-[4px] rounded-[7px] bg-[#f0f1f4] text-[#475467]">
              Source PR <span className="font-mono font-semibold">{header.pr}</span>
            </span>
            {header.poDffRef && (
              <span className="flex items-center gap-[6px] text-[11.5px] font-medium px-[10px] py-[4px] rounded-[7px] bg-[#f0ecfb] text-[#7a5bd9]">
                PO DFF Contract Ref <span className="font-mono font-semibold">{header.poDffRef}</span>
              </span>
            )}
          </div>
          <div className="text-[11px] text-[#98a2b3] mt-[6px] max-w-[440px] leading-[1.4]">
            PO auto-created in Oracle on approval, with this contract's number written into the PO's Descriptive
            Flexfield (DFF) so the PO can be traced back to it; Source PR is the approved Oracle requisition that
            triggered this contract.
          </div>
        </div>
        <div className="flex-1" />
        <div className="flex gap-[26px]">
          <div className="min-w-[110px]">
            <div className="text-[11px] text-[#98a2b3]">Overall Progress</div>
            <div className="text-[20px] font-bold font-mono">{header.progress}</div>
            <div className="mt-[6px]">
              <ProgressBar width={header.progress} color={header.progressColor} height={6} />
            </div>
          </div>
          <div>
            <div className="text-[11px] text-[#98a2b3]">Remaining Duration</div>
            <div className="text-[20px] font-bold font-mono">{header.remainMonths}</div>
          </div>
          <div>
            <div className="text-[11px] text-[#98a2b3]">Expires</div>
            <div className="text-[20px] font-bold font-mono">{header.expiry}</div>
          </div>
        </div>
        <Link
          href={`/contracts/${header.id}/summary`}
          className="flex items-center gap-[7px] bg-white border border-[#e6e8ec] rounded-[8px] px-[13px] py-[9px] text-[12.5px] font-semibold text-[#475467] hover:bg-[#fafbfc]"
        >
          <FileDown size={15} strokeWidth={2} />
          Download Contract Form
        </Link>
      </Card>

      <ContractApprovalCard contractId={header.id} steps={approvalSteps} workflowName={approvalFlow.workflowName} />
      <AttachmentsCard attachments={attachments} />

      {/* Finance cards */}
      <div className="grid grid-cols-5 gap-[14px]">
        {finance.map((f) => (
          <Card key={f.label} padding="16px">
            <div className="text-[11.5px] text-[#667085] mb-[8px]">{f.label}</div>
            <div className="text-[19px] font-bold font-mono">{f.value}</div>
            <div className="text-[11.5px] mt-[5px]" style={{ color: f.color }}>
              {f.note}
            </div>
          </Card>
        ))}
      </div>

      {/* Trackers */}
      <div className="grid grid-cols-3 gap-[16px]">
        {trackers.map((t) => (
          <Card key={t.title}>
            <div className="flex items-center justify-between mb-[14px]">
              <span className="font-semibold text-[13.5px]">{t.title}</span>
              <span className="text-[11px] text-[#98a2b3]">{t.sub}</span>
            </div>
            <div className="mb-[14px]">
              <ProgressBar width={t.barW} color={t.barColor} height={9} />
            </div>
            {t.rows.map((r) => (
              <div key={r.k} className="flex justify-between py-[6px] text-[12.5px] border-b border-[#f6f7f9]">
                <span className="text-[#667085]">{r.k}</span>
                <span className="font-mono" style={{ fontWeight: r.w, color: r.c }}>
                  {r.v}
                </span>
              </div>
            ))}
          </Card>
        ))}
      </div>

      {/* Invoice Submission - work progress claimed by the subcontractor via the Oracle vendor portal */}
      <Card padding="0" className="overflow-hidden">
        <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] flex items-center justify-between">
          <div>
            <div className="font-semibold text-[14px]">Invoice Submission</div>
            <div className="text-[11px] text-[#98a2b3] mt-[2px]">Work-progress invoices submitted via the Oracle vendor portal</div>
          </div>
        </div>
        {vendorSubmissions.length === 0 ? (
          <div className="px-[18px] py-[16px] text-[12.5px] text-[#98a2b3]">No pending submissions from the vendor portal.</div>
        ) : (
          <table className="w-full border-collapse text-[12.5px]">
            <thead>
              <tr className="text-left text-[#667085] text-[10.5px] uppercase tracking-[.04em] bg-[#fafbfc]">
                <th className="px-[16px] py-[10px] font-semibold">Period</th>
                <th className="px-[16px] py-[10px] font-semibold text-right">Work Done</th>
                <th className="px-[16px] py-[10px] font-semibold text-right">Gross Claimed</th>
                <th className="px-[16px] py-[10px] font-semibold">Submitted By</th>
                <th className="px-[16px] py-[10px] font-semibold">Submitted On</th>
                <th className="px-[16px] py-[10px] font-semibold">Status</th>
                <th className="px-[16px] py-[10px] font-semibold" />
              </tr>
            </thead>
            <tbody>
              {vendorSubmissions.map((s) => (
                <tr key={s.id} className="border-t border-[#f0f1f4]">
                  <td className="px-[16px] py-[11px] text-[#475467]">{s.period}</td>
                  <td className="px-[16px] py-[11px] text-right font-mono">{s.workDonePct}</td>
                  <td className="px-[16px] py-[11px] text-right font-mono">{s.grossClaimed}</td>
                  <td className="px-[16px] py-[11px]">{s.submittedBy}</td>
                  <td className="px-[16px] py-[11px] text-[#667085]">{s.submittedAt}</td>
                  <td className="px-[16px] py-[11px]">
                    <Pill color={s.status === "Certified" ? "#12805c" : "#b45309"} bg={s.status === "Certified" ? "#e6f4ee" : "#fbf1e3"}>
                      {s.status}
                    </Pill>
                  </td>
                  <td className="px-[16px] py-[11px] text-right max-w-[280px]">
                    {s.status === "Submitted" ? (
                      <CertifyButton contractId={header.id} submissionId={s.id} />
                    ) : (
                      s.confirmationMessage && <span className="text-[11.5px] font-medium text-[#12805c]">{s.confirmationMessage}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* GRN List (IPC schedule) */}
      <Card padding="0" className="overflow-hidden">
        <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] font-semibold text-[14px]">GRN List</div>
        <table className="w-full border-collapse text-[12.5px]">
          <thead>
            <tr className="text-left text-[#667085] text-[10.5px] uppercase tracking-[.04em] bg-[#fafbfc]">
              <th className="px-[16px] py-[10px] font-semibold">GRN</th>
              <th className="px-[16px] py-[10px] font-semibold">Period</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Work Done</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Gross</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Retention</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Advance Rec.</th>
              <th className="px-[16px] py-[10px] font-semibold text-right">Net Payable</th>
              <th className="px-[16px] py-[10px] font-semibold">Status</th>
              <th className="px-[16px] py-[10px] font-semibold" />
            </tr>
          </thead>
          <tbody>
            {ipcs.map((i) => (
              <tr key={i.id} className="border-t border-[#f0f1f4]">
                <td className="px-[16px] py-[11px] font-mono font-semibold">{i.n}</td>
                <td className="px-[16px] py-[11px] text-[#475467]">{i.period}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{i.done}</td>
                <td className="px-[16px] py-[11px] text-right font-mono">{i.gross}</td>
                <td className="px-[16px] py-[11px] text-right font-mono text-[#b45309]">{i.ret}</td>
                <td className="px-[16px] py-[11px] text-right font-mono text-[#2c7fb0]">{i.adv}</td>
                <td className="px-[16px] py-[11px] text-right font-mono font-semibold">{i.net}</td>
                <td className="px-[16px] py-[11px]">
                  <Pill color={i.color} bg={i.bg}>
                    {i.status}
                  </Pill>
                </td>
                <td className="px-[16px] py-[11px] text-right">
                  <div className="flex items-center justify-end gap-[14px]">
                    <Link
                      href={`/contracts/${header.id}/ipcs/${i.id}/certificate`}
                      className="flex items-center gap-[5px] text-[11.5px] font-semibold text-[#3a5bd9] hover:underline whitespace-nowrap"
                    >
                      <FileDown size={13} strokeWidth={2} />
                      Certificate
                    </Link>
                    <Link
                      href={`/contracts/${header.id}/ipcs/${i.id}/report`}
                      className="flex items-center gap-[5px] text-[11.5px] font-semibold text-[#475467] hover:underline whitespace-nowrap"
                    >
                      <FileSpreadsheet size={13} strokeWidth={2} />
                      BOQ Report
                    </Link>
                    <Link
                      href={`/contracts/${header.id}/ipcs/${i.id}/invoice`}
                      className="flex items-center gap-[5px] text-[11.5px] font-semibold text-[#7a5bd9] hover:underline whitespace-nowrap"
                    >
                      <Receipt size={13} strokeWidth={2} />
                      Invoice
                    </Link>
                    <Link
                      href={`/contracts/${header.id}/ipcs/${i.id}/grn-invoice`}
                      className="flex items-center gap-[5px] text-[11.5px] font-semibold text-[#2c7fb0] hover:underline whitespace-nowrap"
                    >
                      <PackageCheck size={13} strokeWidth={2} />
                      GRN Invoice
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
