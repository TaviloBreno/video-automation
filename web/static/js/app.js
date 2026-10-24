/**
 * Studio AI Video - Frontend Orchestration
 */

let currentJobId = null;
let pollInterval = null;
let appConfig = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  setupEventListeners();
  await loadConfig();
  await loadRecentJobs();
}

function setupEventListeners() {
  // Slider & Duração
  const durationRange = document.getElementById("durationRange");
  const durationBadge = document.getElementById("durationBadge");
  const pillBtns = document.querySelectorAll(".pill-btn");

  durationRange.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    updateDurationDisplay(val);
    pillBtns.forEach((btn) => {
      btn.classList.toggle("active", parseFloat(btn.dataset.min) === val);
    });
  });

  pillBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      pillBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const val = parseFloat(btn.dataset.min);
      durationRange.value = val;
      updateDurationDisplay(val);
    });
  });

  // Formulário de Criação
  const createForm = document.getElementById("createVideoForm");
  createForm.addEventListener("submit", handleCreateVideo);

  // Botão Cancelar
  document.getElementById("btnCancelJob").addEventListener("click", handleCancelJob);

  // Tabs
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const tabId = btn.dataset.tab;
      const targetPane = document.getElementById(tabId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Botão Detectar Cortes Virais
  document.getElementById("btnDetectShorts").addEventListener("click", handleDetectShorts);

  // Histórico Modal
  const modal = document.getElementById("historyModal");
  document.getElementById("btnHistory").addEventListener("click", () => {
    modal.classList.remove("hidden");
    loadHistoryList();
  });
  document.getElementById("btnCloseHistory").addEventListener("click", () => {
    modal.classList.add("hidden");
  });
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });
}

function updateDurationDisplay(minutes) {
  const badge = document.getElementById("durationBadge");
  const sec = Math.round(minutes * 60);
  badge.textContent = `${minutes.toFixed(1)} min (${sec}s)`;
}

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    appConfig = await res.json();

    // Preenche Paletas
    const paletteList = document.getElementById("paletteList");
    paletteList.innerHTML = "";
    appConfig.palettes.forEach((p, idx) => {
      const isDefault = p.id === appConfig.default_palette;
      const div = document.createElement("div");
      div.className = `palette-item ${isDefault ? "active" : ""}`;
      div.dataset.id = p.id;
      div.innerHTML = `
        <div class="palette-swatches">
          <span class="swatch" style="background:${p.primary}"></span>
          <span class="swatch" style="background:${p.accent}"></span>
          <span class="swatch" style="background:${p.background}"></span>
        </div>
        <span class="palette-name">${p.id}</span>
      `;
      div.addEventListener("click", () => {
        document.querySelectorAll(".palette-item").forEach((el) => el.classList.remove("active"));
        div.classList.add("active");
      });
      paletteList.appendChild(div);
    });

    // Preenche Vozes
    const voiceSelect = document.getElementById("voiceSelect");
    voiceSelect.innerHTML = "";
    appConfig.voices.forEach((v) => {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = `${v.name}`;
      if (v.id === appConfig.default_voice) opt.selected = true;
      voiceSelect.appendChild(opt);
    });

    // Preenche Músicas de Fundo Royalty-Free
    const bgMusicSelect = document.getElementById("bgMusicSelect");
    if (bgMusicSelect && appConfig.bg_music_options) {
      bgMusicSelect.innerHTML = "";
      appConfig.bg_music_options.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.name;
        if (m.id === appConfig.default_bg_music) opt.selected = true;
        bgMusicSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Erro ao carregar configurações:", err);
  }
}

