import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";

import "@/app/globals.css";
import { AuthProvider } from "@/lib/auth/auth-context";

const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading"
});

const bodyFont = Manrope({
  subsets: ["latin"],
  variable: "--font-body"
});

export const metadata: Metadata = {
  title: "ZoSwi | AI Career Intelligence",
  description:
    "ZoSwi is a production-grade AI interview and career intelligence platform for candidates and recruiters."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${headingFont.variable} ${bodyFont.variable} font-body antialiased`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

