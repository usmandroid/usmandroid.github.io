// tcDeck(root): root = .sl-deck holding .sl sections. Keys while it has focus:
//   → space  next point, then next slide      ← backspace  back      f  fullscreen      n  speaker notes
// Lists reveal one point at a time: the current <li> is bold with ›, the others stay dim.
function tcDeck(root) {
  const s = [...root.querySelectorAll(".sl")];
  let i = 0,
    k = 0;
  const pts = () => [...s[i].querySelectorAll("li")];
  const mark = () => pts().forEach((x, j) => x.classList.toggle("now", j === k));
  s.forEach((x, n) => {
    const no = x.querySelector(".no");
    if (no) no.textContent = n + 1 + "/" + s.length;
  });
  const go = (n, end) => {
    i = Math.max(0, Math.min(s.length - 1, n));
    s.forEach((x, j) => x.classList.toggle("on", j === i));
    k = end ? Math.max(0, pts().length - 1) : 0;
    mark();
  };
  const next = () => (k < pts().length - 1 ? (k++, mark()) : go(i + 1));
  const back = () => (k > 0 ? (k--, mark()) : go(i - 1, true));
  root.tabIndex = 0;
  root.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === " ") next();
    else if (e.key === "ArrowLeft" || e.key === "Backspace") back();
    else if (e.key === "f")
      document.fullscreenElement ? document.exitFullscreen() : root.requestFullscreen();
    else if (e.key === "n") root.classList.toggle("notes");
    else return;
    e.preventDefault();
  });
  go(0);
  return { next, back };
}
