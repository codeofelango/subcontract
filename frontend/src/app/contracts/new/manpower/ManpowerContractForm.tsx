"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, Trash2, Users } from "lucide-react";
import { createManpowerContract } from "@/lib/api";
import { Card, CardHeader } from "@/components/ui/Card";
import type { ApprovalStepOut, AttachmentOut, ContractorOption, ManpowerContractDraftResponse, ManpowerPositionLineIn } from "@/lib/types";
import { AttachmentUploader } from "../../AttachmentUploader";
import { ApprovalPreviewCard } from "../../ApprovalPreviewCard";

const fmtMoney = (n: number) => "SAR " + Math.round(n).toLocaleString("en-US");

let tempIdSeq = -1;

const inputCls =
  "w-full border border-[#e6e8ec] rounded-[7px] px-[10px] py-[7px] text-[12.5px] font-mono focus:outline-none focus:border-[#3a5bd9]";
const selectCls =
  "w-full border border-[#e6e8ec] rounded-[7px] px-[10px] py-[8px] text-[14px] font-semibold font-mono bg-white focus:outline-none focus:border-[#3a5bd9]";

type PositionRow = ManpowerPositionLineIn & { rowId: number };

function withCurrentContractor(options: ContractorOption[], contractorNo: string, vendorName: string): ContractorOption[] {
  if (!contractorNo || options.some((o) => o.contractorNo === contractorNo)) return options;
  return [...options, { contractorNo, vendorName }];
}

function blankRow(): PositionRow {
  return {
    rowId: tempIdSeq--,
    categoryPosition: "",
    totalStaff: 0,
    workingHours: 8,
    basicSalary: 0,
    hAllowance: 0,
    tAllowance: 0,
    fAllowance: 0,
    share: 0,
    leaveTreatment: "Deductible",
    absenceTreatment: "Non-Deductible",
  };
}

