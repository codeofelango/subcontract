import { getApprovalPreview, getManpowerContractDraft } from "@/lib/api";
import { ManpowerContractForm } from "./ManpowerContractForm";

export const dynamic = "force-dynamic";

export default async function NewManpowerContractPage() {
  const [draft, approvalPreview] = await Promise.all([getManpowerContractDraft(), getApprovalPreview("contract_manpower")]);
  return <ManpowerContractForm draft={draft} approvalPreview={approvalPreview} />;
}
