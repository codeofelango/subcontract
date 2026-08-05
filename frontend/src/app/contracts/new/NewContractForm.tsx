"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, CircleCheck, Plus, Trash2, X } from "lucide-react";
import { createContract } from "@/lib/api";
import { Card, CardHeader } from "@/components/ui/Card";
import { Pill } from "@/components/ui/Pill";
import type { ApprovalStepOut, AttachmentOut, ContractorOption, DraftLineItem, NewContractDraftResponse, PaymentTermOption } from "@/lib/types";
import { AttachmentUploader } from "../AttachmentUploader";
import { ApprovalPreviewCard } from "../ApprovalPreviewCard";

const fmtMoney = (n: number) => "SAR " + Math.round(n).toLocaleString("en-US");

let tempIdSeq = -1;

const inputCls =
  "w-full border border-[#e6e8ec] rounded-[7px] px-[10px] py-[7px] text-[12.5px] font-mono focus:outline-none focus:border-[#3a5bd9]";
const selectCls =
  "w-full border border-[#e6e8ec] rounded-[7px] px-[10px] py-[8px] text-[14px] font-semibold font-mono bg-white focus:outline-none focus:border-[#3a5bd9]";

// Maintained hour bands for Response/Resolution SLA tags - an internal convention, not an Oracle
// master list, so this stays a small local constant rather than a backend-fed lookup.
const SLA_HOUR_OPTIONS = ["1", "2", "4", "8", "12", "24", "48", "72"];
const SLA_METRICS = ["Response", "Resolution"] as const;

// Guarantees the PR's current value is selectable even if it falls outside the Oracle master list.
function withCurrent(options: PaymentTermOption[], current: number): PaymentTermOption[] {
  if (options.some((o) => o.value === current)) return options;
  return [...options, { value: current, label: String(current) }].sort((a, b) => a.value - b.value);
}

function withCurrentContractor(options: ContractorOption[], contractorNo: string, vendorName: string): ContractorOption[] {
  if (options.some((o) => o.contractorNo === contractorNo)) return options;
  return [...options, { contractorNo, vendorName }];
}