async function handleCreateVideo(e) {
  e.preventDefault();

  const topic = document.getElementById("topicInput").value.trim();
  const minutes = parseFloat(document.getElementById("durationRange").value);
  const voice = document.getElementById("voiceSelect").value;
  const legendStyle = document.getElementById("legendStyleSelect").value;
  const research = document.getElementById("researchCheck").checked;
  const bgMusic = document.getElementById("bgMusicSelect") ? document.getElementById("bgMusicSelect").value : "space_ambient";
  const enableImages = document.getElementById("enableImagesCheck") ? document.getElementById("enableImagesCheck").checked : true;

  const activePaletteEl = document.querySelector(".palette-item.active");
  const palette = activePaletteEl ? activePaletteEl.dataset.id : appConfig.default_palette;

  if (!topic) {
    alert("Por favor, digite um tema para o vídeo.");
    return;
  }

  // Prepara UI
  document.getElementById("emptyStateCard").classList.add("hidden");
  document.getElementById("videoReadyCard").classList.add("hidden");
  const progressCard = document.getElementById("progressCard");
  progressCard.classList.remove("hidden");

  document.getElementById("btnSubmit").disabled = true;
  document.getElementById("logContainer").innerHTML = "";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic,
        minutes,
        palette,
        voice,
        legend_style: legendStyle,
        research,
        bg_music: bgMusic,
        enable_images: enableImages,
      }),
    });

    const data = await res.json();
    if (res.ok && data.job_id) {
      currentJobId = data.job_id;
      startPolling(currentJobId);
    } else {
      alert("Erro ao iniciar geração: " + (data.error || "Erro desconhecido"));
      resetUI();
    }
  } catch (err) {
    alert("Falha de conexão com o servidor local.");
    resetUI();
  }
}

