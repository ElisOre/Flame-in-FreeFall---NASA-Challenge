
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