export function NewContractForm({ draft, approvalPreview }: { draft: NewContractDraftResponse; approvalPreview: ApprovalStepOut[] }) {
  const router = useRouter();
  const [lineItems, setLineItems] = useState<DraftLineItem[]>(draft.lineItems);
  const [retentionPct, setRetentionPct] = useState(draft.retentionPct);
  const [advancePct, setAdvancePct] = useState(draft.advancePct);
  const [payableTermsDays, setPayableTermsDays] = useState(draft.payableTermsDays);
  const [contractorNo, setContractorNo] = useState(draft.contractorNo);
  const [serviceType, setServiceType] = useState(draft.serviceType);
  const [tagDraft, setTagDraft] = useState<Record<number, string>>({});
  const [tagMetric, setTagMetric] = useState<Record<number, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draftToken] = useState(() => crypto.randomUUID());
  const [attachments, setAttachments] = useState<AttachmentOut[]>([]);

  // Project comes from the triggering Oracle PR only - not user-selectable.
  const projectNo = draft.projectNo;
  const projectName = draft.projectName;

  const serviceTypeOptions = draft.serviceTypeOptions.includes(draft.serviceType)
    ? draft.serviceTypeOptions
    : [draft.serviceType, ...draft.serviceTypeOptions];
  const contractorOptions = withCurrentContractor(draft.contractorOptions, draft.contractorNo, draft.vendorName);
  const vendorName = contractorOptions.find((c) => c.contractorNo === contractorNo)?.vendorName ?? draft.vendorName;

  const contractValue = lineItems.reduce((sum, li) => sum + li.qty * li.unitRate, 0);
  const contractBudget = lineItems.reduce((sum, li) => sum + li.budget, 0);
  const advanceAmount = (contractValue * advancePct) / 100;
  const retentionAmount = (contractValue * retentionPct) / 100;
  const allSlaTags = Array.from(new Set(lineItems.flatMap((li) => li.slaTags)));

  function updateLine(id: number, patch: Partial<DraftLineItem>) {
    setLineItems((items) => items.map((li) => (li.id === id ? { ...li, ...patch } : li)));
  }

  // Adds a blank row - the user then picks its Oracle PR Line from the dropdown in that row.
  function addLine() {
    setLineItems((items) => [
      ...items,
      { id: tempIdSeq--, code: "", prLineRef: "", description: "", qty: 0, uom: "", unitRate: 0, budget: 0, slaTags: [] },
    ]);
  }

  function removeLine(id: number) {
    setLineItems((items) => items.filter((li) => li.id !== id));
  }

  // Options available to a given row's PR-line dropdown: any catalog line not already used by
  // ANOTHER row, plus whichever line this row currently holds (so it stays selectable) - the
  // same Oracle PR line must not be picked on more than one row.
  function catalogOptionsFor(rowId: number): DraftLineItem[] {
    const usedByOthers = new Set(lineItems.filter((li) => li.id !== rowId).map((li) => li.prLineRef));
    return draft.prLineCatalog.filter((c) => !usedByOthers.has(c.prLineRef));
  }

  // Selecting an Oracle PR Line fills in the rest of the row - qty/uom/rate/budget/SLA all come from that line.
  function selectPrLine(rowId: number, catalogId: number) {
    const source = draft.prLineCatalog.find((l) => l.id === catalogId);
    if (!source) return;
    updateLine(rowId, {
      code: source.code,
      prLineRef: source.prLineRef,
      description: source.description,
      qty: source.qty,
      uom: source.uom,
      unitRate: source.unitRate,
      budget: source.budget,
      slaTags: source.slaTags,
    });
  }

  function pushTag(id: number, value: string) {
    const li = lineItems.find((l) => l.id === id);
    if (!li || !value || li.slaTags.includes(value)) return;
    updateLine(id, { slaTags: [...li.slaTags, value] });
  }

  function addTag(id: number) {
    const value = (tagDraft[id] ?? "").trim();
    if (!value) return;
    pushTag(id, value);
    setTagDraft((d) => ({ ...d, [id]: "" }));
  }

  // Response/Resolution are picked, not typed: choosing an hour band composes the label
  // (e.g. "Response ≤ 4h") immediately and resets the metric picker for the next tag.
  function addHourTag(id: number, metric: string, hours: string) {
    pushTag(id, `${metric} ≤ ${hours}h`);
    setTagMetric((d) => ({ ...d, [id]: "" }));
  }

  function removeTag(id: number, tag: string) {
    const li = lineItems.find((l) => l.id === id);
    if (!li) return;
    updateLine(id, { slaTags: li.slaTags.filter((t) => t !== tag) });
  }

  async function submit() {
    if (attachments.length === 0) {
      setError("At least one supporting document is required — attach one below.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const contract = await createContract({
        vendorName,
        contractorNo,
        contractType: draft.contractType,
        serviceType,
        projectName,
        projectNo,
        durationMonths: draft.durationMonths,
        contractValue,
        contractBudget,
        retentionPct,
        advancePct,
        advanceAmount,
        payableTermsDays,
        sourcePr: draft.sourcePr,
        lineItems: lineItems.map((li) => ({
          code: li.code,
          prLineRef: li.prLineRef,
          description: li.description,
          qty: li.qty,
          uom: li.uom,
          unitRate: li.unitRate,
          budget: li.budget,
          slaTags: li.slaTags,
        })),
        draftToken,
      });
      router.push(`/contracts/${contract.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit contract");
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-[14px] max-w-[1800px]">
      <div className="flex items-center gap-[14px]">
        <Link href="/contracts/new/work" className="flex items-center gap-[6px] text-[12.5px] font-semibold text-[#475467] hover:text-[#3a5bd9]">
          <ArrowLeft size={15} strokeWidth={2.2} />
          Back
        </Link>
        <Link href="/contracts/new" className="text-[12.5px] text-[#98a2b3] hover:text-[#3a5bd9]">
          Change contract type
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-[22px] items-start">
        <div className="flex flex-col gap-[18px]">
          {/* Oracle PR trigger banner */}
          <div className="bg-[#3a5bd9]/[.06] border border-[#3a5bd9]/[.3] rounded-[10px] px-[18px] py-[14px] flex items-center gap-[13px] flex-wrap">
            <div className="w-[34px] h-[34px] rounded-[8px] bg-[#3a5bd9] flex items-center justify-center flex-none">
              <CircleCheck size={17} color="#fff" strokeWidth={2} />
            </div>
            <div className="flex-1 min-w-[200px]">
              <div className="font-semibold text-[13.5px]">
                Triggered by approved Oracle PR — <span className="font-mono text-[#3a5bd9]">{draft.sourcePr}</span>
              </div>
              <div className="text-[12px] text-[#667085]">
                PR lines flow in from Oracle and populate the BOQ below. On approval a PO is auto-created back in Oracle.
              </div>
            </div>
            <Link
              href="/contracts/new/work"
              className="text-[11.5px] font-semibold text-[#3a5bd9] border border-[#3a5bd9]/[.3] rounded-[7px] px-[9px] py-[5px] hover:bg-[#3a5bd9]/[.06]"
            >
              Change PR
            </Link>
            <Pill color="#12805c" bg="#e6f4ee">
              PR Approved
            </Pill>
          </div>

          {/* Line Items — entered first; Contract Header below derives its value/budget from this */}
        <Card padding="0" className="overflow-hidden">
          <div className="px-[18px] py-[14px] border-b border-[#e6e8ec] flex items-center justify-between gap-[12px]">
            <span className="font-semibold text-[14px]">Line Items (BOQ)</span>
            <button
              type="button"
              onClick={addLine}
              className="flex items-center gap-[5px] text-[12px] text-[#3a5bd9] font-semibold cursor-pointer"
            >
              <Plus size={13} strokeWidth={2.5} />
              Add row
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12.5px] min-w-[860px]">
              <thead>
                <tr className="text-left text-[#667085] text-[10.5px] uppercase tracking-[.04em] bg-[#fafbfc]">
                  <th className="px-[10px] py-[9px] font-semibold">Code</th>
                  <th className="px-[10px] py-[9px] font-semibold">Oracle PR Line</th>
                  <th className="px-[10px] py-[9px] font-semibold">Description</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Qty</th>
                  <th className="px-[10px] py-[9px] font-semibold">UoM</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Unit Rate</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Budget</th>
                  <th className="px-[10px] py-[9px] font-semibold text-right">Total</th>
                  <th className="px-[10px] py-[9px] font-semibold">SLA Package</th>
                  <th className="px-[10px] py-[9px] font-semibold w-[30px]" />
                </tr>
              </thead>
              <tbody>
                {lineItems.map((li) => (
                  <tr key={li.id} className="border-t border-[#f0f1f4] align-top">
                    <td className="px-[10px] py-[8px]">
                      <input className={inputCls} value={li.code} onChange={(e) => updateLine(li.id, { code: e.target.value })} />
                    </td>
                    <td className="px-[10px] py-[8px] min-w-[170px]">
                      <select
                        className={inputCls + " text-[11.5px] text-[#3a5bd9]"}
                        value={draft.prLineCatalog.find((c) => c.prLineRef === li.prLineRef)?.id ?? ""}
                        onChange={(e) => selectPrLine(li.id, Number(e.target.value))}
                      >
                        <option value="" disabled>
                          — select PR line —
                        </option>
                        {catalogOptionsFor(li.id).map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.prLineRef}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-[10px] py-[8px] min-w-[180px]">
                      <input
                        className={inputCls + " font-sans"}
                        value={li.description}
                        onChange={(e) => updateLine(li.id, { description: e.target.value })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[70px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={li.qty}
                        onChange={(e) => updateLine(li.id, { qty: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[80px]">
                      <input
                        className={inputCls + " font-sans text-[#667085]"}
                        value={li.uom}
                        onChange={(e) => updateLine(li.id, { uom: e.target.value })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[110px]">
                      <input
                        type="number"
                        className={inputCls + " text-right"}
                        value={li.unitRate}
                        onChange={(e) => updateLine(li.id, { unitRate: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[8px] w-[110px]">
                      <input
                        type="number"
                        className={inputCls + " text-right text-[#667085]"}
                        value={li.budget}
                        onChange={(e) => updateLine(li.id, { budget: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-[10px] py-[10px] text-right font-mono font-semibold whitespace-nowrap">
                      {fmtMoney(li.qty * li.unitRate)}
                    </td>
                    <td className="px-[10px] py-[8px] min-w-[190px]">
                      <div className="flex flex-wrap gap-[5px] mb-[5px]">
                        {li.slaTags.map((tag) => (
                          <span
                            key={tag}
                            className="flex items-center gap-[4px] text-[10.5px] font-medium px-[8px] py-[3px] rounded-[20px] bg-[#3a5bd9]/[.08] text-[#3a5bd9]"
                          >
                            {tag}
                            <button type="button" onClick={() => removeTag(li.id, tag)} className="hover:opacity-60">
                              <X size={10} strokeWidth={2.5} />
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex flex-col gap-[4px]">
                        <select
                          className="w-full border border-dashed border-[#e6e8ec] rounded-[6px] px-[6px] py-[4px] text-[11px] bg-white focus:outline-none focus:border-[#3a5bd9]"
                          value={tagMetric[li.id] ?? ""}
                          onChange={(e) => setTagMetric((d) => ({ ...d, [li.id]: e.target.value }))}
                        >
                          <option value="">+ add SLA tag…</option>
                          {SLA_METRICS.map((m) => (
                            <option key={m} value={m}>
                              {m} (hours)
                            </option>
                          ))}
                          <option value="custom">Custom…</option>
                        </select>
                        {tagMetric[li.id] && tagMetric[li.id] !== "custom" && (
                          <select
                            autoFocus
                            className="w-full border border-[#e6e8ec] rounded-[6px] px-[6px] py-[4px] text-[11px] text-[#3a5bd9] bg-white focus:outline-none focus:border-[#3a5bd9]"
                            value=""
                            onChange={(e) => addHourTag(li.id, tagMetric[li.id], e.target.value)}
                          >
                            <option value="" disabled>
                              — select hours —
                            </option>
                            {SLA_HOUR_OPTIONS.map((h) => (
                              <option key={h} value={h}>
                                ≤ {h}h
                              </option>
                            ))}
                          </select>
                        )}
                        {tagMetric[li.id] === "custom" && (
                          <input
                            autoFocus
                            placeholder="Custom tag, Enter"
                            className="w-full border border-dashed border-[#e6e8ec] rounded-[6px] px-[8px] py-[4px] text-[11px] focus:outline-none focus:border-[#3a5bd9]"
                            value={tagDraft[li.id] ?? ""}
                            onChange={(e) => setTagDraft((d) => ({ ...d, [li.id]: e.target.value }))}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                e.preventDefault();
                                addTag(li.id);
                                setTagMetric((d) => ({ ...d, [li.id]: "" }));
                              }
                            }}
                          />
                        )}
                      </div>
                    </td>
                    <td className="px-[10px] py-[10px] text-center">
                      <button type="button" onClick={() => removeLine(li.id)} className="text-[#98a2b3] hover:text-[#c0362c]">
                        <Trash2 size={14} strokeWidth={2} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Payment Terms — comes after the BOQ, still ahead of the header it feeds into */}
        <Card padding="0" className="overflow-hidden">
          <CardHeader className="justify-start">
            <span className="font-semibold text-[14px]">Payment Terms &amp; Securities</span>
            <span className="text-[11px] text-[#98a2b3] ml-auto">From Oracle PR — editable before submission</span>
          </CardHeader>
          <div className="p-[18px] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[16px]">
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Retention %</label>
              <select className={selectCls} value={retentionPct} onChange={(e) => setRetentionPct(Number(e.target.value))}>
                {withCurrent(draft.retentionOptions, retentionPct).map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <div className="text-[11px] text-[#98a2b3] mt-[5px]">Held per IPC, released on handover</div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Advance Payment %</label>
              <select className={selectCls} value={advancePct} onChange={(e) => setAdvancePct(Number(e.target.value))}>
                {withCurrent(draft.advanceOptions, advancePct).map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <div className="text-[11px] text-[#98a2b3] mt-[5px]">Down payment on mobilisation</div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Advance Amount</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[14px] font-semibold font-mono bg-[#fafbfc] text-[#475467]">
                {fmtMoney(advanceAmount)}
              </div>
              <div className="text-[11px] text-[#98a2b3] mt-[5px]">Recovered pro-rata to progress</div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Payable Terms</label>
              <select className={selectCls} value={payableTermsDays} onChange={(e) => setPayableTermsDays(Number(e.target.value))}>
                {withCurrent(draft.payableTermsOptions, payableTermsDays).map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <div className="text-[11px] text-[#98a2b3] mt-[5px]">From certified IPC date</div>
            </div>
          </div>
        </Card>

        {/* Contract Header — comes last: Contractor/Project pulled live from Oracle master lists, Value/Budget from the BOQ above */}
        <Card padding="0" className="overflow-hidden">
          <CardHeader>
            <span className="font-semibold text-[14px]">Contract Header</span>
            <span className="text-[11px] text-[#98a2b3]">Contractor &amp; Project from Oracle — Value &amp; Budget from BOQ above</span>
          </CardHeader>
          <div className="p-[18px] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-[18px] gap-y-[15px]">
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contractor Name</label>
              <select
                className={selectCls + " text-[13px]"}
                value={contractorNo}
                onChange={(e) => setContractorNo(e.target.value)}
              >
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
                {contractorNo}
              </div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contract Type</label>
              <select className={selectCls + " text-[13px]"} value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
                {serviceTypeOptions.map((t) => (
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
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contract Duration</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[13px]">{draft.durationMonths} months</div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Project Name</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[13px] bg-[#fafbfc] text-[#475467] flex items-center justify-between">
                <span>{projectName}</span>
                <span className="text-[#c0c5d0] text-[11px]">from PR</span>
              </div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Project Number</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[13px] bg-[#fafbfc] text-[#475467] font-mono">
                {projectNo}
              </div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contract Value</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[13px] bg-[#fafbfc] text-[#475467] flex items-center justify-between">
                <span>{fmtMoney(contractValue)}</span>
                <span className="text-[#c0c5d0] text-[11px]">from BOQ</span>
              </div>
            </div>
            <div>
              <label className="block text-[11.5px] font-medium text-[#667085] mb-[6px]">Contract Budget</label>
              <div className="border border-[#e6e8ec] rounded-[7px] px-[11px] py-[9px] text-[13px] bg-[#fafbfc] text-[#475467] flex items-center justify-between">
                <span>{fmtMoney(contractBudget)}</span>
                <span className="text-[#c0c5d0] text-[11px]">from BOQ</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Summary rail */}
      <div className="lg:sticky lg:top-[90px] flex flex-col gap-[16px]">
        <Card>
          <div className="font-semibold text-[14px] mb-[14px]">Contract Summary</div>
          {[
            { label: "Contract Value", value: fmtMoney(contractValue), weight: 700, color: "#101828" },
            { label: "Contract Budget", value: fmtMoney(contractBudget), weight: 500, color: "#475467" },
            { label: "Estimated Saving", value: fmtMoney(contractBudget - contractValue), weight: 600, color: "#12805c" },
            { label: `Retention (${retentionPct}%)`, value: fmtMoney(retentionAmount), weight: 500, color: "#b45309" },
            { label: `Advance (${advancePct}%)`, value: fmtMoney(advanceAmount), weight: 500, color: "#2c7fb0" },
            {
              label: "Source PR (Oracle)",
              value: draft.sourcePr,
              weight: 500,
              color: "#3a5bd9",
              cap: "Purchase Requisition approved in Oracle — the trigger that starts this contract.",
            },
            {
              label: "Oracle PO",
              value: "Auto-created on approval",
              weight: 500,
              color: "#98a2b3",
              cap: "Purchase Order is generated automatically in Oracle once the contract is approved.",
            },
          ].map((r) => (
            <div key={r.label} className="py-[8px] border-b border-[#f4f5f7] text-[13px]">
              <div className="flex justify-between gap-[10px]">
                <span className="text-[#667085]">{r.label}</span>
                <span className="font-mono text-right" style={{ fontWeight: r.weight, color: r.color }}>
                  {r.value}
                </span>
              </div>
              {r.cap && <div className="text-[11px] leading-[1.4] text-[#98a2b3] mt-[4px]">{r.cap}</div>}
            </div>
          ))}
        </Card>
        <ApprovalPreviewCard steps={approvalPreview} />
        <Card>
          <div className="font-semibold text-[13.5px] mb-[10px]">SLA Package</div>
          <div className="flex flex-wrap gap-[7px]">
            {allSlaTags.length === 0 && <span className="text-[12px] text-[#98a2b3]">No SLA tags added to any line item yet.</span>}
            {allSlaTags.map((t) => (
              <span key={t} className="text-[11.5px] font-medium px-[10px] py-[5px] rounded-[20px] bg-[#3a5bd9]/[.08] text-[#3a5bd9]">
                {t}
              </span>
            ))}
          </div>
          <div className="text-[11px] text-[#98a2b3] mt-[8px]">Aggregated from each line item's SLA package above — edit per line.</div>
        </Card>
        <Card>
          <div className="font-semibold text-[13.5px] mb-[10px]">Attachments</div>
          <div className="text-[11px] text-[#98a2b3] mb-[10px]">At least one supporting document is required before submitting.</div>
          <AttachmentUploader draftToken={draftToken} files={attachments} onChange={setAttachments} />
        </Card>
        <div className="flex flex-col gap-[10px]">
          {error && <div className="text-[12px] text-[#c0362c]">{error}</div>}
          <div className="flex gap-[10px]">
            <button
              type="button"
              disabled={submitting}
              className="flex-1 bg-white border border-[#e6e8ec] rounded-[8px] p-[11px] text-[13px] font-semibold text-[#475467] disabled:opacity-50"
            >
              Save Draft
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={submitting}
              className="flex-1 bg-[#3a5bd9] rounded-[8px] p-[11px] text-[13px] font-semibold text-white hover:brightness-[1.08] disabled:opacity-50"
            >
              {submitting ? "Submitting…" : "Submit for Approval"}
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
