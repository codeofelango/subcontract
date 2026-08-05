import type { Metadata } from "next";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { SidebarProvider } from "@/components/layout/SidebarContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "Subcontract Management Module",
  description: "Vendor & manpower control — contracts, payments, reconciliation, change orders, penalties, evaluations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <SidebarProvider>
          <div className="flex min-h-screen w-full">
            <Sidebar />
            <div className="flex-1 min-w-0 flex flex-col">
              <Header />
              <main className="flex-1 overflow-y-auto overflow-x-hidden px-[14px] pt-[14px] pb-[40px] lg:px-[26px] lg:pt-[26px] lg:pb-[60px] bg-[#f4f5f7] print:p-0 print:bg-white">
                {children}
              </main>
            </div>
          </div>
        </SidebarProvider>
      </body>
    </html>
  );
}
