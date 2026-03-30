import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const jsonResponse = (body: unknown, init?: ResponseInit) =>
  new Response(JSON.stringify(body), {
    status: init?.status ?? 200,
    headers: { "Content-Type": "application/json" },
  });

const installFetchMock = (
  board: BoardData = initialData,
  onAiChat?: (payload: {
    message: string;
    history: { role: "user" | "assistant"; content: string }[];
    board: BoardData;
  }) => {
    assistant_message: string;
    board: BoardData;
    board_updated: boolean;
  }
) => {
  let currentBoard = structuredClone(board);

  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url === "/api/board") {
      if (!init?.method || init.method === "GET") {
        return jsonResponse({ board: currentBoard });
      }

      if (init.method === "PUT") {
        currentBoard = JSON.parse(String(init.body)) as BoardData;
        return jsonResponse({ board: currentBoard });
      }
    }

    if (url === "/api/ai/chat" && init?.method === "POST" && onAiChat) {
      const payload = JSON.parse(String(init.body)) as {
        message: string;
        history: { role: "user" | "assistant"; content: string }[];
        board: BoardData;
      };
      const result = onAiChat(payload);
      currentBoard = result.board;
      return jsonResponse(result);
    }

    throw new Error(`Unexpected fetch method: ${init.method}`);
  });
};

describe("KanbanBoard", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads the board from the API", async () => {
    installFetchMock();
    render(<KanbanBoard />);

    expect(
      screen.getByRole("heading", { name: /loading your workspace/i })
    ).toBeInTheDocument();
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
    expect(screen.getByText("Connected")).toBeInTheDocument();
  });

  it("renames a column and persists the change", async () => {
    const fetchMock = installFetchMock();
    render(<KanbanBoard />);

    const column = await screen.findByTestId("column-col-backlog");
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");

    expect(input).toHaveValue("New Name");

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board",
        expect.objectContaining({
          method: "PUT",
          body: expect.stringContaining('"title":"New Name"'),
        })
      );
    });
  });

  it("adds and removes a card while saving changes", async () => {
    const fetchMock = installFetchMock();
    render(<KanbanBoard />);

    const column = await screen.findByTestId("column-col-backlog");
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board",
        expect.objectContaining({
          method: "PUT",
          body: expect.stringContaining('"title":"New card"'),
        })
      );
    });

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(within(column).queryByText("New card")).not.toBeInTheDocument();
    });
  });

  it("edits a card and persists the changes", async () => {
    const fetchMock = installFetchMock();
    render(<KanbanBoard />);

    const card = await screen.findByTestId("card-card-1");
    await userEvent.click(
      within(card).getByRole("button", { name: /edit align roadmap themes/i })
    );

    const titleInput = within(card).getByLabelText("Card title");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Updated roadmap theme");

    const detailsInput = within(card).getByLabelText("Card details");
    await userEvent.clear(detailsInput);
    await userEvent.type(detailsInput, "Fresh implementation notes.");

    await userEvent.click(within(card).getByRole("button", { name: /save/i }));

    expect(await within(card).findByText("Updated roadmap theme")).toBeInTheDocument();
    expect(within(card).getByText("Fresh implementation notes.")).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board",
        expect.objectContaining({
          method: "PUT",
          body: expect.stringContaining('"title":"Updated roadmap theme"'),
        })
      );
    });
  });

  it("shows a load error when the API request fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: "Backend offline" }, { status: 503 })
    );

    render(<KanbanBoard />);

    expect(
      await screen.findByRole("heading", { name: /unable to load the workspace/i })
    ).toBeInTheDocument();
    expect(screen.getByText("Backend offline")).toBeInTheDocument();
  });

  it("sends an AI prompt and applies the returned board update", async () => {
    installFetchMock(initialData, (payload) => {
      expect(payload.message).toBe("Move QA micro-interactions to Done");
      expect(payload.history).toEqual([]);
      expect(payload.board.columns[3].cardIds).toContain("card-6");

      const nextBoard = structuredClone(payload.board);
      nextBoard.columns[3].cardIds = [];
      nextBoard.columns[4].cardIds = [...nextBoard.columns[4].cardIds, "card-6"];

      return {
        assistant_message: "Moved QA micro-interactions to Done.",
        board: nextBoard,
        board_updated: true,
      };
    });

    render(<KanbanBoard />);

    await screen.findByTestId("column-col-review");
    await userEvent.type(
      screen.getByPlaceholderText(/ask the ai to create, edit, move, or summarize cards/i),
      "Move QA micro-interactions to Done"
    );
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(
      await screen.findByText("Moved QA micro-interactions to Done.")
    ).toBeInTheDocument();
    expect(
      within(screen.getByTestId("column-col-done")).getByTestId("card-card-6")
    ).toBeInTheDocument();
    expect(screen.getByText("All changes saved")).toBeInTheDocument();
  });
});
