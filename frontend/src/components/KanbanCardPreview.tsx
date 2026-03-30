import type { Card } from "@/lib/kanban";

type KanbanCardPreviewProps = {
  card: Card;
};

export const KanbanCardPreview = ({ card }: KanbanCardPreviewProps) => (
  <article className="rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_18px_32px_rgba(3,33,71,0.16)]">
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-[rgba(236,173,10,0.16)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--navy-dark)]">
            {card.priority}
          </span>
          {card.assignee ? (
            <span className="rounded-full bg-[var(--surface)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--gray-text)]">
              {card.assignee}
            </span>
          ) : null}
        </div>
        <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
          {card.title}
        </h4>
        <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
          {card.details}
        </p>
      </div>
    </div>
  </article>
);
