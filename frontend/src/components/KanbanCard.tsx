import { useEffect, useState, type FormEvent } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card, CardPriority } from "@/lib/kanban";
import { parseLabelInput } from "@/lib/kanban";

type CardFormValues = {
  title: string;
  details: string;
  assignee: string;
  dueDate: string;
  priority: CardPriority;
  labels: string[];
};

type KanbanCardProps = {
  card: Card;
  onSave: (cardId: string, values: CardFormValues) => void;
  onDelete: (cardId: string) => void;
};

const priorityStyles: Record<CardPriority, string> = {
  low: "bg-[rgba(32,157,215,0.12)] text-[var(--primary-blue)]",
  medium: "bg-[rgba(236,173,10,0.16)] text-[var(--navy-dark)]",
  high: "bg-[rgba(117,57,145,0.14)] text-[var(--secondary-purple)]",
};

export const KanbanCard = ({ card, onSave, onDelete }: KanbanCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(card.title);
  const [draftDetails, setDraftDetails] = useState(card.details);
  const [draftAssignee, setDraftAssignee] = useState(card.assignee);
  const [draftDueDate, setDraftDueDate] = useState(card.dueDate);
  const [draftPriority, setDraftPriority] = useState<CardPriority>(card.priority);
  const [draftLabels, setDraftLabels] = useState(card.labels.join(", "));
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id, disabled: isEditing });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };
  const dragProps = isEditing ? {} : { ...attributes, ...listeners };

  useEffect(() => {
    if (!isEditing) {
      setDraftTitle(card.title);
      setDraftDetails(card.details);
      setDraftAssignee(card.assignee);
      setDraftDueDate(card.dueDate);
      setDraftPriority(card.priority);
      setDraftLabels(card.labels.join(", "));
    }
  }, [
    card.assignee,
    card.details,
    card.dueDate,
    card.labels,
    card.priority,
    card.title,
    isEditing,
  ]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextTitle = draftTitle.trim();
    if (!nextTitle) {
      return;
    }

    onSave(card.id, {
      title: nextTitle,
      details: draftDetails.trim(),
      assignee: draftAssignee.trim(),
      dueDate: draftDueDate,
      priority: draftPriority,
      labels: parseLabelInput(draftLabels),
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setDraftTitle(card.title);
    setDraftDetails(card.details);
    setDraftAssignee(card.assignee);
    setDraftDueDate(card.dueDate);
    setDraftPriority(card.priority);
    setDraftLabels(card.labels.join(", "));
    setIsEditing(false);
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      {...dragProps}
      data-testid={`card-${card.id}`}
    >
      {isEditing ? (
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            value={draftTitle}
            onChange={(event) => setDraftTitle(event.target.value)}
            aria-label="Card title"
            className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-semibold text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
          />
          <textarea
            value={draftDetails}
            onChange={(event) => setDraftDetails(event.target.value)}
            aria-label="Card details"
            rows={4}
            className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm leading-6 text-[var(--gray-text)] outline-none transition focus:border-[var(--primary-blue)]"
          />
          <input
            value={draftAssignee}
            onChange={(event) => setDraftAssignee(event.target.value)}
            aria-label="Card assignee"
            placeholder="Assignee"
            className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <input
              value={draftDueDate}
              onChange={(event) => setDraftDueDate(event.target.value)}
              aria-label="Card due date"
              type="date"
              className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
            <select
              value={draftPriority}
              onChange={(event) => setDraftPriority(event.target.value as CardPriority)}
              aria-label="Card priority"
              className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            >
              <option value="low">Low priority</option>
              <option value="medium">Medium priority</option>
              <option value="high">High priority</option>
            </select>
          </div>
          <input
            value={draftLabels}
            onChange={(event) => setDraftLabels(event.target.value)}
            aria-label="Card labels"
            placeholder="Labels (comma separated)"
            className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
          />
          <div className="flex items-center gap-2">
            <button
              type="submit"
              className="rounded-full bg-[var(--secondary-purple)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
            >
              Save
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span
                className={clsx(
                  "rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]",
                  priorityStyles[card.priority]
                )}
              >
                {card.priority}
              </span>
              {card.assignee ? (
                <span className="rounded-full bg-[var(--surface)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--gray-text)]">
                  {card.assignee}
                </span>
              ) : null}
              {card.dueDate ? (
                <span className="rounded-full bg-[var(--surface)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--gray-text)]">
                  Due {card.dueDate}
                </span>
              ) : null}
            </div>
            <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
              {card.title}
            </h4>
            <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
              {card.details}
            </p>
            {card.labels.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {card.labels.map((label, index) => (
                  <span
                    key={`${label}-${index}`}
                    className="rounded-full border border-[var(--stroke)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--navy-dark)]"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--primary-blue)] transition hover:border-[var(--stroke)]"
              aria-label={`Edit ${card.title}`}
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => onDelete(card.id)}
              className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:text-[var(--navy-dark)]"
              aria-label={`Delete ${card.title}`}
            >
              Remove
            </button>
          </div>
        </div>
      )}
    </article>
  );
};
