import type { Metadata } from "next";
import { Suspense } from "react";

import { LoginForm } from "@/components/auth/LoginForm";

export const metadata: Metadata = { title: "Log in" };

export default function LoginPage() {
  // LoginForm reads ?next= (search params), which needs a Suspense boundary.
  return (
    <div className="flex flex-1 items-start justify-center px-4 py-10 sm:py-16">
      <Suspense>
        <LoginForm />
      </Suspense>
    </div>
  );
}
