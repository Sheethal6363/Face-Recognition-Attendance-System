/**
 * VYRON — Main Script
 * Manages Cyberpunk Theme toggle (dark-theme / light-theme), mobile navigation, and telemetry updates.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Theme Management (Default: dark-theme)
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeLabel = document.getElementById('themeModeLabel');
  const themeIcon = document.getElementById('themeIcon');
  const savedTheme = localStorage.getItem('vyron_theme') || 'dark-theme';

  function applyTheme(theme) {
    if (theme === 'light-theme') {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark-theme');
      if (themeLabel) themeLabel.textContent = 'HOLO LIGHT';
      if (themeIcon) themeIcon.className = 'fas fa-sun neon-pink';
    } else {
      document.documentElement.classList.remove('light-theme');
      document.documentElement.classList.add('dark-theme');
      if (themeLabel) themeLabel.textContent = 'CYBER DARK';
      if (themeIcon) themeIcon.className = 'fas fa-moon neon-cyan';
    }
    localStorage.setItem('vyron_theme', theme);
  }

  // Apply initially
  applyTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const isLight = document.documentElement.classList.contains('light-theme');
      const newTheme = isLight ? 'dark-theme' : 'light-theme';
      applyTheme(newTheme);
    });
  }

  // Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 992 && 
          !sidebar.contains(e.target) && 
          !sidebarToggle.contains(e.target) && 
          sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
      }
    });
  }

  // Auto-dismiss alert messages
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => alert.remove());
    }
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });
});
