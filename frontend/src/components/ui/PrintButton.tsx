"use client";

import { Download } from "lucide-react";

export function PrintButton({ label = "Download / Print" }: { label?: string }) {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="print:hidden flex items-center gap-[7px] bg-[#3a5bd9] text-white rounded-[8px] px-[14px] py-[9px] text-[13px] font-semibold hover:brightness-[1.08]"
    >
      <Download size={15} strokeWidth={2.2} />
      {label}
    </button>
  );
}
