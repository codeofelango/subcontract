import { getIpcReport } from "@/lib/api";
import { BackLink } from "@/components/ui/BackLink";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { PrintButton } from "@/components/ui/PrintButton";

export const dynamic = "force-dynamic";

export default async function IpcReportPage({ params }: { params: Promise<{ id: string; ipcId: string }> }) {
  const { id, ipcId } = await params;
  const report = await getIpcReport(id, Number(ipcId));

  const summaryRows = [
    { label: "Gross BOQ Value (Contract)", value: report.totals.boqGrossTotal, weight: 500, color: "#101828" },
    { label: "Executed Previously", value: report.totals.previousAmountTotal, weight: 500, color: "#667085" },
    { label: "Executed This Period", value: report.totals.currentAmountTotal, weight: 700, color: "#101828" },
    { label: "Total Executed to Date", value: report.totals.totalExecutedToDate, weight: 700, color: "#12805c" },
  ];

  const certifiedRows = [
    { label: "Current Period", current: report.totals.retentionCurrent, toDate: report.totals.retentionToDate, header: `Retention (${report.totals.retentionPct})`, color: "#b45309" },
    { label: "Advance", current: report.totals.advanceRecoveredCurrent, toDate: report.totals.advanceRecoveredToDate, header: `Advance Recovered (${report.totals.advancePct})`, color: "#2c7fb0" },
    { label: "Net", current: report.totals.netPayableCurrent, toDate: report.totals.netPayableToDate, header: "Net Payable", color: "#12805c" },
  ];

  return (
    <div className="flex flex-col gap-[18px] max-w-[1180px] mx-auto print:max-w-none">
      <BackLink href={`/contracts/${id}`} label="Back to Contract Tracking" />
      <div className="flex items-center justify-between print:hidden">
        <div>
          <div className="text-[16.5px] font-semibold">IPC Report — {report.ipcNumber}</div>
          <div className="text-[12px] text-[#667085]">BOQ execution breakdown · internal PMO / QS review copy</div>
        </div>
        <PrintButton label="Download / Print Report" />
      </div>

      <Card padding="0" className="overflow-hidden">
        <div className="p-[28px] border-b border-[#e6e8ec] flex items-start justify-between gap-[16px] flex-wrap">
          <div>
            <div className="text-[11px] font-semibold tracking-[.08em] uppercase text-[#98a2b3]">Interim Payment Certificate — BOQ Report</div>
            <div className="text-[20px] font-bold mt-[4px]">{report.ipcNumber}</div>
            <div className="font-mono text-[14px] text-[#3a5bd9] mt-[3px]">{report.contractId}</div>
            <div className="text-[11.5px] text-[#98a2b3] mt-[6px]">Certified {report.createdAt} · Period {report.period}</div>
          </div>
          <Pill color={report.status === "Paid" ? "#12805c" : "#3a5bd9"} bg={report.status === "Paid" ? "#e6f4ee" : "#eef1fd"}>
            {report.status}
          </Pill>
        </div>

        <div className="p-[28px] grid grid-cols-4 gap-x-[24px] gap-y-[16px] border-b border-[#e6e8ec]">
          {[
            { label: "Subcontractor", value: report.vendor },
            { label: "Contractor No.", value: report.contractorNo },
            { label: "Project", value: report.project },
            { label: "Project No.", value: report.projectNo },
            { label: "Oracle PO", value: report.oraclePo ?? "Not yet issued" },
            { label: "PO Revision", value: report.oraclePoRev ?? "—" },
            { label: "Source PR", value: report.sourcePr ?? "—" },
            { label: "Contract Number", value: report.contractId },
          ].map((f) => (
            <div key={f.label}>
              <div className="text-[11px] font-medium text-[#667085] mb-[3px]">{f.label}</div>
              <div className="text-[13px] font-mono">{f.value}</div>
            </div>
          ))}
        </div>

        <div className="p-[28px] border-b border-[#e6e8ec]">
          <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">
            BOQ Execution — Previous / Current / Total
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12px] whitespace-nowrap">
              <thead>
                <tr className="text-left text-[#667085] text-[10px] uppercase tracking-[.04em] bg-[#fafbfc]">
                  <th rowSpan={2} className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec] align-bottom">Code</th>
                  <th rowSpan={2} className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec] align-bottom">Description</th>
                  <th rowSpan={2} className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec] align-bottom">UoM</th>
                  <th colSpan={3} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec] bg-[#f4f5f7]">Contract BOQ</th>
                  <th colSpan={2} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec]">Previous</th>
                  <th colSpan={2} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec] bg-[#eef1fd]">Current</th>
                  <th colSpan={2} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec]">Total to Date</th>
                </tr>
                <tr className="text-left text-[#667085] text-[10px] uppercase tracking-[.04em] bg-[#fafbfc]">
                  <th className="px-[10px] py-[8px] font-semibold text-right border-l border-[#e6e8ec] bg-[#f4f5f7]">Qty</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right bg-[#f4f5f7]">Rate</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right bg-[#f4f5f7]">Total</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-l border-[#e6e8ec]">Qty</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right">Amount</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-l border-[#e6e8ec] bg-[#eef1fd]">Qty</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right bg-[#eef1fd]">Amount</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-l border-[#e6e8ec]">Qty</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {report.lines.map((l) => (
                  <tr key={l.code} className="border-t border-[#f0f1f4] hover:bg-[#fafbfc]">
                    <td className="px-[10px] py-[9px] font-mono font-medium">{l.code}</td>
                    <td className="px-[10px] py-[9px] whitespace-normal min-w-[180px]">{l.description}</td>
                    <td className="px-[10px] py-[9px] text-[#667085]">{l.uom}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono border-l border-[#f0f1f4] bg-[#fafbfc]">{l.contractQty}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono bg-[#fafbfc]">{l.unitRate}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono font-semibold bg-[#fafbfc]">{l.contractTotal}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono border-l border-[#f0f1f4] text-[#667085]">{l.previousQty}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono text-[#667085]">{l.previousAmount}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono border-l border-[#f0f1f4]">{l.currentQty}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono font-semibold text-[#3a5bd9]">{l.currentAmount}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono border-l border-[#f0f1f4]">{l.totalQty}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono font-semibold">{l.totalAmount}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-[#101828] font-semibold">
                  <td colSpan={5} className="px-[10px] py-[10px] text-right">Gross Total =</td>
                  <td className="px-[10px] py-[10px] text-right font-mono">{report.totals.boqGrossTotal}</td>
                  <td className="px-[10px] py-[10px] text-right border-l border-[#f0f1f4]" />
                  <td className="px-[10px] py-[10px] text-right font-mono">{report.totals.previousAmountTotal}</td>
                  <td className="px-[10px] py-[10px] text-right border-l border-[#f0f1f4]" />
                  <td className="px-[10px] py-[10px] text-right font-mono text-[#3a5bd9]">{report.totals.currentAmountTotal}</td>
                  <td className="px-[10px] py-[10px] text-right border-l border-[#f0f1f4]" />
                  <td className="px-[10px] py-[10px] text-right font-mono">{report.totals.totalExecutedToDate}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div className="text-[10.5px] text-[#98a2b3] mt-[10px] leading-[1.5]">
            Per-line Previous/Current/Total figures apportion this IPC&apos;s certified gross amount across BOQ lines pro-rata to each
            line&apos;s share of the contract BOQ value — the underlying model tracks progress at the IPC/contract level, not per BOQ line.
          </div>
        </div>

        <div className="p-[28px] grid grid-cols-2 gap-[24px] border-b border-[#e6e8ec]">
          <div>
            <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">Executed Work Summary</div>
            <div className="flex flex-col gap-[2px]">
              {summaryRows.map((r) => (
                <div key={r.label} className="flex justify-between items-center py-[9px] border-b border-[#f4f5f7] text-[13px]">
                  <span className="text-[#667085]">{r.label}</span>
                  <span className="font-mono" style={{ fontWeight: r.weight, color: r.color }}>{r.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">Certified Deductions</div>
            <table className="w-full text-[13px] border-collapse">
              <thead>
                <tr className="text-[10.5px] uppercase tracking-[.04em] text-[#98a2b3]">
                  <th className="text-left font-semibold pb-[8px]" />
                  <th className="text-right font-semibold pb-[8px]">This IPC</th>
                  <th className="text-right font-semibold pb-[8px]">To Date</th>
                </tr>
              </thead>
              <tbody>
                {certifiedRows.map((r) => (
                  <tr key={r.header} className="border-t border-[#f4f5f7]">
                    <td className="py-[9px] text-[#667085]">{r.header}</td>
                    <td className="py-[9px] text-right font-mono" style={{ color: r.color }}>{r.current}</td>
                    <td className="py-[9px] text-right font-mono font-semibold" style={{ color: r.color }}>{r.toDate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="p-[28px] grid grid-cols-2 gap-[16px]">
          <Card padding="16px" className="bg-[#fafbfc]">
            <div className="font-semibold text-[13px] mb-[10px]">Advance Payment Tracking</div>
            {[
              { k: "Advance Paid", v: report.advanceTracker.advancePaid },
              { k: "Recovered to Date", v: report.advanceTracker.advanceRecoveredToDate },
              { k: "Outstanding Advance", v: report.advanceTracker.outstandingAdvance },
            ].map((r) => (
              <div key={r.k} className="flex justify-between py-[6px] text-[12.5px] border-b border-[#f0f1f4] last:border-0">
                <span className="text-[#667085]">{r.k}</span>
                <span className="font-mono font-semibold">{r.v}</span>
              </div>
            ))}
          </Card>
          <Card padding="16px" className="bg-[#fafbfc]">
            <div className="font-semibold text-[13px] mb-[10px]">Retention Tracking</div>
            {[
              { k: "Retention Held to Date", v: report.retentionTracker.retentionHeldToDate },
              { k: "Released", v: report.retentionTracker.retentionReleased },
              { k: "Net Retention", v: report.retentionTracker.netRetention },
            ].map((r) => (
              <div key={r.k} className="flex justify-between py-[6px] text-[12.5px] border-b border-[#f0f1f4] last:border-0">
                <span className="text-[#667085]">{r.k}</span>
                <span className="font-mono font-semibold">{r.v}</span>
              </div>
            ))}
          </Card>
        </div>

        <div className="p-[20px] text-[11px] text-[#98a2b3] leading-[1.5] border-t border-[#e6e8ec]">
          Internal BOQ execution report for {report.ipcNumber} against contract {report.contractId}. For the flat vendor-facing
          certificate, see the IPC Certificate document.
        </div>
      </Card>
    </div>
  );
}