function startPolling(jobId) {
  if (pollInterval) clearInterval(pollInterval);

  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/status/${jobId}`);
      if (!res.ok) return;

      const status = await res.json();
      updateProgressUI(status);

      if (status.status === "completed") {
        clearInterval(pollInterval);
        onJobCompleted(status);
      } else if (status.status === "failed" || status.status === "cancelled") {
        clearInterval(pollInterval);
        document.getElementById("btnSubmit").disabled = false;
        alert(`O processo foi interrompido: ${status.stage}`);
      }
    } catch (err) {
      console.warn("Erro ao verificar status:", err);
    }
  }, 1200);
}

function updateProgressUI(status) {
  const pct = Math.max(0, Math.min(100, status.progress || 0));
  document.getElementById("progressBar").style.width = `${pct}%`;
  document.getElementById("progressPercentage").textContent = `${Math.round(pct)}%`;
  document.getElementById("stageDescription").textContent = status.stage || "Processando...";

  // Atualiza logs
  if (status.logs && status.logs.length) {
    const logBox = document.getElementById("logContainer");
    logBox.innerHTML = status.logs.map((l) => `<div>${escapeHtml(l)}</div>`).join("");
    logBox.scrollTop = logBox.scrollHeight;
  }

  // Atualiza Stepper
  updateStepper(pct);
}

function updateStepper(pct) {
  const steps = [
    { id: "step1", threshold: 5 },
    { id: "step2", threshold: 25 },
    { id: "step3", threshold: 45 },
    { id: "step4", threshold: 85 },
    { id: "step5", threshold: 98 },
  ];

  steps.forEach((st, idx) => {
    const el = document.getElementById(st.id);
    if (!el) return;
    el.classList.remove("active", "completed");

    if (pct >= st.threshold) {
      el.classList.add("completed");
    } else if (idx === 0 || pct >= steps[idx - 1].threshold) {
      el.classList.add("active");
    }
  });
}

async function handleCancelJob() {
  if (!currentJobId) return;
  if (!confirm("Deseja realmente cancelar a geração atual?")) return;

  try {
    await fetch(`/api/jobs/${currentJobId}/cancel`, { method: "POST" });
  } catch (err) {
    console.error("Erro ao cancelar:", err);
  }
}

function onJobCompleted(job) {
  document.getElementById("progressCard").classList.add("hidden");
  document.getElementById("videoReadyCard").classList.remove("hidden");
  document.getElementById("btnSubmit").disabled = false;

  const manifest = job.manifest;
  if (!manifest) return;

  // Carrega Player Principal (YouTube)
  const videoPlayer = document.getElementById("mainVideoPlayer");
  videoPlayer.src = `/media/${currentJobId}/video.mp4`;
  videoPlayer.load();

  document.getElementById("videoTitleDisplay").textContent = manifest.title || manifest.topic;
  document.getElementById("videoDurationDisplay").textContent = `Duração: ${(manifest.actual_seconds / 60).toFixed(1)} min (${manifest.actual_seconds}s)`;

  const btnDl = document.getElementById("btnDownloadMain");
  btnDl.href = `/media/${currentJobId}/video.mp4`;
  btnDl.download = `${sanitizeFilename(manifest.title || "video")}_youtube.mp4`;

  // Renderiza Roteiro e Capítulos
  renderChapters(manifest.chapters || []);
  renderSources(manifest.sources || []);

  // Renderiza Pacote Completo de SEO & YouTube
  renderSeoMetadata(manifest.youtube_metadata || {}, manifest);

  // Limpa candidatos anteriores e busca Shorts já gerados
  document.getElementById("viralCandidatesContainer").innerHTML = "";
  loadExistingShorts(currentJobId);
}

function renderChapters(chapters) {
  const container = document.getElementById("chaptersList");
  container.innerHTML = "";

  let totalWords = 0;
  chapters.forEach((ch, idx) => {
    totalWords += (ch.narration || "").split(/\s+/).length;
    const div = document.createElement("div");
    div.className = "chapter-box";

    let imageHtml = "";
    if (ch.image_path || ch.image_url) {
      const imgSource = ch.image_path ? `/media/${currentJobId}/${ch.image_path.split(/[\\/]/).pop()}` : ch.image_url;
      const creditText = escapeHtml(ch.image_credit || "Imagem científica sob licença livre");
      imageHtml = `
        <div class="chapter-image-bar">
          <img src="${imgSource}" alt="${escapeHtml(ch.title)}" class="chapter-thumb-img" onerror="this.style.display='none'">
          <div class="chapter-image-info">
            <span>📷 <b>Imagem Ilustrativa:</b> ${creditText}</span>
          </div>
        </div>
      `;
    }

    div.innerHTML = `
      <div class="chapter-box-header">
        <span class="chapter-title">${idx + 1}. ${escapeHtml(ch.title)}</span>
        <span class="chapter-timestamp">${formatTime(ch.start)} - ${formatTime(ch.start + ch.duration)}</span>
      </div>
      <p class="chapter-narration">${escapeHtml(ch.narration)}</p>
      ${imageHtml}
    `;
    div.addEventListener("click", () => {
      const player = document.getElementById("mainVideoPlayer");
      player.currentTime = ch.start;
      player.play();
      document.querySelector('[data-tab="tabYoutube"]').click();
    });
    container.appendChild(div);
  });

  document.getElementById("scriptWordCount").textContent = `${totalWords} palavras narradas`;
}

function renderSeoMetadata(seo, manifest) {
  // 1. Títulos Alternativos de Alto CTR
  const titlesList = document.getElementById("seoTitlesList");
  titlesList.innerHTML = "";
  const titles = seo.titles && seo.titles.length ? seo.titles : [manifest.title || manifest.topic];
  titles.forEach((t) => {
    const row = document.createElement("div");
    row.className = "seo-title-row";
    row.innerHTML = `
      <span>${escapeHtml(t)}</span>
      <button class="btn-copy">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span>Copiar</span>
      </button>
    `;
    const btn = row.querySelector(".btn-copy");
    btn.addEventListener("click", () => copyToClipboard(t, btn));
    titlesList.appendChild(row);
  });

  // 2. Descrição Completa
  const descArea = document.getElementById("seoDescriptionArea");
  const fullDesc = seo.description || (manifest.chapters || []).map((c, i) => `${formatTime(c.start)} ${c.title}`).join("\n");
  descArea.value = fullDesc;
  const btnCopyDesc = document.getElementById("btnCopyDescription");
  btnCopyDesc.onclick = () => copyToClipboard(fullDesc, btnCopyDesc);

  // 3. Tags & Palavras-Chave
  const tagsPills = document.getElementById("seoTagsPills");
  tagsPills.innerHTML = "";
  const tags = seo.tags || [];
  tags.forEach((tag) => {
    const span = document.createElement("span");
    span.className = "tag-pill";
    span.textContent = tag;
    tagsPills.appendChild(span);
  });
  const btnCopyTags = document.getElementById("btnCopyTags");
  btnCopyTags.onclick = () => copyToClipboard(tags.join(", "), btnCopyTags);

  // 4. Hashtags
  const hashtagsPills = document.getElementById("seoHashtagsPills");
  hashtagsPills.innerHTML = "";
  const hashtags = seo.hashtags || [];
  hashtags.forEach((h) => {
    const span = document.createElement("span");
    span.className = "tag-pill";
    span.textContent = h.startsWith("#") ? h : `#${h}`;
    hashtagsPills.appendChild(span);
  });
  const btnCopyHash = document.getElementById("btnCopyHashtags");
  btnCopyHash.onclick = () => copyToClipboard(hashtags.map((h) => (h.startsWith("#") ? h : `#${h}`)).join(" "), btnCopyHash);

  // 5. Conceito de Thumbnail
  const thumbConcept = document.getElementById("seoThumbnailConcept");
  thumbConcept.textContent = seo.thumbnail_concept || "Crie uma imagem de alto contraste com o elemento central em grande destaque e texto com menos de 5 palavras.";
}

