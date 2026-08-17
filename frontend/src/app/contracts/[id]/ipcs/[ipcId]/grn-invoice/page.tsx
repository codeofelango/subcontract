import { getIpcGrnInvoice } from "@/lib/api";
import { BackLink } from "@/components/ui/BackLink";
import { Card } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import { PrintButton } from "@/components/ui/PrintButton";

export const dynamic = "force-dynamic";

export default async function IpcGrnInvoicePage({ params }: { params: Promise<{ id: string; ipcId: string }> }) {
  const { id, ipcId } = await params;
  const inv = await getIpcGrnInvoice(id, Number(ipcId));

  return (
    <div className="flex flex-col gap-[18px] max-w-[1180px] mx-auto print:max-w-none">
      <BackLink href={`/contracts/${id}`} label="Back to Contract Tracking" />
      <div className="flex items-center justify-between print:hidden">
        <div>
          <div className="text-[16.5px] font-semibold">GRN Invoice — {inv.invoiceNumber}</div>
          <div className="text-[12px] text-[#667085]">
            Percentage completion & billed amounts grounded in Goods Receipt Note (GRN) data, not the vendor&apos;s self-declared claim
          </div>
        </div>
        <PrintButton label="Download / Print GRN Invoice" />
      </div>

      <Card padding="0" className="overflow-hidden">
        <div className="p-[24px] border-b border-[#e6e8ec] flex items-start justify-between gap-[16px] flex-wrap">
          <div className="grid grid-cols-3 gap-x-[24px] gap-y-[10px] flex-1">
            {[
              { label: "Project No.", value: inv.projectNo },
              { label: "Date", value: inv.date },
              { label: "Invoice No.", value: inv.invoiceNumber },
              { label: "Project", value: inv.project },
              { label: "Location", value: inv.location ?? "—" },
              { label: "Contract Number", value: inv.contractNumber },
              { label: "Subcontractor", value: inv.vendor },
            ].map((f) => (
              <div key={f.label}>
                <div className="text-[11px] font-medium text-[#667085] mb-[3px]">{f.label}</div>
                <div className="text-[13px] font-mono">{f.value}</div>
              </div>
            ))}
            <div className="col-span-2">
              <div className="text-[11px] font-medium text-[#667085] mb-[3px]">Period</div>
              <div className="text-[13px] font-mono">
                {inv.periodFrom && inv.periodTo ? `from (${inv.periodFrom}) to (${inv.periodTo})` : "—"}
              </div>
            </div>
          </div>
          <Pill color={inv.status === "Paid" ? "#12805c" : "#3a5bd9"} bg={inv.status === "Paid" ? "#e6f4ee" : "#eef1fd"}>
            {inv.status}
          </Pill>
        </div>

        <div className="p-[24px] border-b border-[#e6e8ec] grid grid-cols-2 gap-[16px]">
          <div className="rounded-[8px] border border-[#e6e8ec] p-[14px]">
            <div className="text-[11px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[8px]">Vendor-Claimed Completion</div>
            <div className="text-[22px] font-bold font-mono">{inv.totals.claimedCompletionPct}</div>
            <div className="text-[12px] text-[#667085] mt-[4px]">Executed to date (self-declared): {inv.totals.claimedGrossToDate}</div>
          </div>
          <div className={`rounded-[8px] border p-[14px] ${inv.totals.varianceFlag ? "border-[#c0362c] bg-[#fbeceb]" : "border-[#e6e8ec]"}`}>
            <div className="text-[11px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[8px]">GRN-Verified Completion</div>
            <div className="text-[22px] font-bold font-mono" style={{ color: inv.totals.varianceFlag ? "#c0362c" : "#101828" }}>
              {inv.totals.grnCompletionPct}
            </div>
            <div className="text-[12px] mt-[4px]" style={{ color: inv.totals.varianceFlag ? "#c0362c" : "#667085" }}>
              Received to date (GRN): {inv.totals.grnGrossToDate}
              {inv.totals.varianceFlag && ` — variance this period ${inv.totals.varianceCurrent}`}
            </div>
          </div>
        </div>

        <div className="p-[24px] border-b border-[#e6e8ec]">
          <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">
            BOQ Line Reconciliation — Claimed vs GRN Received
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12px] whitespace-nowrap">
              <thead>
                <tr className="text-left text-[#667085] text-[10px] uppercase tracking-[.04em] bg-[#fafbfc]">
                  <th className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec]">Code</th>
                  <th className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec]">Description</th>
                  <th className="px-[10px] py-[8px] font-semibold border-b border-[#e6e8ec]">Unit</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-l border-[#e6e8ec]">Rate</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-[#e6e8ec]">Claimed Qty</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-[#e6e8ec]">Claimed Amount</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-l border-[#e6e8ec] bg-[#f4f5f7]">GRN Qty (Prev)</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-[#e6e8ec] bg-[#f4f5f7]">GRN Qty (Curr)</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-[#e6e8ec] bg-[#f4f5f7]">GRN Qty (To Date)</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-[#e6e8ec] bg-[#f4f5f7]">GRN Amount (To Date)</th>
                  <th className="px-[10px] py-[8px] font-semibold text-right border-b border-l border-[#e6e8ec]">Variance</th>
                  <th className="px-[10px] py-[8px] font-semibold text-center border-b border-[#e6e8ec]">Status</th>
                </tr>
              </thead>
              <tbody>
                {inv.lines.map((l) => (
                  <tr key={l.code} className={`border-t border-[#f0f1f4] ${!l.matched ? "bg-[#fbeceb]/40" : "hover:bg-[#fafbfc]"}`}>
                    <td className="px-[10px] py-[9px] font-mono font-medium">{l.code}</td>
                    <td className="px-[10px] py-[9px] whitespace-normal min-w-[180px]">{l.description}</td>
                    <td className="px-[10px] py-[9px] text-[#667085]">{l.uom}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono border-l border-[#f0f1f4]">{l.unitRate}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono">{l.claimedQtyToDate}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono font-semibold">{l.claimedAmountToDate}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono border-l border-[#f0f1f4] bg-[#fafbfc] text-[#667085]">{l.grnQtyPrevious}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono bg-[#fafbfc]">{l.grnQtyCurrent}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono bg-[#fafbfc] font-semibold">{l.grnQtyToDate}</td>
                    <td className="px-[10px] py-[9px] text-right font-mono bg-[#fafbfc] font-semibold">{l.grnAmountToDate}</td>
                    <td
                      className="px-[10px] py-[9px] text-right font-mono font-semibold border-l border-[#f0f1f4]"
                      style={{ color: l.matched ? "#667085" : "#c0362c" }}
                    >
                      {l.variance}
                    </td>
                    <td className="px-[10px] py-[9px] text-center">
                      <Pill color={l.matched ? "#12805c" : "#c0362c"} bg={l.matched ? "#e6f4ee" : "#fbeceb"}>
                        {l.matched ? "Matched" : "Review"}
                      </Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-[10.5px] text-[#98a2b3] mt-[10px] leading-[1.5]">
            Variance flagged when |GRN received amount − claimed amount| ≥ SAR 100 (same threshold used for manpower reconciliation).
            Claimed figures apportion the certified IPC&apos;s gross across BOQ lines pro-rata to contract value share; GRN figures are
            actual receipt events logged independently of the vendor&apos;s claim.
          </div>
        </div>

        <div className="p-[24px] border-b border-[#e6e8ec]">
          <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">GRN-Basis Deductions</div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12.5px]">
              <thead>
                <tr className="text-left text-[10.5px] uppercase tracking-[.04em] text-[#98a2b3]">
                  <th className="text-left font-semibold pb-[8px]">Deduction / Charge</th>
                  <th className="text-right font-semibold pb-[8px]">Current</th>
                  <th className="text-right font-semibold pb-[8px]">To Date</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-[#f0f1f4]">
                  <td className="py-[9px] font-semibold text-[#12805c]">VAT 15%</td>
                  <td className="py-[9px] text-right font-mono text-[#12805c]">+ {inv.totals.vatCurrentTotal}</td>
                  <td className="py-[9px] text-right font-mono font-semibold text-[#12805c]">+ {inv.totals.vatToDateTotal}</td>
                </tr>
                {inv.totals.deductions.map((d) => (
                  <tr key={d.label} className="border-t border-[#f0f1f4]">
                    <td className="py-[9px] text-[#b45309]">{d.label}</td>
                    <td className="py-[9px] text-right font-mono text-[#b45309]">− {d.current}</td>
                    <td className="py-[9px] text-right font-mono font-semibold text-[#b45309]">− {d.toDate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="p-[24px] border-b border-[#e6e8ec]">
          <div className="text-[12px] font-semibold text-[#667085] uppercase tracking-[.05em] mb-[14px]">GRN Payment Summary</div>
          <div className="grid grid-cols-2 gap-[24px]">
            <div className="flex flex-col gap-[2px]">
              {[
                { label: "GRN Gross — Previous", value: inv.totals.grnGrossPrevious, weight: 500, color: "#667085" },
                { label: "GRN Gross — Current", value: inv.totals.grnGrossCurrent, weight: 700, color: "#101828" },
                { label: "GRN Gross — To Date", value: inv.totals.grnGrossToDate, weight: 700, color: "#12805c" },
              ].map((r) => (
                <div key={r.label} className="flex justify-between items-center py-[9px] border-b border-[#f4f5f7] text-[13px]">
                  <span className="text-[#667085]">{r.label}</span>
                  <span className="font-mono" style={{ fontWeight: r.weight, color: r.color }}>{r.value}</span>
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-[2px]">
              {[
                { label: "Less: Previous Net Paid", value: `− ${inv.totals.previousNetPaid}`, color: "#b45309" },
                { label: "Less: Total Deduction (this period)", value: `− ${inv.totals.totalDeductionCurrent}`, color: "#b45309" },
              ].map((r) => (
                <div key={r.label} className="flex justify-between items-center py-[9px] border-b border-[#f4f5f7] text-[13px]">
                  <span className="text-[#667085]">{r.label}</span>
                  <span className="font-mono font-medium" style={{ color: r.color }}>{r.value}</span>
                </div>
              ))}
              <div className="flex justify-between items-center py-[12px] mt-[6px] bg-[#e6f4ee] rounded-[8px] px-[12px]">
                <span className="text-[13px] font-semibold text-[#12805c]">Net Amount Payable (GRN-verified)</span>
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
          GRN Invoice {inv.invoiceNumber} for contract {inv.contractNumber}. Net Amount = GRN Gross(current) + VAT(current) −
          Retention(current) − Advance Tranche 1(current) − Advance Tranche 2(current) − Letter of Credit(current) − Equipment
          Rental(current), computed against Goods Receipt Note quantities rather than the vendor&apos;s self-declared claim.
        </div>
      </Card>
    </div>
  );
}
