/**
 * VDP Direct Feed Import — Jazzmin admin fixes (loaded via JAZZMIN_SETTINGS custom_js).
 *
 * Context: django-jazzmin 3.0.2 targets Bootstrap 4; this project runs Django 6
 * with Bootstrap 5. AdminLTE 3 dropdown/tab JS therefore fails without these patches.
 *
 * Loaded after {% block extrajs %} in templates/admin/base.html so change_form.js
 * is parsed first; the jQuery .tab() bridge below must exist before its $(ready).
 */

// jazzmin/static/jazzmin/js/change_form.js calls $('a').tab('show') (removed in BS5).
(function ($) {
  if (!$ || $.fn.tab) {
    return;
  }
  $.fn.tab = function (action) {
    if (action === 'show') {
      this.each(function () {
        activateJazzyTab(this);
      });
    }
    return this;
  };
})(window.jQuery);

/** Switch horizontal change-form tabs without Bootstrap Tab (see horizontal_tabs.html). */
function activateJazzyTab(trigger) {
  const tabList = document.getElementById('jazzy-tabs');
  if (!tabList || !trigger) {
    return;
  }

  const href = trigger.getAttribute('href');
  if (!href || !href.startsWith('#')) {
    return;
  }

  tabList.querySelectorAll('.nav-link').forEach((link) => {
    link.classList.remove('active');
    link.setAttribute('aria-selected', 'false');
  });
  trigger.classList.add('active');
  trigger.setAttribute('aria-selected', 'true');

  // Tab panes follow the tab list in jazzmin/includes/horizontal_tabs.html.
  const content = tabList.nextElementSibling;
  if (!content || !content.classList.contains('tab-content')) {
    return;
  }

  content.querySelectorAll('.tab-pane').forEach((pane) => {
    pane.classList.remove('active', 'show');
  });

  const pane = content.querySelector(href);
  if (pane) {
    pane.classList.add('active', 'show');
  }

  // Preserve tab in URL (same behaviour as jazzmin change_form.js).
  if (history.pushState) {
    history.pushState(null, null, href);
  } else {
    location.hash = href;
  }
  window.dispatchEvent(new Event('resize'));
}

function initJazzyChangeFormTabs() {
  const tabList = document.getElementById('jazzy-tabs');
  if (!tabList) {
    return;
  }

  tabList.querySelectorAll('.nav-link').forEach((trigger) => {
    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      activateJazzyTab(trigger);
    });
  });

  // Open the tab that contains validation errors first.
  const errors = document.querySelectorAll('.change-form .errorlist li');
  if (errors.length) {
    const pane = errors[0].closest('.tab-pane');
    const paneId = pane?.getAttribute('id');
    if (paneId) {
      const trigger = tabList.querySelector(`[href="#${paneId}"]`);
      if (trigger) {
        activateJazzyTab(trigger);
      }
    }
    return;
  }

  // Restore tab from URL hash on reload.
  const hash = window.location.hash;
  if (hash) {
    const trigger = tabList.querySelector(`[href="${hash}"]`);
    if (trigger) {
      activateJazzyTab(trigger);
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Replace default Jazzmin footer version text.
  const footer = document.querySelector('.main-footer > div');
  if (footer) {
    const link = document.createElement('a');
    link.href = 'https://github.com/paultumabini';
    link.textContent = '@paultumabini';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    footer.textContent = '';
    footer.appendChild(link);
  }

  initJazzyChangeFormTabs();

  // Django admin logout requires POST + CSRF (templates/admin/base.html account panel).
  const logoutForm = document.getElementById('logout-form');
  const logoutLink = document.getElementById('jazzy-logout-link');
  if (logoutLink && logoutForm) {
    logoutLink.addEventListener('click', (event) => {
      event.preventDefault();
      logoutForm.submit();
    });
  }
});