function renderSources(sources) {
  const container = document.getElementById("sourcesContainer");
  container.innerHTML = "";

  if (!sources || !sources.length) {
    container.innerHTML = "<p style='color:var(--text-dim);font-size:13px;'>Nenhuma pesquisa web realizada.</p>";
    return;
  }

  sources.forEach((s) => {
    const div = document.createElement("div");
    div.className = "source-item";
    div.innerHTML = `
      <b>[${escapeHtml(s.id)}] ${escapeHtml(s.publisher || "Fonte")}</b>
      <a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.title)}</a>
    `;
    container.appendChild(div);
  });
}

// ---------------------------------------------------------------------------
// Cortes Virais (Shorts 9:16)
// ---------------------------------------------------------------------------

async function handleDetectShorts() {
  if (!currentJobId) return;

  const btn = document.getElementById("btnDetectShorts");
  btn.disabled = true;
  btn.innerHTML = `<span class="magic-icon">⏳</span> Analisando Roteiro com IA...`;

  try {
    const res = await fetch(`/api/jobs/${currentJobId}/detect_shorts`, { method: "POST" });
    const data = await res.json();

    if (res.ok && data.candidates) {
      renderViralCandidates(data.candidates);
    } else {
      alert("Erro ao detectar trechos virais: " + (data.error || "Erro desconhecido"));
    }
  } catch (err) {
    alert("Falha na comunicação com o servidor.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="magic-icon">✨</span> Detectar Melhores Trechos com IA`;
  }
}

function renderViralCandidates(candidates) {
  const container = document.getElementById("viralCandidatesContainer");
  container.innerHTML = "";

  candidates.forEach((c) => {
    const card = document.createElement("div");
    card.className = "candidate-card";
    card.innerHTML = `
      <div>
        <div class="candidate-top">
          <h4 class="candidate-title">${escapeHtml(c.title)}</h4>
          <span class="viral-badge">🔥 ${c.viral_score}% Viral</span>
        </div>
        <p class="candidate-hook">"${escapeHtml(c.hook)}"</p>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
          <span class="candidate-times">⏱️ ${formatTime(c.start_time)} até ${formatTime(c.end_time)}</span>
          <span class="candidate-times">${Math.round(c.duration)}s</span>
        </div>
        <button class="btn-render-short">Gerar Short Vertical (9:16)</button>
      </div>
    `;

    const btn = card.querySelector(".btn-render-short");
    btn.addEventListener("click", () => renderSingleShort(c, btn));

    container.appendChild(card);
  });
}

async function renderSingleShort(candidate, btnElement) {
  if (!currentJobId) return;

  btnElement.disabled = true;
  btnElement.textContent = "⏳ Recortando e aplicando legendas...";

  try {
    const res = await fetch(`/api/jobs/${currentJobId}/render_short`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start_time: candidate.start_time,
        end_time: candidate.end_time,
        title: candidate.title,
        legend_style: document.getElementById("legendStyleSelect").value,
      }),
    });

    const data = await res.json();
    if (res.ok && data.clip) {
      btnElement.textContent = "✅ Pronto!";
      addShortToGrid(data.clip);
      updateShortsBadgeCount();
    } else {
      alert("Falha ao gerar Short: " + (data.error || "Erro desconhecido"));
      btnElement.disabled = false;
      btnElement.textContent = "Tentar Novamente";
    }
  } catch (err) {
    alert("Erro ao conectar ao servidor.");
    btnElement.disabled = false;
    btnElement.textContent = "Tentar Novamente";
  }
}

