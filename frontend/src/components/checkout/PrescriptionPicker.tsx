"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorBanner } from "@/components/ui";
import type { Prescription } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";

const STATUS_TEXT: Record<Prescription["status"], string> = {
  approved: "approved",
  pending: "waiting for review",
  rejected: "rejected",
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
    <fieldset aria-label="Prescription" className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <legend className="px-1 font-medium">Prescription</legend>
      <p className="text-sm text-slate-600">
        Your cart has prescription medicines. Choose an approved prescription, or upload a new one for a
        pharmacist to review.
      </p>

      {prescriptions.isError && <ErrorBanner message={prescriptions.error.message} />}
      <ul className="space-y-1">
        {prescriptions.data?.map((rx) => (
          <li key={rx.id}>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="prescription"
                value={rx.id}
                checked={value === rx.id}
                disabled={rx.status !== "approved"}
                onChange={() => onChange(rx.id)}
              />
              <span className={rx.status === "approved" ? "" : "text-slate-400"}>
                {rx.original_filename} ({STATUS_TEXT[rx.status]})
              </span>
            </label>
          </li>
        ))}
        {prescriptions.data?.length === 0 && <li className="text-sm text-slate-500">No prescriptions yet.</li>}
      </ul>

      <label className="block text-sm font-medium">
        Upload a prescription (PDF, JPEG or PNG, up to 5 MB)
        <input
          type="file"
          accept="application/pdf,image/jpeg,image/png"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload.mutate(file);
            e.target.value = "";
          }}
          className="mt-1 block text-sm"
        />
      </label>
      {upload.isPending && <p className="text-sm text-slate-500">Uploading…</p>}
      {upload.isError && <ErrorBanner message={upload.error.message} />}
      {upload.isSuccess && (
        <p className="text-sm text-emerald-700">
          Uploaded. It is waiting for a pharmacist to approve it; you can place the order once it is approved.
        </p>
      )}
    </fieldset>
  );
}
