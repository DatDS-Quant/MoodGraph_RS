/**
 * MovieDetailModalComponent — Module Hộp Thoại Chi Tiết Phim & Provenance Explorer
 * Triết lý thiết kế: Taste-Skill & Impeccable (Chống tràn viền, cân đối Grid 12 cột, Accordion tối giản)
 */
(function(window, document) {
  'use strict';

  let isAccordionOpen = false;

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function toggleAccordion(forceState) {
    if (typeof forceState === 'boolean') {
      isAccordionOpen = forceState;
    } else {
      isAccordionOpen = !isAccordionOpen;
    }

    const bodyEl = document.getElementById('prov-accordion-body');
    const chevronEl = document.getElementById('prov-accordion-chevron');
    const triggerBtn = document.getElementById('prov-accordion-trigger');

    if (bodyEl) {
      if (isAccordionOpen) {
        bodyEl.classList.remove('max-h-0', 'opacity-0', 'pointer-events-none');
        bodyEl.classList.add('max-h-[600px]', 'opacity-100', 'pointer-events-auto');
      } else {
        bodyEl.classList.add('max-h-0', 'opacity-0', 'pointer-events-none');
        bodyEl.classList.remove('max-h-[600px]', 'opacity-100', 'pointer-events-auto');
      }
    }

    if (chevronEl) {
      if (isAccordionOpen) {
        chevronEl.classList.add('rotate-180');
      } else {
        chevronEl.classList.remove('rotate-180');
      }
    }

    if (triggerBtn) {
      triggerBtn.setAttribute('aria-expanded', isAccordionOpen ? 'true' : 'false');
    }
  }

  function open(movieIdOrObj) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.openMovieDetailModal === 'function') {
      const id = (typeof movieIdOrObj === 'object' && movieIdOrObj !== null) ? movieIdOrObj.movieId : movieIdOrObj;
      window.MoodGraphApp.openMovieDetailModal(id);
      return;
    }
    const modal = document.getElementById('movie-detail-modal');
    if (modal) modal.classList.add('active');
  }

  function close(event) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.closeMovieDetailModal === 'function') {
      window.MoodGraphApp.closeMovieDetailModal(event);
      return;
    }
    if (event && event.target && event.target !== event.currentTarget) return;
    const modal = document.getElementById('movie-detail-modal');
    if (modal) modal.classList.remove('active');
  }

  function switchTab(tabKey) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.switchProvenanceTab === 'function') {
      window.MoodGraphApp.switchProvenanceTab(tabKey);
    }
  }

  function toggleWatchlist(movieId) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.toggleWatchlist === 'function') {
      window.MoodGraphApp.toggleWatchlist(movieId);
    }
  }

  const MovieDetailModalComponent = {
    open,
    close,
    toggleAccordion,
    toggleProvenanceAccordion: toggleAccordion,
    switchTab,
    toggleWatchlist
  };

  window.MovieDetailModalComponent = MovieDetailModalComponent;

})(window, document);

