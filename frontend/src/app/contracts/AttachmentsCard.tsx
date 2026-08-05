import { FileDown, FileText } from "lucide-react";
import { attachmentDownloadUrl } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import type { AttachmentOut } from "@/lib/types";

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AttachmentsCard({ attachments }: { attachments: AttachmentOut[] }) {
  if (attachments.length === 0) return null;

  return (
    <Card>
      <div className="font-semibold text-[13.5px] mb-[10px]">Attachments</div>
      <div className="flex flex-col gap-[6px]">
        {attachments.map((a) => (
          <a
            key={a.id}
            href={attachmentDownloadUrl(a.id)}
            className="flex items-center gap-[8px] text-[12px] bg-[#fafbfc] border border-[#f0f1f4] rounded-[6px] px-[9px] py-[6px] hover:border-[#3a5bd9]"
          >
            <FileText size={13} color="#98a2b3" strokeWidth={2} className="flex-none" />
            <span className="flex-1 min-w-0 truncate text-[#101828]">{a.filename}</span>
            <span className="text-[#98a2b3] flex-none">{fmtSize(a.sizeBytes)}</span>
            <FileDown size={13} color="#3a5bd9" strokeWidth={2} className="flex-none" />
          </a>
        ))}
      </div>
    </Card>
  );
}