export function ManpowerContractForm({
  draft,
  approvalPreview,
}: {
  draft: ManpowerContractDraftResponse;
  approvalPreview: ApprovalStepOut[];
}) {
  const router = useRouter();
  const contractorOptions = draft.contractorOptions;
  const [contractorNo, setContractorNo] = useState(contractorOptions[0]?.contractorNo ?? "");
  const [serviceType, setServiceType] = useState(draft.serviceTypeOptions[0] ?? "Manpower");
  const [issueDate, setIssueDate] = useState(new Date().toISOString().slice(0, 10));
  const [expiryTerms, setExpiryTerms] = useState("Automatic renewal");
  const [terminationNotice, setTerminationNotice] = useState("60 Days");
  const [emailAddress, setEmailAddress] = useState("");
  const [paymentTermsNote, setPaymentTermsNote] = useState("5 days from issue invoice");
  const [accountNumber, setAccountNumber] = useState("");
  const [rows, setRows] = useState<PositionRow[]>([blankRow()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draftToken] = useState(() => crypto.randomUUID());
  const [attachments, setAttachments] = useState<AttachmentOut[]>([]);

  const vendorName = withCurrentContractor(contractorOptions, contractorNo, "").find((c) => c.contractorNo === contractorNo)?.vendorName ?? "";

  function updateRow(rowId: number, patch: Partial<PositionRow>) {
    setRows((items) => items.map((r) => (r.rowId === rowId ? { ...r, ...patch } : r)));
  }

  function addRow() {
    setRows((items) => [...items, blankRow()]);
  }

  function removeRow(rowId: number) {
    setRows((items) => items.filter((r) => r.rowId !== rowId));
  }

  function totalCostFor(r: PositionRow): number {
    return r.basicSalary + r.hAllowance + r.tAllowance + r.fAllowance + r.share;
  }

  const contractValue = rows.reduce((sum, r) => sum + totalCostFor(r) * r.totalStaff, 0);

  async function submit() {
    if (attachments.length === 0) {
      setError("At least one supporting document is required — attach one below.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const contract = await createManpowerContract({
        vendorName,
        contractorNo,
        serviceType,
        issueDate,
        expiryTerms,
        terminationNotice,
        emailAddress,
        paymentTermsNote,
        accountNumber,
        positionLines: rows.map((r) => ({
          categoryPosition: r.categoryPosition,
          totalStaff: r.totalStaff,
          workingHours: r.workingHours,
          basicSalary: r.basicSalary,
          hAllowance: r.hAllowance,
          tAllowance: r.tAllowance,
          fAllowance: r.fAllowance,
          share: r.share,
          leaveTreatment: r.leaveTreatment,
          absenceTreatment: r.absenceTreatment,
        })),
        draftToken,
      });
      router.push(`/contracts/${contract.id}/manpower`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit contract");
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-[14px] max-w-[1800px]">
      <Link href="/contracts/new" className="flex items-center gap-[6px] text-[12.5px] font-semibold text-[#475467] hover:text-[#3a5bd9] w-fit">
        <ArrowLeft size={15} strokeWidth={2.2} />
        Back
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-[22px] items-start">
      <div className="flex flex-col gap-[18px]">
        {/* Trigger banner — no Oracle PR for this flow */}
        <div className="bg-[#2c7fb0]/[.06] border border-[#2c7fb0]/[.3] rounded-[10px] px-[18px] py-[14px] flex items-center gap-[13px]">
          <div className="w-[34px] h-[34px] rounded-[8px] bg-[#2c7fb0] flex items-center justify-center flex-none">
            <Users size={17} color="#fff" strokeWidth={2} />
          </div>
          <div className="flex-1">
            <div className="font-semibold text-[13.5px]">Manpower Supply — created directly, no Oracle PR</div>
            <div className="text-[12px] text-[#667085]">
              Rate-based labour by category/position. Reconciled monthly against HCM timesheets and vendor invoices.
            </div>
          </div>
        </div>

        {/* Contract Header */}
        <Card padding="0" className="overflow-hidden">
          <CardHeader>
            <span className="font-semibold text-[14px]">Contract Header</span>
          </CardHeader>
          <div className="p-[18px] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-[18px] gap-y-[15px]">
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contractor Name</label>
              <select className={selectCls + " text-[13px]"} value={contractorNo} onChange={(e) => setContractorNo(e.target.value)}>
                {contractorOptions.map((c) => (
                  <option key={c.contractorNo} value={c.contractorNo}>
                    {c.vendorName}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contractor No.</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[13px] bg-[#fafbfc] text-[#475467] font-mono">
                {contractorNo || "—"}
              </div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contract Type</label>
              <select className={selectCls + " text-[13px]"} value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
                {draft.serviceTypeOptions.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contract Number</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[13px] bg-[#fafbfc] text-[#475467] flex items-center justify-between">
                <span>{draft.contractNumberHint}</span>
                <span className="text-[#c0c5d0] text-[11px]">auto</span>
              </div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contract Issue Date</label>
              <input type="date" className={inputCls} value={issueDate} onChange={(e) => setIssueDate(e.target.value)} />
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Expiry / Renewal Terms</label>
              <input
                className={inputCls + " font-sans"}
                placeholder="e.g. Automatic renewal, or a fixed date"
                value={expiryTerms}
                onChange={(e) => setExpiryTerms(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Period of Termination Notice</label>
              <input className={inputCls + " font-sans"} value={terminationNotice} onChange={(e) => setTerminationNotice(e.target.value)} />
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Email Address</label>
              <input
                type="email"
                className={inputCls + " font-sans"}
                value={emailAddress}
                onChange={(e) => setEmailAddress(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Payment Terms</label>
              <input
                className={inputCls + " font-sans"}
                placeholder="e.g. 5 days from issue invoice"
                value={paymentTermsNote}
                onChange={(e) => setPaymentTermsNote(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Account Number (IBAN)</label>
              <input className={inputCls} value={accountNumber} onChange={(e) => setAccountNumber(e.target.value)} />
            </div>
          </div>
        </Card>

        {/* Position rate card */}
        <Card padding="0" className="overflow-hidden">
          <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] flex items-center justify-between gap-[12px]">
            <span className="font-semibold text-[14px]">Position Rate Card</span>
            <button
              type="button"
              onClick={addRow}
              className="flex items-center gap-[5px] text-[12px] text-[#3a5bd9] font-semibold cursor-pointer"
            >
              <Plus size={13} strokeWidth={2.5} />
              Add row
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12.5px] min-w-[960px]">
              <thead>
                <tr className="text-left text-[#667085] text-[10.5px] uppercase tracking-[.04em] bg-[#fafbfc]">
                  <th className="px-[10px] py-[9px] font-semibold">Category Position</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Total Staff</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Working Hrs</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Basic Salary</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">H Allow.</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">T Allow.</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">F Allow.</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Share</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Total Cost</th>
                  <th className="px-[10px] py-[9px] font-semibold">Leave Treatment</th>
                  <th className="px-[10px] py-[9px] font-semibold">Absence Treatment</th>
                  <th className="px-[10px] py-[9px] font-semibold w-[30px]" />
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.rowId} className="border-t border-[#f0f1f4] align-top">
                    <td className="px-[10px] py-[8px] min-w-[140px]">
                      <input
                        className={inputCls + " font-sans"}
                        value={r.categoryPosition}
                        onChange={(e) => updateRow(r.rowId, { categoryPosition: e.target.value })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[80px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={r.totalStaff}
                        onChange={(e) => updateRow(r.rowId, { totalStaff: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[80px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={r.workingHours}
                        onChange={(e) => updateRow(r.rowId, { workingHours: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[100px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={r.basicSalary}
                        onChange={(e) => updateRow(r.rowId, { basicSalary: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[90px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={r.hAllowance}
                        onChange={(e) => updateRow(r.rowId, { hAllowance: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[90px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={r.tAllowance}
                        onChange={(e) => updateRow(r.rowId, { tAllowance: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[90px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={r.fAllowance}
                        onChange={(e) => updateRow(r.rowId, { fAllowance: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[90px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={r.share}
                        onChange={(e) => updateRow(r.rowId, { share: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[10px] text-right font-mono font-semibold whitespace-nowrap">
                      {fmtMoney(totalCostFor(r))}
                    </td>
                    <td className="px-[10px] py-[8px] w-[130px]">
                      <select
                        className={inputCls + " font-sans"}
                        value={r.leaveTreatment}
                        onChange={(e) => updateRow(r.rowId, { leaveTreatment: e.target.value })}
                      >
                        <option value="Deductible">Deductible</option>
                        <option value="Non-Deductible">Non-Deductible</option>
                      </select>
                    </td>
                    <td className="px-[10px] py-[8px] w-[130px]">
                      <select
                        className={inputCls + " font-sans"}
                        value={r.absenceTreatment}
                        onChange={(e) => updateRow(r.rowId, { absenceTreatment: e.target.value })}
                      >
                        <option value="Deductible">Deductible</option>
                        <option value="Non-Deductible">Non-Deductible</option>
                      </select>
                    </td>
                    <td className="px-[10px] py-[10px] text-center">
                      <button type="button" onClick={() => removeRow(r.rowId)} className="text-[#98a2b3] hover:text-[#c0362c]">
                        <Trash2 size={14} strokeWidth={2} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card>
          <div className="font-semibold text-[13.5px] mb-[10px]">Attachments</div>
          <div className="text-[11px] text-[#98a2b3] mb-[10px]">At least one supporting document is required before submitting.</div>
          <AttachmentUploader draftToken={draftToken} files={attachments} onChange={setAttachments} />
        </Card>
      </div>

      {/* Summary rail */}
      <div className="lg:sticky lg:top-[90px] flex flex-col gap-[16px]">
        <Card>
          <div className="font-semibold text-[14px] mb-[14px]">Contract Summary</div>
          {[
            { label: "Contract Value", value: fmtMoney(contractValue), weight: 700, color: "#101828" },
            { label: "Contract Budget", value: fmtMoney(contractValue), weight: 500, color: "#475467" },
            { label: "Positions", value: String(rows.length), weight: 500, color: "#667085" },
            { label: "Total Staff", value: String(rows.reduce((s, r) => s + r.totalStaff, 0)), weight: 500, color: "#667085" },
          ].map((r) => (
            <div key={r.label} className="py-[8px] border-b border-[#f4f5f7] text-[13px]">
              <div className="flex justify-between gap-[10px]">
                <span className="text-[#667085]">{r.label}</span>
                <span className="font-mono text-right" style={{ fontWeight: r.weight, color: r.color }}>
                  {r.value}
                </span>
              </div>
            </div>
          ))}
        </Card>
        <ApprovalPreviewCard steps={approvalPreview} />
        <div className="flex flex-col gap-[10px]">
          {error && <div className="text-[12px] text-[#c0362c]">{error}</div>}
          <button
            type="button"
            onClick={submit}
            disabled={submitting}
            className="bg-[#3a5bd9] rounded-[8px] p-[11px] text-[13px] font-semibold text-white hover:brightness-[1.08] disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit for Approval"}
          </button>
        </div>
      </div>
      </div>
    </div>
  );
}
