import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";

import "./globals.css";
import { Providers } from "./providers";

// Downloaded at build time and served from our own origin: no runtime request to Google.
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: { default: "InstaMed: medicines from your nearest pharmacy", template: "%s · InstaMed" },
  description: "Order medicines from the pharmacy that serves your pincode.",
};

export const viewport: Viewport = {
  themeColor: "#0a8073",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-slate-50 text-slate-900">
        <Providers>
          <Header />
          <main className="flex w-full flex-1 flex-col">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
