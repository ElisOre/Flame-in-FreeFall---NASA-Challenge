
// always start at the top (hero), ignoring #hash and the browser's saved scroll position
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
if (location.hash) history.replaceState(null, '', location.pathname + location.search);
window.scrollTo({ top: 0, left: 0, behavior: 'instant' });

document.addEventListener('DOMContentLoaded', () => {
  const HOVER_DELAY = 400; // ms antes de cambiar al articulo seleccionado.

  const searchInput = document.getElementById('article-search');
  const noResults   = document.getElementById('no-results');
  const layout      = document.querySelector('.articles-layout');
  const items       = document.querySelectorAll('.article-item');
  const panels      = document.querySelectorAll('.article-panel');

  let hoverTimer = null;

  function showArticle(id) {
    items.forEach(i => i.classList.toggle('active', i.dataset.target === id));
    panels.forEach(p => p.classList.toggle('active', p.id === id));
  }

  items.forEach(item => {
    const id = item.dataset.target;

    // Cambia articulo despues de mantener 400ms el mouse sobre el titulo
    item.addEventListener('mouseenter', () => {
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => showArticle(id), HOVER_DELAY);
    });
    item.addEventListener('mouseleave', () => clearTimeout(hoverTimer));

    // Cambio inmediato al hacer click. Excepcion para moviles.
    item.addEventListener('click', () => {
      clearTimeout(hoverTimer);
      showArticle(id);
    });
    item.addEventListener('focus', () => {
      clearTimeout(hoverTimer);
      showArticle(id);
    });
  });

  // Buscador - filtra los articulos
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase();
      let visible = 0;
      let firstVisibleId = null;
      let activeStillVisible = false;

      items.forEach(item => {
        const panel = document.getElementById(item.dataset.target);
        const text = (item.textContent + ' ' + panel.textContent).toLowerCase();
        const match = text.includes(q);

        item.parentElement.classList.toggle('hidden', !match);

        if (match) {
          visible++;
          if (!firstVisibleId) firstVisibleId = item.dataset.target;
          if (item.classList.contains('active')) activeStillVisible = true;
        }
      });

      if (visible > 0 && !activeStillVisible) showArticle(firstVisibleId);

      layout.classList.toggle('hidden', visible === 0);
      noResults.hidden = visible > 0;
    });
  }
});


//Video controls (YouTube IFrame API) - hecho con IA
(function () {
  const AUTO_HIDE_MS = 3000;   // ms para que el overlay desaparezca automaticamente

  const btnPlay    = document.getElementById('btn-play');
  const btnMute    = document.getElementById('btn-mute');
  const btnOverlay = document.getElementById('btn-overlay');
  const content    = document.querySelector('.hero-content');
  if (!btnPlay || !btnMute || !btnOverlay || !content) return;

  let player = null;
  let hideTimer = null;
  let autoHideStarted = false;

  // Texto de l ahero section
  function setOverlay(show) {
    content.classList.toggle('is-hidden', !show);
    btnOverlay.classList.toggle('is-on', show);
    btnOverlay.setAttribute('aria-pressed', String(show));
  }

  function startAutoHide() {
    if (autoHideStarted) return;
    autoHideStarted = true;
    hideTimer = setTimeout(() => setOverlay(false), AUTO_HIDE_MS);
  }

  btnOverlay.addEventListener('click', () => {
    clearTimeout(hideTimer);
    autoHideStarted = true;
    setOverlay(content.classList.contains('is-hidden'));
  });

  // botones del overlay mute y pause
  function syncButtons() {
    if (!player) return;
    const state  = player.getPlayerState();
    const paused = state === YT.PlayerState.PAUSED;
    const muted  = player.isMuted();

    btnPlay.classList.toggle('is-paused', paused);
    btnPlay.setAttribute('aria-label', paused ? 'Play video' : 'Pause video');

    btnMute.classList.toggle('is-off', muted);
    btnMute.setAttribute('aria-label', muted ? 'Unmute video' : 'Mute video');

    if (state === YT.PlayerState.PLAYING) startAutoHide();
  }

  window.onYouTubeIframeAPIReady = function () {
    player = new YT.Player('hero-player', {
      events: { onReady: syncButtons, onStateChange: syncButtons }
    });
  };

  btnPlay.addEventListener('click', () => {
    if (!player) return;
    if (player.getPlayerState() === YT.PlayerState.PAUSED) player.playVideo();
    else player.pauseVideo();
  });

  btnMute.addEventListener('click', () => {
    if (!player) return;
    if (player.isMuted()) player.unMute();
    else player.mute();
    syncButtons();
  });

  // safety net: if the YouTube API never loads (blocked, offline), still fade the titles - IA generated
  setTimeout(() => { if (!player) startAutoHide(); }, 5000);

  const tag = document.createElement('script');
  tag.src = 'https://www.youtube.com/iframe_api';
  document.head.appendChild(tag);
})();
