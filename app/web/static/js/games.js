document.getElementById("board")?.addEventListener("click", async (e) => {
  const btn = e.target.closest(".board-cell");
  if (!btn) return;
  await fetch(`/games/sessions/${SESSION_ID}/move`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_id: PLAYER_ID, move: { cell: Number(btn.dataset.cell) } }),
  });
  location.reload();
});