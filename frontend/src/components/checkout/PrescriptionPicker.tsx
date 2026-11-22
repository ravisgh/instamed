"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { CheckIcon, FileIcon, UploadIcon } from "@/components/icons";
import { Callout, ErrorBanner, Skeleton, Spinner } from "@/components/ui";
import type { Prescription } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";

const STATUS: Record<Prescription["status"], { text: string; pill: string }> = {
  approved: { text: "approved", pill: "bg-brand-50 text-brand-700 ring-brand-200" },
  pending: { text: "waiting for review", pill: "bg-amber-50 text-amber-800 ring-amber-200" },
  rejected: { text: "rejected", pill: "bg-rose-50 text-rose-700 ring-rose-200" },
};

export function PrescriptionPicker({ value, onChange }: { value: string | null; onChange(id: string): void }) {
  const { api } = useAuth();
  const queryClient = useQueryClient();
  const prescriptions = useQuery({
    queryKey: ["prescriptions"],
    queryFn: () => api.get<Prescription[]>("/prescriptions?limit=50"),
  });

  const upload = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api.post<Prescription>("/prescriptions", form);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["prescriptions"] }),
  });

  return (
    <fieldset
      aria-label="Prescription"
      className="space-y-4 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card"
    >
      <legend className="sr-only">Prescription</legend>
      <div>
        <h2 className="text-base font-bold text-slate-900">Prescription</h2>
        <p className="mt-1 text-sm text-slate-600">
          Your cart has prescription medicines. Choose an approved prescription, or upload a new one for a
          pharmacist to review.
        </p>
      </div>

      {prescriptions.isError && <ErrorBanner message={prescriptions.error.message} />}
      {prescriptions.isPending && <Skeleton className="h-14 w-full rounded-xl" />}
      <ul className="space-y-2">
        {prescriptions.data?.map((rx) => {
          const usable = rx.status === "approved";
          const checked = value === rx.id;
          return (
            <li key={rx.id}>
              <label
                className={`flex items-center gap-3 rounded-xl border p-3 text-sm transition ${
                  checked
                    ? "border-brand-500 bg-brand-50/60 ring-1 ring-brand-500"
                    : usable
                      ? "cursor-pointer border-slate-200 hover:border-brand-300"
                      : "cursor-not-allowed border-slate-200 bg-slate-50"
                }`}
              >
                <input
                  type="radio"
                  name="prescription"
                  value={rx.id}
                  checked={checked}
                  disabled={!usable}
                  onChange={() => onChange(rx.id)}
                  className="h-4 w-4 accent-brand-600"
                />
                <FileIcon className={`h-5 w-5 shrink-0 ${usable ? "text-brand-600" : "text-slate-400"}`} />
                <span className={`min-w-0 flex-1 truncate font-medium ${usable ? "text-slate-800" : "text-slate-400"}`}>
                  {rx.original_filename}
                </span>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${STATUS[rx.status].pill}`}>
                  {STATUS[rx.status].text}
                </span>
              </label>
            </li>
          );
        })}
        {prescriptions.data?.length === 0 && <li className="text-sm text-slate-500">No prescriptions yet.</li>}
      </ul>

      <label className="flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed border-slate-300 px-4 py-6 text-center transition hover:border-brand-400 hover:bg-brand-50/40 focus-within:border-brand-500">
        <UploadIcon className="h-6 w-6 text-brand-600" />
        <span className="text-sm font-semibold text-slate-800">Upload a prescription</span>
        <span className="text-xs text-slate-500">(PDF, JPEG or PNG, up to 5 MB)</span>
        <input
          type="file"
          accept="application/pdf,image/jpeg,image/png"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload.mutate(file);
            e.target.value = "";
          }}
          className="sr-only"
        />
      </label>
      {upload.isPending && <Spinner label="Uploading…" />}
      {upload.isError && <ErrorBanner message={upload.error.message} />}
      {upload.isSuccess && (
        <Callout tone="success">
          <span className="inline-flex items-center gap-1 font-semibold">
            <CheckIcon className="h-4 w-4" /> Uploaded.
          </span>{" "}
          It is waiting for a pharmacist to approve it; you can place the order once it is approved.
        </Callout>
      )}
    </fieldset>
  );
}
