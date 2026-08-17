import { getIpcInvoice } from "@/lib/api";
import { BackLink } from "@/components/ui/BackLink";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { PrintButton } from "@/components/ui/PrintButton";

export const dynamic = "force-dynamic";

export default async function IpcInvoicePage({ params }: { params: Promise<{ id: string; ipcId: string }> }) {
  const { id, ipcId } = await params;
  const inv = await getIpcInvoice(id, Number(ipcId));

  return (
    <div className="flex flex-col gap-[18px] max-w-[1180px] mx-auto print:max-w-none">
      <BackLink href={`/contracts/${id}`} label="Back to Contract Tracking" />
      <div className="flex items-center justify-between print:hidden">
        <div>
          <div className="text-[16.5px] font-semibold">Invoice — {inv.invoiceNumber}</div>
          <div className="text-[12px] text-[#667085]">Vendor invoice / payment certificate — VAT, advance recovery, retention & LC</div>
        </div>
        <PrintButton label="Download / Print Invoice" />
      </div>

      <Card padding="0" className="overflow-hidden">
        <div className="p-[24px] border-b border-[#e6e8ec] grid grid-cols-3 gap-x-[24px] gap-y-[10px]">
          {[
            { label: "Project No.", value: inv.projectNo },
            { label: "Date", value: inv.date },
            { label: "Invoice No.", value: inv.invoiceNumber },
            { label: "Project", value: inv.project },
            { label: "Ref", value: inv.refNote ?? "—" },
            { label: "Location", value: inv.location ?? "—" },
            { label: "Subcontractor", value: inv.vendor },
            { label: "ERP Ref", value: inv.erpRef ?? "—" },
            { label: "Contract Number", value: inv.contractNumber },
          ].map((f) => (
            <div key={f.label}>
              <div className="text-[11px] font-medium text-[#667085] mb-[3px]">{f.label}</div>
              <div className="text-[13px] font-mono underline decoration-[#e6e8ec] underline-offset-2">{f.value}</div>
            </div>
          ))}
          <div className="col-span-3 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-medium text-[#667085] mb-[3px]">Period</div>
              <div className="text-[13px] font-mono">
                {inv.periodFrom && inv.periodTo ? `from (${inv.periodFrom}) to (${inv.periodTo})` : "—"}
              </div>
            </div>
            <Pill color={inv.status === "Paid" ? "#12805c" : "#3a5bd9"} bg={inv.status === "Paid" ? "#e6f4ee" : "#eef1fd"}>
              {inv.status}
            </Pill>
          </div>
        </div>

        <div className="p-[24px] border-b border-[#e6e8ec]">
          <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">
            B.O.Q as Contract — Executed Work
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12px] whitespace-nowrap">
              <thead>
                <tr className="text-left text-[#667085] text-[10px] uppercase tracking-[.04em] bg-[#fafbfc]">
                  <th rowSpan={2} className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec] align-bottom">Code</th>
                  <th rowSpan={2} className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec] align-bottom">Description</th>
                  <th rowSpan={2} className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec] align-bottom">Unit</th>
                  <th colSpan={3} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec] bg-[#f4f5f7]">B.O.Q Subcontractor</th>
                  <th colSpan={2} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec]">Previous</th>
                  <th colSpan={2} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec] bg-[#eef1fd]">Current</th>
                  <th colSpan={2} className="px-[10px] py-[6px] font-semibold text-center border-b border-l border-[#e6e8ec]">Total</th>
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
                {inv.lines.map((l) => (
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
                  <td className="px-[10px] py-[10px] text-right font-mono">{inv.totals.boqGrossTotal}</td>
                  <td className="px-[10px] py-[10px] text-right border-l border-[#f0f1f4]" />
                  <td className="px-[10px] py-[10px] text-right font-mono">{inv.totals.previousExecuted}</td>
                  <td className="px-[10px] py-[10px] text-right border-l border-[#f0f1f4]" />
                  <td className="px-[10px] py-[10px] text-right font-mono text-[#3a5bd9]">{inv.totals.currentExecuted}</td>
                  <td className="px-[10px] py-[10px] text-right border-l border-[#f0f1f4]" />
                  <td className="px-[10px] py-[10px] text-right font-mono">{inv.totals.totalExecutedToDate}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="mt-[16px] overflow-x-auto">
            <table className="w-full border-collapse text-[12.5px]">
              <thead>
                <tr className="text-left text-[10.5px] uppercase tracking-[.04em] text-[#98a2b3]">
                  <th className="text-left font-semibold pb-[8px]">Deduction / Charge</th>
                  <th className="text-right font-semibold pb-[8px]">Previous</th>
                  <th className="text-right font-semibold pb-[8px]">Current</th>
                  <th className="text-right font-semibold pb-[8px]">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-[#f0f1f4]">
                  <td className="py-[9px] font-semibold text-[#12805c]">VAT 15%</td>
                  <td className="py-[9px] text-right font-mono text-[#12805c]">+ {inv.totals.vatPreviousTotal}</td>
                  <td className="py-[9px] text-right font-mono text-[#12805c]">+ {inv.totals.vatCurrentTotal}</td>
                  <td className="py-[9px] text-right font-mono font-semibold text-[#12805c]">+ {inv.totals.vatToDateTotal}</td>
                </tr>
                {inv.totals.deductions.map((d) => (
                  <tr key={d.label} className="border-t border-[#f0f1f4]">
                    <td className="py-[9px] text-[#b45309]">{d.label}</td>
                    <td className="py-[9px] text-right font-mono text-[#b45309]">− {d.previous}</td>
                    <td className="py-[9px] text-right font-mono text-[#b45309]">− {d.current}</td>
                    <td className="py-[9px] text-right font-mono font-semibold text-[#b45309]">− {d.toDate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="p-[24px] border-b border-[#e6e8ec]">
          <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">Payment Certificate Summary</div>
          <div className="grid grid-cols-2 gap-[24px]">
            <div className="flex flex-col gap-[2px]">
              {[
                { label: "Contract Value", value: inv.totals.boqGrossTotal, weight: 500, color: "#101828" },
                { label: "Total Certified Amount (Executed to Date)", value: inv.totals.totalExecutedToDate, weight: 500, color: "#101828" },
                { label: "VAT 15% (to date)", value: `+ ${inv.totals.vatToDateTotal}`, weight: 500, color: "#12805c" },
                { label: "Total Executed to Date (incl. VAT)", value: inv.totals.totalExecutedInclVatToDate, weight: 700, color: "#101828" },
              ].map((r) => (
                <div key={r.label} className="flex justify-between items-center py-[9px] border-b border-[#f4f5f7] text-[13px]">
                  <span className="text-[#667085]">{r.label}</span>
                  <span className="font-mono" style={{ fontWeight: r.weight, color: r.color }}>{r.value}</span>
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-[2px]">
              {[
                { label: "Less: Previous Net Paid", value: `− ${inv.totals.previousNetPaid}`, weight: 500, color: "#b45309" },
                { label: "Less: Total Deduction (this period)", value: `− ${inv.totals.totalDeductionCurrent}`, weight: 500, color: "#b45309" },
                { label: "Total Deduction to Date", value: `− ${inv.totals.totalDeductionToDate}`, weight: 500, color: "#667085" },
              ].map((r) => (
                <div key={r.label} className="flex justify-between items-center py-[9px] border-b border-[#f4f5f7] text-[13px]">
                  <span className="text-[#667085]">{r.label}</span>
                  <span className="font-mono" style={{ fontWeight: r.weight, color: r.color }}>{r.value}</span>
                </div>
              ))}
              <div className="flex justify-between items-center py-[12px] mt-[6px] bg-[#e6f4ee] rounded-[8px] px-[12px]">
                <span className="text-[13px] font-semibold text-[#12805c]">Net Amount Payable (this invoice)</span>
                <span className="font-mono font-bold text-[16px] text-[#12805c]">{inv.totals.netAmountCurrent}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-[24px] grid grid-cols-3 gap-[16px]">
          <Card padding="16px" className="bg-[#fafbfc]">
            <div className="font-semibold text-[13px] mb-[10px]">Statement of Advance Payment</div>
            {inv.advanceStatements.map((s) => (
              <div key={s.label} className={`mb-[10px] pb-[10px] border-b border-[#f0f1f4] last:border-0 last:mb-0 last:pb-0 ${!s.applicable ? "opacity-50" : ""}`}>
                <div className="text-[12px] font-medium text-[#475467] mb-[4px]">{s.label} ({s.pctOfContract} of contract)</div>
                {[
                  { k: "Amount", v: s.amount },
                  { k: "Recovered to Date", v: s.recoveredToDate },
                  { k: "Outstanding", v: s.outstanding },
                ].map((r) => (
                  <div key={r.k} className="flex justify-between text-[11.5px] py-[2px]">
                    <span className="text-[#667085]">{r.k}</span>
                    <span className="font-mono">{r.v}</span>
                  </div>
                ))}
              </div>
            ))}
          </Card>
          <Card padding="16px" className={`bg-[#fafbfc] ${!inv.lcStatement.applicable ? "opacity-50" : ""}`}>
            <div className="font-semibold text-[13px] mb-[10px]">Statement of Letter of Credit</div>
            {inv.lcStatement.applicable ? (
              [
                { k: "Percentage", v: inv.lcStatement.pctOfContract },
                { k: "Amount", v: inv.lcStatement.amount },
                { k: "Outstanding L/C", v: inv.lcStatement.outstanding },
              ].map((r) => (
                <div key={r.k} className="flex justify-between text-[12.5px] py-[6px] border-b border-[#f0f1f4] last:border-0">
                  <span className="text-[#667085]">{r.k}</span>
                  <span className="font-mono font-semibold">{r.v}</span>
                </div>
              ))
            ) : (
              <div className="text-[12px] text-[#98a2b3]">Not applicable to this contract.</div>
            )}
          </Card>
          <Card padding="16px" className="bg-[#fafbfc]">
            <div className="font-semibold text-[13px] mb-[10px]">Statement of Release of Retention</div>
            {[
              { k: `Retention (${inv.retentionStatement.pct})`, v: `of ${inv.retentionStatement.ofAmount}` },
              { k: "Retention Held to Date", v: inv.retentionStatement.heldToDate },
              { k: "Release of Retention", v: inv.retentionStatement.released },
              { k: "Net Retention", v: inv.retentionStatement.netRetention },
            ].map((r) => (
              <div key={r.k} className="flex justify-between text-[12.5px] py-[6px] border-b border-[#f0f1f4] last:border-0">
                <span className="text-[#667085]">{r.k}</span>
                <span className="font-mono font-semibold">{r.v}</span>
              </div>
            ))}
          </Card>
        </div>

        <div className="p-[20px] text-[11px] text-[#98a2b3] leading-[1.5] border-t border-[#e6e8ec]">
          Invoice {inv.invoiceNumber} for contract {inv.contractNumber}. Net Amount Payable = Gross(current) + VAT(current) −
          Retention(current) − Advance Tranche 1(current) − Advance Tranche 2(current) − Letter of Credit(current) −
          Equipment Rental(current).
        </div>
      </Card>
    </div>
  );
}
