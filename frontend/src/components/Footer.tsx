import { LogoMark } from "./icons";

export function Footer() {
  return (
    <footer className="mt-12 border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-2">
          <LogoMark className="h-6 w-6" />
          <span className="font-semibold text-slate-700">InstaMed</span>
          <span className="hidden sm:inline">· Licensed pharmacy · Genuine medicines</span>
        </div>
        <p className="max-w-md text-xs leading-relaxed sm:text-right">
          Prescription medicines are dispensed only against a valid prescription checked by a registered
          pharmacist. Always follow your doctor&apos;s advice.
        </p>
      </div>
    </footer>
  );
}
