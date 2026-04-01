"use client";

import { useState } from "react";

export default function AddCardForm({
  onAdd,
}: {
  onAdd: (input: { title: string; details: string }) => void;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [details, setDetails] = useState("");

  const canSubmit = title.trim().length > 0 && details.trim().length > 0;

  return (
    <div className="pt-3">
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="w-full rounded-md border border-foreground/10 px-3 py-2 text-sm font-medium text-navy transition-colors hover:border-accent"
        >
          + Add card
        </button>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit) return;

            onAdd({
              title: title.trim(),
              details: details.trim(),
            });

            setTitle("");
            setDetails("");
            setOpen(false);
          }}
          className="space-y-2"
        >
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Card title"
            className="w-full rounded-md border border-foreground/10 bg-white px-3 py-2 text-sm text-navy placeholder:text-gray-text outline-none focus:border-accent"
          />
          <textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder="Card details"
            rows={3}
            className="w-full resize-none rounded-md border border-foreground/10 bg-white px-3 py-2 text-sm text-navy placeholder:text-gray-text outline-none focus:border-accent"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={!canSubmit}
              className="flex-1 rounded-md bg-secondary px-3 py-2 text-sm font-medium text-white transition-colors disabled:cursor-not-allowed disabled:opacity-60"
            >
              Add
            </button>
            <button
              type="button"
              onClick={() => {
                setTitle("");
                setDetails("");
                setOpen(false);
              }}
              className="rounded-md border border-foreground/10 px-3 py-2 text-sm font-medium text-navy transition-colors hover:border-accent"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

