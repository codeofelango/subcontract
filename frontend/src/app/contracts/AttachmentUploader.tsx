"use client";

import { useRef, useState } from "react";
import { FileText, Upload, X } from "lucide-react";
import { deleteAttachment, uploadAttachment } from "@/lib/api";
import type { AttachmentOut } from "@/lib/types";

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AttachmentUploader({
  draftToken,
  files,
  onChange,
}: {
  draftToken: string;
  files: AttachmentOut[];
  onChange: (files: AttachmentOut[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function uploadFiles(fileList: FileList | File[]) {
    setUploading(true);
    setError(null);
    try {
      const uploaded: AttachmentOut[] = [];
      for (const file of Array.from(fileList)) {
        uploaded.push(await uploadAttachment(draftToken, file));
      }
      onChange([...files, ...uploaded]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to upload file");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function remove(id: number) {
    await deleteAttachment(id);
    onChange(files.filter((f) => f.id !== id));
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={
          "flex items-center gap-[8px] justify-center rounded-[7px] border border-dashed px-[12px] py-[10px] text-[12px] cursor-pointer transition-colors " +
          (dragOver ? "border-[#3a5bd9] bg-[#3a5bd9]/[.06] text-[#3a5bd9]" : "border-[#cfd4dc] text-[#667085] hover:border-[#3a5bd9] hover:text-[#3a5bd9]")
        }
      >
        <Upload size={14} strokeWidth={2} />
        {uploading ? "Uploading…" : "Click or drop documents to attach"}
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && uploadFiles(e.target.files)}
        />
      </div>

      {error && <div className="text-[11px] text-[#c0362c] mt-[6px]">{error}</div>}

      {files.length > 0 && (
        <div className="flex flex-col gap-[6px] mt-[10px]">
          {files.map((f) => (
            <div key={f.id} className="flex items-center gap-[8px] text-[12px] bg-[#fafbfc] border border-[#f0f1f4] rounded-[6px] px-[9px] py-[6px]">
              <FileText size={13} color="#98a2b3" strokeWidth={2} className="flex-none" />
              <span className="flex-1 min-w-0 truncate">{f.filename}</span>
              <span className="text-[#98a2b3] flex-none">{fmtSize(f.sizeBytes)}</span>
              <button type="button" onClick={() => remove(f.id)} className="text-[#98a2b3] hover:text-[#c0362c] flex-none">
                <X size={13} strokeWidth={2.3} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
