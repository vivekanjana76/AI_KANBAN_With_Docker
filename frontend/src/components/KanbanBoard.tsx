"use client";

import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import {
  loadBoard,
  saveBoard,
  sendAiMessage,
  type ChatHistoryMessage,
} from "@/lib/api";
import { createId, moveCard, type BoardData } from "@/lib/kanban";

type LoadState = "loading" | "ready" | "error";
type SaveState = "idle" | "saving" | "saved" | "error";

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatHistoryMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [aiError, setAiError] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const skipNextSave = useRef(true);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        setLoadState("loading");
        setLoadError(null);
        const nextBoard = await loadBoard();
        if (cancelled) {
          return;
        }
        skipNextSave.current = true;
        setBoard(nextBoard);
        setSaveState("idle");
        setLoadState("ready");
      } catch (error) {
        if (cancelled) {
          return;
        }
        setLoadState("error");
        setLoadError(
          error instanceof Error ? error.message : "Unable to load the board."
        );
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!board) {
      return;
    }

    if (skipNextSave.current) {
      skipNextSave.current = false;
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      void (async () => {
        try {
          setSaveState("saving");
          setSaveError(null);
          await saveBoard(board, controller.signal);
          setSaveState("saved");
        } catch (error) {
          if (controller.signal.aborted) {
            return;
          }
          setSaveState("error");
          setSaveError(
            error instanceof Error ? error.message : "Unable to save the board."
          );
        }
      })();
    }, 300);

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [board]);

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);
  const updateBoard = (transform: (currentBoard: BoardData) => BoardData) => {
    setBoard((prev) => (prev ? transform(prev) : prev));
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id || !board) {
      return;
    }

    updateBoard((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    if (!board) {
      return;
    }

    updateBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    if (!board) {
      return;
    }

    const id = createId("card");
    updateBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    if (!board) {
      return;
    }

    updateBoard((prev) => ({
      ...prev,
      cards: Object.fromEntries(
        Object.entries(prev.cards).filter(([id]) => id !== cardId)
      ),
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? {
              ...column,
              cardIds: column.cardIds.filter((id) => id !== cardId),
            }
          : column
      ),
    }));
  };

  const handleUpdateCard = (cardId: string, title: string, details: string) => {
    if (!board) {
      return;
    }

    updateBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [cardId]: {
          ...prev.cards[cardId],
          title,
          details: details || "No details yet.",
        },
      },
    }));
  };

  const handleAiSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!board) {
      return;
    }

    const message = chatInput.trim();
    if (!message || isAiLoading) {
      return;
    }

    setIsAiLoading(true);
    setAiError(null);
    setChatInput("");

    try {
      const result = await sendAiMessage(message, chatHistory, board);
      setChatHistory((prev) => [
        ...prev,
        { role: "user", content: message },
        { role: "assistant", content: result.assistant_message },
      ]);
      skipNextSave.current = true;
      setBoard(result.board);
      setSaveState("saved");
      setSaveError(null);
    } catch (error) {
      setAiError(
        error instanceof Error ? error.message : "Unable to reach the AI assistant."
      );
      setChatInput(message);
    } finally {
      setIsAiLoading(false);
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;
  const boardColumns = board?.columns ?? [];
  const statusText =
    saveState === "saving"
      ? "Saving changes..."
      : saveState === "saved"
        ? "All changes saved"
        : saveState === "error"
          ? saveError || "Save failed"
          : "Connected";

  if (loadState === "error") {
    return (
      <div className="relative overflow-hidden">
        <main className="relative mx-auto flex min-h-screen max-w-[1500px] items-center justify-center px-6 py-12">
          <div className="rounded-[32px] border border-[var(--stroke)] bg-white/90 px-8 py-10 text-center shadow-[var(--shadow)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
              Board
            </p>
            <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
              Unable to load the workspace
            </h1>
            <p className="mt-3 max-w-md text-sm leading-6 text-[var(--gray-text)]">
              {loadError || "The board could not be loaded right now."}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-6 rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110"
            >
              Retry
            </button>
          </div>
        </main>
      </div>
    );
  }

  if (loadState === "loading" || !board) {
    return (
      <div className="relative overflow-hidden">
        <main className="relative mx-auto flex min-h-screen max-w-[1500px] items-center justify-center px-6 py-12">
          <div className="rounded-[32px] border border-[var(--stroke)] bg-white/90 px-8 py-10 text-center shadow-[var(--shadow)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
              Board
            </p>
            <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
              Loading your workspace
            </h1>
            <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
              Pulling the latest board state from the server.
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and use the AI sidebar to reshape work without losing the thread.
              </p>
            </div>
            <div className="flex items-start gap-4">
              <a
                href="/logout"
                className="rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)] transition hover:border-[var(--accent-yellow)]"
              >
                Log out
              </a>
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Sync
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  {statusText}
                </p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {boardColumns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <section className="grid gap-6 lg:grid-cols-5">
              {boardColumns.map((column) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  cards={column.cardIds.map((cardId) => board.cards[cardId])}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onUpdateCard={handleUpdateCard}
                  onDeleteCard={handleDeleteCard}
                />
              ))}
            </section>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          <aside className="rounded-[32px] border border-[var(--stroke)] bg-white/80 p-5 shadow-[var(--shadow)] backdrop-blur xl:sticky xl:top-8 xl:h-[calc(100vh-4rem)] xl:max-h-[900px]">
            <div className="flex h-full flex-col">
              <div className="border-b border-[var(--stroke)] pb-4">
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
                  AI Sidebar
                </p>
                <h2 className="mt-3 font-display text-2xl font-semibold text-[var(--navy-dark)]">
                  Board Copilot
                </h2>
                <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
                  Ask for card creation, edits, moves, or a quick summary of the
                  current board.
                </p>
              </div>

              <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1">
                {chatHistory.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-[var(--stroke)] px-4 py-5 text-sm leading-6 text-[var(--gray-text)]">
                    Try: "Create a card for drafting release notes in Review" or
                    "Move QA micro-interactions to Done."
                  </div>
                ) : (
                  chatHistory.map((message, index) => (
                    <article
                      key={`${message.role}-${index}`}
                      className={
                        message.role === "assistant"
                          ? "rounded-2xl bg-[var(--surface)] px-4 py-3"
                          : "ml-8 rounded-2xl bg-[var(--primary-blue)] px-4 py-3 text-white"
                      }
                    >
                      <p
                        className={
                          message.role === "assistant"
                            ? "text-[11px] font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]"
                            : "text-[11px] font-semibold uppercase tracking-[0.25em] text-white/70"
                        }
                      >
                        {message.role === "assistant" ? "Assistant" : "You"}
                      </p>
                      <p
                        className={
                          message.role === "assistant"
                            ? "mt-2 text-sm leading-6 text-[var(--navy-dark)]"
                            : "mt-2 text-sm leading-6 text-white"
                        }
                      >
                        {message.content}
                      </p>
                    </article>
                  ))
                )}
                {isAiLoading ? (
                  <div className="rounded-2xl bg-[var(--surface)] px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                      Assistant
                    </p>
                    <p className="mt-2 text-sm leading-6 text-[var(--navy-dark)]">
                      Thinking through the board...
                    </p>
                  </div>
                ) : null}
              </div>

              <form onSubmit={handleAiSubmit} className="mt-4 border-t border-[var(--stroke)] pt-4">
                <textarea
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Ask the AI to create, edit, move, or summarize cards..."
                  rows={5}
                  className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm leading-6 text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                />
                {aiError ? (
                  <p className="mt-3 text-sm leading-6 text-[#b91c1c]">{aiError}</p>
                ) : null}
                <div className="mt-4 flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                    Uses the live board state
                  </p>
                  <button
                    type="submit"
                    disabled={isAiLoading || !chatInput.trim()}
                    className="rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isAiLoading ? "Working..." : "Send"}
                  </button>
                </div>
              </form>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};
