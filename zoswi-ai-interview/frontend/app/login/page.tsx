import { LoginForm } from "@/components/auth/login-form";
import { Card } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md items-center px-6 py-16">
      <Card className="w-full">
        <h1 className="text-2xl font-bold text-white">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-400">Sign in to continue your ZoSwi interview workflow.</p>
        <div className="mt-6">
          <LoginForm />
        </div>
      </Card>
    </div>
  );
}

