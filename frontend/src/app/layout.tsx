import type { Metadata } from "next";

import { Header } from "@/components/Header";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "InstaMed",
  description: "Order medicines from the pharmacy that serves your pincode.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col bg-slate-50 text-slate-900">
        <Providers>
          <Header />
          <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
