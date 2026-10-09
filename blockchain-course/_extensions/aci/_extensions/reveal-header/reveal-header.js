/* reveal-header.js — single top bar, event-driven, robust
   - Uses slidechanged event payload (e.currentSlide, e.indexh/e.indexv)
   - Title-slide detection by indices only (h=0, v=0)
   - Per-slide overrides: data-header attribute or ::: header block
   - skip-title-lift and title-slide-header supported
*/

(function () {
  // ---- helpers to read <meta> published by the Lua filter -------------------
  function meta(name) {
    const m = document.querySelector(`meta[name="${name}"]`);
    return m ? m.content : "";
  }
  function truthy(name) { return meta(name) === "true"; }

  function readConfig() {
    return {
      defaultText:        meta("reveal-header-default") || "",
      logo:               meta("reveal-header-logo") || "",
      logoLink:           meta("reveal-header-logo-link") || "",
      footerLogoLink:     meta("reveal-header-footer-logo-link") || "",
      homeLink:           meta("reveal-header-home-link") || "../../index.html",
      homeText:           meta("reveal-header-home-text") || "Course Portal",
      titleAsDefault:     truthy("reveal-header-title-as-default"),
      subtitleAsDefault:  truthy("reveal-header-subtitle-as-default"),
      hideFromTitleSlide: meta("reveal-header-hide-from-titleslide") || "",
      preferSlideHeader:  meta("reveal-header-prefer-slide-header") !== "false", // default true
      skipTitleLift:      truthy("reveal-header-skip-title-lift"),               // default false
      titleSlideHeader:   meta("reveal-header-title-slide-header") || ""
    };
  }

  // ---- DOM for the single header bar ---------------------------------------
  function ensureHeaderBar(deck, cfg) {
    const host = deck.getRevealElement();
    let bar = host.querySelector(".reveal-header");
    if (bar) return bar;

    bar = document.createElement("div");
    bar.className = "reveal-header";

    if (cfg.homeLink !== "none" && cfg.homeLink !== "false") {
      const homeBtn = document.createElement("a");
      homeBtn.className = "course-portal-back-btn";
      homeBtn.href = cfg.homeLink;
      homeBtn.title = "Return to Course Home Portal";
      homeBtn.setAttribute("aria-label", "Return to Course Home Portal");
      homeBtn.innerHTML =
        '<svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<line x1="19" y1="12" x2="5" y2="12"></line>' +
        '<polyline points="12 19 5 12 12 5"></polyline>' +
        '</svg>' +
        '<span>' + (cfg.homeText || "Course Portal") + '</span>';
      homeBtn.addEventListener("click", function (e) {
        e.stopPropagation();
      });
      bar.appendChild(homeBtn);
    }

    const text = document.createElement("div");
    text.className = "header-text";
    bar.appendChild(text);

    if (cfg.logo) {
      const logo = document.createElement("div");
      logo.className = "header-logo";
      const img = document.createElement("img");
      img.src = cfg.logo; img.alt = "header-logo";
      if (cfg.logoLink) {
        const a = document.createElement("a");
        a.href = cfg.logoLink; a.target = "_blank"; a.rel = "noopener";
        a.appendChild(img); logo.appendChild(a);
      } else {
        logo.appendChild(img);
      }
      bar.appendChild(logo);
    }
    host.appendChild(bar);
    return bar;
  }

  // ---- title slide test: rely on indices from event payload -----------------
  function isTitleFromIndices(idx) {
    return idx && idx.h === 0 && idx.v === 0;
  }

  // ---- per-slide overrides ---------------------------------------------------
  // A) Attribute override works even on "headerless" slides
  function readAttrHeader(section) {
    if (!section || !section.getAttribute) return null;
    const v = section.getAttribute("data-header");
    return v && v.trim() ? { text: v.trim(), html: "" } : null;
  }

  // B) ::: header block — remove only if we actually use it (no duplicates)
  function readAndRemoveHeaderBlock(section) {
    if (!section) return null;
    let block = null;
    try {
      block = section.querySelector(':scope > .header');
    } catch (e) {
      block = section.querySelector('div.header');
    }
    if (!block) return null;
    const txt = (block.textContent || "").trim();
    if (!txt) return null;
    const html = (block.innerHTML || "").trim();
    block.remove();
    return { text: txt, html };
  }

  // ---- lifting/removing slide titles ----------------------------------------
  function firstTopHeading(section) {
    return section ? section.querySelector("h1, h2, h3") : null;
  }

  function cacheAndRemoveHeading(section) {
    if (section.dataset.headerText) {
      return {
        text: section.dataset.headerText,
        html: section.dataset.headerHtml || ""
      };
    }
    const h = firstTopHeading(section);
    if (h) {
      const txt = (h.textContent || "").trim();
      const html = (h.innerHTML || "").trim();
      h.remove();
      section.dataset.headerText = txt;
      section.dataset.headerHtml = html;
      return { text: txt, html };
    }
    return null;
  }

  function asHeaderContent(value) {
    if (!value) return null;
    if (typeof value === "string") {
      return { text: value, html: "" };
    }
    return value;
  }

  function setHeaderContent(textEl, value) {
    const content = asHeaderContent(value);
    if (!content) {
      textEl.textContent = "";
      return;
    }

    if (content.html && content.html !== content.text) {
      textEl.innerHTML = content.html;
    } else {
      textEl.textContent = content.text;
    }
  }

  // ---- document-level fallbacks ---------------------------------------------
  function docTitle() {
    const el = document.querySelector('.title-slide h1, section.title-slide h1, #title-slide h1');
    return el ? el.textContent.trim() : (document.title || "");
  }
  function docSubtitle() {
    const el = document.querySelector('.title-slide h2, section.title-slide h2, #title-slide h2');
    return el ? el.textContent.trim() : "";
  }
  function fallbackText(cfg) {
    if (cfg.titleAsDefault)  { const t = docTitle();     if (t) return t; }
    if (cfg.subtitleAsDefault){ const s = docSubtitle(); if (s) return s; }
    return cfg.defaultText || "";
  }

  // ---- optional: make bottom-right .slide-logo clickable --------------------
  function wrapFooterLogoIfNeeded(cfg) {
    const link = cfg.footerLogoLink;
    if (!link) return;
    const img = document.querySelector("img.slide-logo");
    if (!img || img.closest("a")) return;
    const a = document.createElement("a");
    a.href = link; a.target = "_blank"; a.rel = "noopener";
    a.appendChild(img.cloneNode(true));
    img.replaceWith(a);
  }
  // If you don't need this feature, you can delete the function above and the call below.

  // ---- the plugin -----------------------------------------------------------
  window.RevealHeader = function () {
    return {
      id: "RevealHeader",
      init: function (deck) {
        const cfg = readConfig();
        const bar = ensureHeaderBar(deck, cfg);
        const textEl = bar.querySelector(".header-text");

        // Single update that uses the event payload (Option A)
        function updateFromEvent(e) {
          // Use event-provided slide + indices; fall back to deck getters when e is absent (e.g. ready)
          const section = (e && e.currentSlide) || deck.getCurrentSlide();
          const idx = e ? { h: e.indexh, v: e.indexv } : deck.getIndices();
          const onTitle = isTitleFromIndices(idx);

          // Respect hide-from-titleSlide
          bar.classList.toggle("hide-text", onTitle && (cfg.hideFromTitleSlide === "text" || cfg.hideFromTitleSlide === "all"));
          bar.classList.toggle("hide-logo", onTitle && (cfg.hideFromTitleSlide === "logo" || cfg.hideFromTitleSlide === "all"));

          let headerContent = null;

          if (onTitle) {
            // Title-slide precedence:
            // 1) explicit override
            if (cfg.titleSlideHeader) {
              headerContent = cfg.titleSlideHeader;
            }
            // 2) per-slide data-header
            if (!headerContent) {
              const a = readAttrHeader(section);
              if (a) headerContent = a;
            }
            // 3) ::: header block (if allowed)
            if (!headerContent && cfg.preferSlideHeader) {
              const b = readAndRemoveHeaderBlock(section);
              if (b) headerContent = b;
            }
            // 4) If still empty…
            if (!headerContent) {
              if (cfg.skipTitleLift) {
                // Do NOT lift/remove on title slide
                headerContent = fallbackText(cfg);
              } else {
                const lifted = cacheAndRemoveHeading(section);
                headerContent = lifted || fallbackText(cfg);
              }
            }

          } else {
            // Non-title slides precedence:
            // 1) per-slide data-header
            const a = readAttrHeader(section);
            if (a) headerContent = a;

            // 2) ::: header block (if allowed and not already set)
            if (!headerContent && cfg.preferSlideHeader) {
              const b = readAndRemoveHeaderBlock(section);
              if (b) headerContent = b;
            }

            // 3) lift/remove H1/H2/H3
            if (!headerContent) {
              const lifted = cacheAndRemoveHeading(section);
              headerContent = lifted || fallbackText(cfg);
            }
          }

          setHeaderContent(textEl, headerContent);
        }

        deck.on("ready", () => {
          wrapFooterLogoIfNeeded(cfg);    // <-- remove this line too if you dropped the function
          updateFromEvent();              // no event object on first call; falls back to deck.getIndices()
        });

        // Use event payload (no timing race)
        deck.on("slidechanged", (e) => updateFromEvent(e));
      }
    };
  };
})();
