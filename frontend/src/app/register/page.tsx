import type { Metadata } from "next";

import { RegisterForm } from "@/components/auth/RegisterForm";

export const metadata: Metadata = { title: "Create account" };

export default function RegisterPage() {
  return (
    <div className="flex flex-1 items-start justify-center px-4 py-10 sm:py-16">
      <RegisterForm />
    </div>
  );
}
