(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);

  const views = {
    home: $("#view-home"),
    loading: $("#view-loading"),
    results: $("#view-results"),
  };

  function showView(name) {
    Object.values(views).forEach((v) => v.classList.remove("is-visible"));
    views[name].classList.add("is-visible");
  }

  // ---------------------------------------------------------
  // Home / upload
  // ---------------------------------------------------------
  const form = $("#upload-card");
  const fileInput = $("#file-input");
  const analyzeBtn = $("#analyze-btn");
  const errorBox = $("#upload-error");
  const uploadEmpty = $("#upload-empty");
  const uploadFilled = $("#upload-filled");
  const previewImg = $("#preview-img");
  const filenameLabel = $("#filename-label");

  let selectedFile = null;

  function setError(msg) {
    if (!msg) {
      errorBox.classList.remove("is-visible");
      errorBox.textContent = "";
      return;
    }
    errorBox.textContent = msg;
    errorBox.classList.add("is-visible");
  }

  function setSelectedFile(file) {
    if (!file) return;
    const okTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!okTypes.includes(file.type)) {
      setError("Please upload a JPG, PNG or WEBP photo.");
      return;
    }
    setError(null);
    selectedFile = file;
    analyzeBtn.disabled = false;

    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      uploadEmpty.classList.add("hidden");
      uploadFilled.classList.remove("hidden");
      filenameLabel.textContent = file.name;
    };
    reader.readAsDataURL(file);
  }

  fileInput.addEventListener("change", (e) => setSelectedFile(e.target.files[0]));

  form.addEventListener("dragover", (e) => {
    e.preventDefault();
    form.classList.add("is-dragover");
  });
  form.addEventListener("dragleave", () => form.classList.remove("is-dragover"));
  form.addEventListener("drop", (e) => {
    e.preventDefault();
    form.classList.remove("is-dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  });

  // clicking the empty state opens the file picker; clicking the
  // preview / button area should not double-trigger it
  uploadEmpty.addEventListener("click", (e) => {
    if (e.target.tagName !== "LABEL") fileInput.click();
  });

  const LOADING_LINES = [
    "Reading your handwriting...",
    "Measuring slant and spacing...",
    "Weighing up your baseline...",
    "Writing your read...",
  ];

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    showView("loading");
    let lineIdx = 0;
    const loadingText = $("#loading-text");
    const loadingTimer = setInterval(() => {
      lineIdx = (lineIdx + 1) % LOADING_LINES.length;
      loadingText.textContent = LOADING_LINES[lineIdx];
    }, 1400);

    const body = new FormData();
    body.append("image", selectedFile);

    try {
      const res = await fetch("/analyze", { method: "POST", body });
      const data = await res.json();

      clearInterval(loadingTimer);

      if (!res.ok) {
        setError(data.error || "Something went wrong analyzing that image.");
        showView("home");
        return;
      }

      renderResults(data);
      showView("results");
    } catch (err) {
      clearInterval(loadingTimer);
      setError("Couldn't reach the server. Is the Flask app running?");
      showView("home");
    }
  });

  $("#analyze-another").addEventListener("click", resetToHome);

  function resetToHome() {
    selectedFile = null;
    fileInput.value = "";
    analyzeBtn.disabled = true;
    uploadEmpty.classList.remove("hidden");
    uploadFilled.classList.add("hidden");
    setError(null);
    showView("home");
  }

  // ---------------------------------------------------------
  // Results rendering
  // ---------------------------------------------------------
  const FEATURE_META = {
    slant:    { title: "Slant", icon: `<path d="M12 3 L12 21 M12 3 L9 6 M12 3 L15 6" transform="rotate(15 12 12)"/>`, barClass: "bar-fill--moss" },
    spacing:  { title: "Spacing", icon: `<path d="M6 4v16M18 4v16M6 12h12"/>`, barClass: "bar-fill--moss" },
    size:     { title: "Size", icon: `<path d="M4 18h4l8-14 4 14"/>`, barClass: "bar-fill--moss" },
    baseline: { title: "Baseline", icon: `<path d="M4 8h16M4 16h16"/>`, barClass: "bar-fill--moss" },
  };

  function renderResults(data) {
    const { features, trait, scores, personality_read, doodle } = data;
    const interp = interpretFeatures(features);

    // hero text + trait pill
    $("#trait-word").textContent = trait + ".";
    $("#read-text").textContent = personality_read;

    // trait card image (the illustrated plush-mascot cards)
    const resolvedTrait = DOODLE_TO_TRAIT[doodle] || trait;
    const slot = $("#doodle-slot");
    const imgSrc = TRAIT_IMAGES[resolvedTrait];
    slot.innerHTML = imgSrc
      ? `<img src="${imgSrc}" alt="${resolvedTrait}" class="trait-card-img">`
      : "";
    // The heading word is already baked into each card image, so no
    // separate caption is needed underneath anymore.
    $("#doodle-caption").textContent = "";

    // feature analysis rows
    const featureRows = $("#feature-rows");
    featureRows.innerHTML = "";
    ["slant", "spacing", "size", "baseline"].forEach((key) => {
      const meta = FEATURE_META[key];
      const info = interp[key];
      featureRows.insertAdjacentHTML("beforeend", `
        <div class="metric-row">
          <div class="metric-row__top">
            <div class="metric-row__icon"><svg viewBox="0 0 24 24" fill="none" stroke="#2D3536" stroke-width="2" stroke-linecap="round">${meta.icon}</svg></div>
            <div>
              <div class="metric-row__label">${meta.title}</div>
              <p class="metric-row__sub">${info.label}</p>
            </div>
            <div class="metric-row__pct">${info.pct}%</div>
          </div>
          <div class="bar-track"><div class="bar-fill ${meta.barClass}" data-pct="${info.pct}"></div></div>
        </div>
      `);
    });

    // trait rows
    const traitRows = $("#trait-rows");
    traitRows.innerHTML = "";
    TRAIT_ORDER.forEach((key) => {
      const pct = Math.round((scores[key] || 0) * 100);
      traitRows.insertAdjacentHTML("beforeend", `
        <div class="trait-row">
          <div class="trait-row__label">${traitLabel(key)}</div>
          <div class="bar-track"><div class="bar-fill bar-fill--euc" data-pct="${pct}"></div></div>
          <div class="trait-row__pct">${pct}%</div>
        </div>
      `);
    });

    // trigger entrance + bar animations after paint
    const heroEl = $("#result-hero");
    heroEl.classList.remove("is-in");
    void heroEl.offsetWidth; // restart animation on repeat visits
    requestAnimationFrame(() => {
      heroEl.classList.add("is-in");
      document.querySelectorAll(".bar-fill").forEach((bar) => {
        requestAnimationFrame(() => { bar.style.width = bar.dataset.pct + "%"; });
      });
    });
  }

  // nav "Home" always returns to home view
  document.querySelectorAll('[data-nav="home"]').forEach((el) => {
    el.addEventListener("click", (e) => { e.preventDefault(); resetToHome(); });
  });
  $('[data-action="get-started"]').addEventListener("click", () => {
    document.getElementById("file-input").click();
  });
})();