"use client";

import { useState } from "react";
import { submitBugReport, type BugReportPayload } from "@/lib/api";

interface Props {
  /** "suggestion" reframes placeholders around ideas and prefixes the
   *  submitted summary with "[Suggestion] " so the admin queue can
   *  visually separate the two without a schema change. */
  mode?: "bug" | "suggestion";
}

export default function BugReportForm({ mode = "bug" }: Props) {
  const isSuggestion = mode === "suggestion";
  const [summary, setSummary] = useState("");
  const [details, setDetails] = useState("");
  const [source, setSource] = useState<"website" | "addon">("website");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<null | { id: number }>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const trimmed = summary.trim();
      const submittedSummary = isSuggestion
        ? `[Suggestion] ${trimmed}`
        : trimmed;
      const payload: BugReportPayload = {
        summary: submittedSummary,
        details: details.trim(),
        source,
        submitter_name: name.trim() || undefined,
        submitter_email: email.trim() || undefined,
        page_url:
          typeof window !== "undefined" ? window.location.href : undefined,
      };
      const res = await submitBugReport(payload);
      setSubmitted({ id: res.id });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="bg-surface-container-high rounded-xl p-8 border border-primary/30">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
          Got It
        </p>
        <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl text-on-surface mb-3">
          {isSuggestion ? "Suggestion received." : `Bug report #${submitted.id} received.`}
        </h2>
        <p className="text-on-surface-variant">
          {isSuggestion
            ? "Thanks for the idea. We read every suggestion. If you left an email we might follow up with questions."
            : "Thanks for the heads-up. We'll look into it. If you left an email we might follow up with questions."}
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={onSubmit}
      className="bg-surface-container-low rounded-xl p-6 md:p-8 space-y-5"
    >
      <div className="flex gap-2">
        {(["website", "addon"] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSource(s)}
            className={`font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest px-4 py-2 rounded-md border transition-colors ${
              source === s
                ? "bg-primary/10 border-primary/40 text-primary"
                : "bg-surface-container-high border-outline-variant/20 text-on-surface-variant hover:text-on-surface"
            }`}
          >
            {isSuggestion
              ? s === "website"
                ? "For the website"
                : "For the addon"
              : s === "website"
                ? "Website bug"
                : "Addon bug"}
          </button>
        ))}
      </div>

      <Field label="Summary" required htmlFor="bug-summary">
        <input
          id="bug-summary"
          type="text"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          required
          minLength={3}
          maxLength={200}
          placeholder={
            isSuggestion
              ? "Short description: what should we build?"
              : "Short description: what broke?"
          }
          className="w-full bg-surface-container-high rounded-md px-3 py-2 text-on-surface placeholder:text-on-surface-variant/60 border border-outline-variant/20 focus:border-primary/50 focus:outline-none"
        />
      </Field>

      <Field label="Details" htmlFor="bug-details">
        <textarea
          id="bug-details"
          value={details}
          onChange={(e) => setDetails(e.target.value)}
          maxLength={8000}
          rows={8}
          placeholder={
            isSuggestion
              ? "What problem would this solve for you? Any examples of how other tools handle it? Rough sketches of the UI are welcome."
              : source === "addon"
                ? "Paste /umbra bug output here. Include steps that triggered it."
                : "Steps to reproduce, what you expected vs. what happened, screenshots if any."
          }
          className="w-full bg-surface-container-high rounded-md px-3 py-2 text-on-surface placeholder:text-on-surface-variant/60 border border-outline-variant/20 focus:border-primary/50 focus:outline-none font-mono text-sm"
        />
      </Field>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Field label="Your name (optional)" htmlFor="bug-name">
          <input
            id="bug-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={80}
            placeholder="So we know who to thank"
            className="w-full bg-surface-container-high rounded-md px-3 py-2 text-on-surface placeholder:text-on-surface-variant/60 border border-outline-variant/20 focus:border-primary/50 focus:outline-none"
          />
        </Field>
        <Field label="Email (optional)" htmlFor="bug-email">
          <input
            id="bug-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            maxLength={200}
            placeholder="In case we need details"
            className="w-full bg-surface-container-high rounded-md px-3 py-2 text-on-surface placeholder:text-on-surface-variant/60 border border-outline-variant/20 focus:border-primary/50 focus:outline-none"
          />
        </Field>
      </div>

      {error && (
        <p className="text-red-400 font-[family-name:var(--font-label)] text-xs uppercase tracking-widest">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting || summary.trim().length < 3}
        className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.2em] bg-primary text-on-primary px-6 py-3 rounded-md hover:brightness-110 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting
          ? "Sending..."
          : isSuggestion
            ? "Send Suggestion"
            : "Send Report"}
      </button>
    </form>
  );
}

function Field({
  label,
  required,
  htmlFor,
  children,
}: {
  label: string;
  required?: boolean;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="block">
      <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mb-2 inline-block">
        {label}
        {required && <span className="text-primary ml-1">*</span>}
      </span>
      {children}
    </label>
  );
}
