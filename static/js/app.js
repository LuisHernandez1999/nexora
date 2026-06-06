// L3D Labz — interações e animações (sem framework)
(function () {
  "use strict";

  /* ---------------------------------------------------- menu mobile */
  const toggle = document.getElementById("navToggle");
  const nav = document.getElementById("mainNav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      Object.assign(nav.style, open ? {
        display: "flex", position: "absolute", top: "var(--header-h)", left: "0", right: "0",
        flexDirection: "column", background: "var(--bg-soft)", padding: "1rem 22px",
        borderBottom: "1px solid var(--border)", gap: "1rem",
      } : { display: "" });
    });
  }

  /* ---------------------------------------------------- alternância de tema */
  const themeBtn = document.getElementById("themeToggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const cur = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
      const next = cur === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("l3d-theme", next); } catch (e) {}
    });
  }

  /* ---------------------------------------------------- header ao rolar */
  const header = document.querySelector(".site-header");
  if (header) {
    const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------------------------------------------------- reveal on scroll */
  const revealables = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealables.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealables.forEach((el) => io.observe(el));
  } else {
    revealables.forEach((el) => el.classList.add("is-visible"));
  }

  /* ---------------------------------------------------- CSRF helper */
  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m.pop()) : "";
  }

  /* ---------------------------------------------------- add to cart (fetch) */
  document.addEventListener("submit", async (e) => {
    const form = e.target.closest("form[data-cart-form]");
    if (!form) return;
    e.preventDefault();
    const btn = form.querySelector("button[type=submit]");
    const original = btn ? btn.innerHTML : "";
    if (btn) { btn.disabled = true; btn.innerHTML = "Adicionando…"; }
    try {
      const res = await fetch(form.action, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken"), "X-Requested-With": "fetch" },
        body: new FormData(form),
      });
      const data = await res.json();
      updateCartBadge(data.cart_count);
      if (btn) {
        btn.innerHTML = "Adicionado";
        btn.classList.add("added");
        setTimeout(() => { btn.innerHTML = original; btn.disabled = false; btn.classList.remove("added"); }, 1300);
      }
    } catch (err) {
      window.location = form.action;
    }
  });

  /* ---------------------------------------------------- carrosséis */
  document.querySelectorAll(".carousel").forEach((root) => {
    const track = root.querySelector(".carousel-track");
    const slides = root.querySelectorAll(".slide");
    const dotsWrap = root.querySelector("[data-carousel-dots]");
    if (!track || slides.length < 2) return;
    let i = 0, timer;
    const dots = [];
    if (dotsWrap) {
      slides.forEach((_, idx) => {
        const b = document.createElement("button");
        b.setAttribute("aria-label", "Ir para slide " + (idx + 1));
        b.addEventListener("click", () => go(idx));
        dotsWrap.appendChild(b); dots.push(b);
      });
    }
    const render = () => {
      track.style.transform = `translateX(-${i * 100}%)`;
      dots.forEach((d, idx) => d.classList.toggle("active", idx === i));
    };
    const go = (n) => { i = (n + slides.length) % slides.length; render(); restart(); };
    const restart = () => { clearInterval(timer); timer = setInterval(() => go(i + 1), 5500); };
    const prev = root.querySelector("[data-carousel-prev]");
    const next = root.querySelector("[data-carousel-next]");
    if (prev) prev.addEventListener("click", () => go(i - 1));
    if (next) next.addEventListener("click", () => go(i + 1));
    root.addEventListener("mouseenter", () => clearInterval(timer));
    root.addEventListener("mouseleave", restart);
    render(); restart();
  });

  /* ---------------------------------------------------- toasts */
  (function toasts() {
    const wrap = document.getElementById("toastWrap");
    if (!wrap) return;
    const dismiss = (t) => { t.classList.add("hide"); setTimeout(() => t.remove(), 400); };
    wrap.querySelectorAll(".toast").forEach((t, i) => {
      const close = t.querySelector(".tc");
      if (close) close.addEventListener("click", () => dismiss(t));
      setTimeout(() => dismiss(t), 4500 + i * 600);
    });
  })();

  /* ---------------------------------------------------- copiar (PIX/boleto) */
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-copy]");
    if (!btn) return;
    const text = btn.getAttribute("data-copy");
    navigator.clipboard.writeText(text).then(() => {
      const original = btn.innerHTML;
      btn.classList.add("copied");
      btn.innerHTML = "Copiado";
      setTimeout(() => { btn.classList.remove("copied"); btn.innerHTML = original; }, 1600);
    });
  });

  function updateCartBadge(count) {
    let badge = document.querySelector("[data-cart-count]");
    if (!count) { if (badge) badge.remove(); return; }
    if (!badge) {
      const cartBtn = document.querySelector('a[href*="carrinho"]');
      if (!cartBtn) return;
      badge = document.createElement("span");
      badge.className = "cart-badge";
      badge.setAttribute("data-cart-count", "");
      cartBtn.appendChild(badge);
    }
    badge.textContent = count;
    badge.style.animation = "none"; void badge.offsetWidth; badge.style.animation = "";
  }
})();
