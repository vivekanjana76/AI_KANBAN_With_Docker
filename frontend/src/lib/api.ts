import type { BoardData } from "@/lib/kanban";

export type ChatHistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AIChatResult = {
  assistant_message: string;
  board: BoardData;
  board_updated: boolean;
};

const getErrorMessage = async (response: Response) => {
  try {
    const data = (await response.json()) as { detail?: string; error?: string };
    return data.detail || data.error || `Request failed with ${response.status}`;
  } catch {
    return `Request failed with ${response.status}`;
  }
};

const ensureOk = async (response: Response) => {
  if (response.status === 401) {
    window.location.href = "/login";
    throw new Error("Authentication required");
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response;
};

export const loadBoard = async (): Promise<BoardData> => {
  const response = await ensureOk(
    await fetch("/api/board", {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    })
  );
  const data = (await response.json()) as { board: BoardData };
  return data.board;
};

export const saveBoard = async (board: BoardData, signal?: AbortSignal): Promise<BoardData> => {
  const response = await ensureOk(
    await fetch("/api/board", {
      method: "PUT",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(board),
      signal,
    })
  );
  const data = (await response.json()) as { board: BoardData };
  return data.board;
};

export const sendAiMessage = async (
  message: string,
  history: ChatHistoryMessage[],
  board: BoardData
): Promise<AIChatResult> => {
  const response = await ensureOk(
    await fetch("/api/ai/chat", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ message, history, board }),
    })
  );
  return (await response.json()) as AIChatResult;
};
