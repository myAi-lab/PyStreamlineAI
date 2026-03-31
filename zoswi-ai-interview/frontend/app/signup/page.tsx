import { SignupForm } from "@/components/auth/signup-form";
import { Card } from "@/components/ui/card";

export default function SignupPage() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-xl items-center px-6 py-16">
      <Card className="w-full">
        <h1 className="text-2xl font-bold text-white">Create your ZoSwi account</h1>
        <p className="mt-2 text-sm text-slate-400">
          Start resume analysis and interview simulations with role-aware onboarding.
        </p>
        <div className="mt-6">
          <SignupForm />
        </div>
      </Card>
    </div>
  );
}
