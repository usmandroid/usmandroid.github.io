// Keys: every action has one. Theme choice is shared with STYLESHEET.html (same storage key).
// "auto" = no data-theme attribute: CSS follows the system dark/light setting live.
(function () {
  var themes = ["auto", "dark", "light", "eink"];
  var root = document.documentElement;
  var jobs = function () {
    return document.querySelectorAll("details.job, details.abs");
  };
  var current = function () {
    return root.dataset.theme || "auto";
  };

  function setTheme(t) {
    if (t === "auto") root.removeAttribute("data-theme");
    else root.dataset.theme = t;
    try {
      if (t === "auto") localStorage.removeItem("tc-style-theme");
      else localStorage.setItem("tc-style-theme", t);
    } catch (e) {}
    document.querySelectorAll("[data-theme-set]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.themeSet === t);
    });
  }
  function setAll(open) {
    jobs().forEach(function (d) {
      d.open = open;
    });
  }

  var act = {
    t: function () {
      setTheme(themes[(themes.indexOf(current()) + 1) % themes.length]);
    },
    e: function () {
      setAll(true);
    },
    c: function () {
      setAll(false);
    },
    p: function () {
      window.print();
    },
  };

  document.addEventListener("keydown", function (ev) {
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
    var tag = (ev.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (act[ev.key]) act[ev.key]();
  });
  document.querySelectorAll("[data-act]").forEach(function (b) {
    b.addEventListener("click", function () {
      act[b.dataset.act]();
    });
  });
  document.querySelectorAll("[data-theme-set]").forEach(function (b) {
    b.addEventListener("click", function () {
      setTheme(b.dataset.themeSet);
    });
  });
  setTheme(current());

  // print and PDF always show every entry, then restore the fold state
  var state = [];
  window.addEventListener("beforeprint", function () {
    state = Array.prototype.map.call(jobs(), function (d) {
      return d.open;
    });
    setAll(true);
  });
  window.addEventListener("afterprint", function () {
    jobs().forEach(function (d, i) {
      d.open = state[i];
    });
  });
})();
