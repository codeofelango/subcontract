import { getEvaluation } from "@/lib/api";
import { EvaluationsClient } from "./EvaluationsClient";

export const dynamic = "force-dynamic";

export default async function EvaluationsPage() {
  const initial = await getEvaluation("jr");
  return <EvaluationsClient initial={initial} />;
}
