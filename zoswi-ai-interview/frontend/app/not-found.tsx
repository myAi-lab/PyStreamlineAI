import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-xl flex-col items-center justify-center px-6 text-center">
      <h1 className="text-4xl font-bold text-white">Page not found</h1>
      <p className="mt-3 text-slate-400">The resource you requested does not exist in this ZoSwi workspace.</p>
      <Link href="/" className="mt-6">
        <Button>Go Home</Button>
      </Link>
    </div>
  );
}

