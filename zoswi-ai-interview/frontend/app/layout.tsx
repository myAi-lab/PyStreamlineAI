import type { Metadata } from "next";
import { DM_Sans, Space_Grotesk } from "next/font/google";

import "./globals.css";

const bodyFont = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"]
});

const displayFont = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"]
});

export const metadata: Metadata = {
  title: "ZoSwi AI Interview",
  description: "AI-powered technical interview platform for ZoSwi",
  icons: {
    icon: "/zoswi-logo-icon.png",
    shortcut: "/zoswi-logo-icon.png",
    apple: "/zoswi-logo-icon.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${bodyFont.variable} ${displayFont.variable} font-[var(--font-body)]`}>{children}</body>
    </html>
  );
}

