/* Yerbateca Lightbox — click illustration to zoom */
(function() {
  'use strict';

  var overlay = null;

  function create() {
    overlay = document.createElement('div');
    overlay.className = 'lightbox';
    overlay.innerHTML = '<button class="lightbox-close" aria-label="Cerrar">&times;</button>'
      + '<img alt="">'
      + '<div class="lightbox-caption"></div>';
    document.body.appendChild(overlay);

    overlay.addEventListener('click', function(e) {
      if (e.target === overlay || e.target.classList.contains('lightbox-close')) close();
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') close();
    });
  }

  function open(src, caption) {
    if (!overlay) create();
    overlay.querySelector('img').src = src;
    overlay.querySelector('.lightbox-caption').textContent = caption || '';
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    if (!overlay) return;
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  document.addEventListener('click', function(e) {
    var img = e.target.closest('.illustration');
    if (!img) return;
    e.preventDefault();
    var full = img.dataset.full || img.src;
    var caption = img.alt || '';
    open(full, caption);
  });
})();