async function loadExistingShorts(jobId) {
  try {
    const res = await fetch(`/api/jobs/${jobId}/shorts`);
    if (!res.ok) return;
    const data = await res.json();
    const grid = document.getElementById("renderedShortsGrid");
    grid.innerHTML = "";
    (data.shorts || []).forEach((s) => {
      addShortToGrid({
        file: s.file,
        url: s.url,
        title: s.file,
        social_metadata: s.social_metadata,
      });
    });
    updateShortsBadgeCount();
  } catch (err) {
    console.error("Erro ao carregar Shorts existentes:", err);
  }
}

function addShortToGrid(clip) {
  const grid = document.getElementById("renderedShortsGrid");
  const card = document.createElement("div");
  card.className = "short-card";
  const videoUrl = clip.url || `/media/${currentJobId}/shorts/${clip.file}`;

  let socialHtml = "";
  const sm = clip.social_metadata;
  if (sm) {
    const tiktokText = (sm.tiktok && sm.tiktok.caption) || "";
    const reelsText = (sm.instagram_reels && sm.instagram_reels.caption) || "";
    const ytText = sm.youtube_shorts ? `${sm.youtube_shorts.title || ""}\n\n${sm.youtube_shorts.description || ""}\n\n${(sm.youtube_shorts.hashtags || []).join(" ")}`.trim() : "";

    socialHtml = `
      <div class="short-social-box">
        <div class="social-pills-nav">
          <button type="button" class="social-pill-btn active" data-platform="tiktok">TikTok</button>
          <button type="button" class="social-pill-btn" data-platform="reels">Reels</button>
          <button type="button" class="social-pill-btn" data-platform="shorts">Shorts</button>
        </div>
        <div class="social-caption-display" data-current="tiktok">${escapeHtml(tiktokText)}</div>
        <button type="button" class="btn-copy-social">📋 Copiar para TikTok</button>
      </div>
    `;
  }

  card.innerHTML = `
    <div class="short-player-wrapper">
      <video src="${videoUrl}" controls playsinline preload="metadata"></video>
    </div>
    <div class="short-actions">
      <span style="font-size:11px;color:var(--text-dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px;">
        ${escapeHtml(clip.title || clip.file)}
      </span>
      <a href="${videoUrl}" download="${clip.file}">Baixar 9:16</a>
    </div>
    ${socialHtml}
  `;

  if (sm) {
    const pillBtns = card.querySelectorAll(".social-pill-btn");
    const display = card.querySelector(".social-caption-display");
    const btnCopy = card.querySelector(".btn-copy-social");

    const platformTexts = {
      tiktok: (sm.tiktok && sm.tiktok.caption) || "",
      reels: (sm.instagram_reels && sm.instagram_reels.caption) || "",
      shorts: sm.youtube_shorts ? `${sm.youtube_shorts.title || ""}\n\n${sm.youtube_shorts.description || ""}\n\n${(sm.youtube_shorts.hashtags || []).join(" ")}`.trim() : "",
    };

    pillBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        pillBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const plat = btn.dataset.platform;
        display.dataset.current = plat;
        display.textContent = platformTexts[plat] || "";
        const label = plat === "tiktok" ? "TikTok" : plat === "reels" ? "Instagram Reels" : "YouTube Shorts";
        btnCopy.textContent = `📋 Copiar para ${label}`;
      });
    });

    btnCopy.addEventListener("click", () => {
      const plat = display.dataset.current;
      const textToCopy = platformTexts[plat] || "";
      copyToClipboard(textToCopy, btnCopy);
    });
  }

  grid.prepend(card);
}

