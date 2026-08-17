import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export function BackLink({
  href,
  label = "Back",
  className = "",
}: {
  href: string;
  label?: string;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={`print:hidden flex items-center gap-[6px] text-[12.5px] font-semibold text-[#475467] hover:text-[#3a5bd9] w-fit ${className}`}
    >
      <ArrowLeft size={15} strokeWidth={2.2} />
      {label}
    </Link>
  );
}
