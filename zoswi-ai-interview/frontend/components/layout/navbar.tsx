import Link from "next/link";

import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-surface/85 backdrop-blur-sm">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-xl font-bold tracking-tight text-white">
          ZoSwi
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-slate-200 md:flex">
          <a href="#features" className="hover:text-brand-200">
            Features
          </a>
          <a href="#trust" className="hover:text-brand-200">
            Trust
          </a>
          <a href="#platform" className="hover:text-brand-200">
            Platform
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-medium text-slate-200 hover:text-white">
            Log in
          </Link>
          <Link href="/signup">
            <Button className="px-5 py-2">Start Free</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}