function copyToClipboard(text, btnElement) {
  if (!text) return;

  const originalContent = btnElement.innerHTML;
  const doFeedback = () => {
    btnElement.classList.add("copied");
    btnElement.innerHTML = `<span>Copiado! ✓</span>`;
    setTimeout(() => {
      btnElement.classList.remove("copied");
      btnElement.innerHTML = originalContent;
    }, 2200);
  };

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(doFeedback).catch(() => {
      fallbackCopy(text);
      doFeedback();
    });
  } else {
    fallbackCopy(text);
    doFeedback();
  }
}

function fallbackCopy(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.left = "-9999px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    document.execCommand("copy");
  } catch (err) {
    console.error("Falha ao copiar:", err);
  }
  document.body.removeChild(textArea);
}

function updateShortsBadgeCount() {
  const count = document.querySelectorAll("#renderedShortsGrid .short-card").length;
  document.getElementById("shortsCountBadge").textContent = count;
}

// ---------------------------------------------------------------------------
// Histórico
// ---------------------------------------------------------------------------

async function loadRecentJobs() {
  try {
    const res = await fetch("/api/jobs");
    const data = await res.json();
    if (data.jobs && data.jobs.length > 0) {
      // Se houver job recente já concluído, podemos abrir direto
      const latest = data.jobs[0];
      if (latest.has_video) {
        currentJobId = latest.id;
        const statusRes = await fetch(`/api/status/${latest.id}`);
        if (statusRes.ok) {
          const status = await statusRes.json();
          document.getElementById("emptyStateCard").classList.add("hidden");
          onJobCompleted(status);
        }
      }
    }
  } catch (err) {
    console.warn("Sem histórico carregado:", err);
  }
}

async function loadHistoryList() {
  const container = document.getElementById("historyList");
  container.innerHTML = "Carregando...";

  try {
    const res = await fetch("/api/jobs");
    const data = await res.json();
    container.innerHTML = "";

    if (!data.jobs || !data.jobs.length) {
      container.innerHTML = "<p style='color:var(--text-dim)'>Nenhum vídeo no histórico.</p>";
      return;
    }

    data.jobs.forEach((j) => {
      const div = document.createElement("div");
      div.className = "history-item";
      div.innerHTML = `
        <div>
          <strong>${escapeHtml(j.title || j.topic)}</strong>
          <div style="font-size:12px;color:var(--text-dim);margin-top:4px;">
            ${j.minutes} min • Status: ${j.status}
          </div>
        </div>
        <button class="btn-secondary" style="padding:6px 12px;font-size:12px;">Abrir</button>
      `;
      div.addEventListener("click", async () => {
        document.getElementById("historyModal").classList.add("hidden");
        currentJobId = j.id;
        const statusRes = await fetch(`/api/status/${j.id}`);
        if (statusRes.ok) {
          const status = await statusRes.json();
          document.getElementById("emptyStateCard").classList.add("hidden");
          onJobCompleted(status);
        }
      });
      container.appendChild(div);
    });
  } catch (err) {
    container.innerHTML = "Erro ao carregar histórico.";
  }
}

function resetUI() {
  document.getElementById("btnSubmit").disabled = false;
  document.getElementById("progressCard").classList.add("hidden");
  document.getElementById("emptyStateCard").classList.remove("hidden");
}

function formatTime(seconds) {
  if (isNaN(seconds) || seconds === null) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function sanitizeFilename(text) {
  return text.toLowerCase().replace(/[^\w\s-]/g, "").replace(/\s+/g, "_").slice(0, 40);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}
