"use client";

import Link from "next/link";
import { Boxes, Users } from "lucide-react";
import { useSession } from "next-auth/react";
import { BackLink } from "@/components/ui/BackLink";
import { Card } from "@/components/ui/Card";
import type { AccessRole } from "@/lib/types";

export default function NewContractChooserPage() {
  const { data: session } = useSession();
  const role = (session?.user?.role ?? null) as AccessRole;
  const showWork = role !== "hr_requester";
  const showManpower = role !== "procurement_requester";

  return (
    <div className="max-w-[880px]">
      <BackLink href="/contracts" label="Back to Contracts" className="mb-[14px]" />
      <div className="text-[13px] text-[#667085] mb-[18px]">
        Choose the contract type. Scope/Works and Manpower Supply are separate flows with different source data,
        fields, and approval routing.
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-[16px]">
        {showWork && (
          <Link href="/contracts/new/work">
            <Card className="h-full hover:border-[#3a5bd9] transition-colors cursor-pointer">
              <div className="w-[38px] h-[38px] rounded-[9px] bg-[#3a5bd9]/[.1] flex items-center justify-center mb-[14px]">
                <Boxes size={19} color="#3a5bd9" strokeWidth={2} />
              </div>
              <div className="font-semibold text-[15px] mb-[6px]">Scope / Works Contract</div>
              <div className="text-[12.5px] text-[#667085] leading-[1.5]">
                Triggered by an approved Oracle PR. Lump-sum or measured works, BOQ line items, progress-billed via
                IPC. Retention &amp; advance apply.
              </div>
            </Card>
          </Link>
        )}
        {showManpower && (
          <Link href="/contracts/new/manpower">
            <Card className="h-full hover:border-[#3a5bd9] transition-colors cursor-pointer">
              <div className="w-[38px] h-[38px] rounded-[9px] bg-[#2c7fb0]/[.1] flex items-center justify-center mb-[14px]">
                <Users size={19} color="#2c7fb0" strokeWidth={2} />
              </div>
              <div className="font-semibold text-[15px] mb-[6px]">Manpower Supply</div>
              <div className="text-[12.5px] text-[#667085] leading-[1.5]">
                Created directly, without an Oracle PR. Rate-based labour by category/position, reconciled monthly
                against HCM timesheets and vendor invoices.
              </div>
            </Card>
          </Link>
        )}
      </div>
    </div>
  );
}
