/**
 * VYRON — Main System Controller
 * Handles Multi-Device navigation, theme toggling, PWA service worker,
 * network pairing modal, and Fullscreen Kiosk Mode.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Theme Management (Default: dark-theme)
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
      if (themeIcon) themeIcon.className = 'fas fa-moon neon-pink';
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

  // 2. Mobile Sidebar & Backdrop Drawer Navigation
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('show');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
    document.body.classList.add('sidebar-open');
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('show');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
    document.body.classList.remove('sidebar-open');
  }

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    if (sidebarBackdrop) {
      sidebarBackdrop.addEventListener('click', closeSidebar);
    }

    // Close when navigating on mobile
    const navLinks = sidebar.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 992) {
          closeSidebar();
        }
      });
    });
  }

  // 3. Multi-Device Network Connect & QR Code Kiosk Modal
  const connectDeviceBtn = document.getElementById('connectDeviceBtn');
  const deviceConnectModal = document.getElementById('deviceConnectModal');
  const closeModalBtn = document.getElementById('closeDeviceModalBtn');
  const copyUrlBtn = document.getElementById('copyNetworkUrlBtn');
  const qrContainer = document.getElementById('modalQrCode');
  const networkUrlText = document.getElementById('networkUrlText');
  const kioskFullscreenBtn = document.getElementById('kioskFullscreenBtn');

  let currentNetworkUrl = window.location.origin + '/live-attendance';

  async function loadNetworkInfo() {
    try {
      const res = await fetch('/api/system-network');
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          // If accessing over localhost, use local LAN IP so phones on the same Wi-Fi can connect
          if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            currentNetworkUrl = `http://${data.local_ip}:${data.port}/live-attendance`;
          } else {
            currentNetworkUrl = window.location.origin + '/live-attendance';
          }
        }
      }
    } catch (e) {
      console.warn('Network info discovery failed, using origin:', e);
      currentNetworkUrl = window.location.origin + '/live-attendance';
    }

    if (networkUrlText) {
      networkUrlText.textContent = currentNetworkUrl;
    }

    // Render QR Code using reliable SVG QR image endpoint with fallback
    if (qrContainer) {
      const encodedUrl = encodeURIComponent(currentNetworkUrl);
      qrContainer.innerHTML = `
        <div style="background: #ffffff; padding: 12px; border-radius: 10px; display: inline-block; box-shadow: 0 0 20px rgba(0, 245, 255, 0.4);">
          <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodedUrl}&bgcolor=ffffff&color=09050c&margin=0" 
               alt="Scan to Connect Scanner Kiosk" 
               style="display: block; width: 170px; height: 170px; border-radius: 4px;"
               onerror="this.onerror=null; this.parentElement.innerHTML='<div style=\\'padding:20px; color:#09050C; font-weight:bold;\\'>Scan QR Unavailable - Use URL Above</div>';" />
        </div>
      `;
    }
  }

  if (connectDeviceBtn && deviceConnectModal) {
    connectDeviceBtn.addEventListener('click', () => {
      deviceConnectModal.classList.add('active');
      loadNetworkInfo();
    });

    if (closeModalBtn) {
      closeModalBtn.addEventListener('click', () => {
        deviceConnectModal.classList.remove('active');
      });
    }

    deviceConnectModal.addEventListener('click', (e) => {
      if (e.target === deviceConnectModal) {
        deviceConnectModal.classList.remove('active');
      }
    });

    if (copyUrlBtn) {
      copyUrlBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(currentNetworkUrl).then(() => {
          copyUrlBtn.innerHTML = '<i class="fas fa-check"></i> COPIED!';
          setTimeout(() => {
            copyUrlBtn.innerHTML = '<i class="fas fa-copy"></i> COPY LINK';
          }, 2000);
        });
      });
    }
  }

  // 4. Kiosk Mode Fullscreen Toggle
  if (kioskFullscreenBtn) {
    kioskFullscreenBtn.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
          console.warn('Fullscreen request failed:', err);
        });
        kioskFullscreenBtn.innerHTML = '<i class="fas fa-compress"></i> EXIT KIOSK FULLSCREEN';
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        }
        kioskFullscreenBtn.innerHTML = '<i class="fas fa-expand"></i> LAUNCH FULLSCREEN KIOSK';
      }
    });
  }

  // 5. Register Progressive Web App (PWA) Service Worker
  if ('serviceWorker' in navigator && window.location.protocol.startsWith('http')) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').then((reg) => {
        console.log('[*] VYRON Service Worker active for multi-device performance.');
      }).catch((err) => {
        console.warn('Service worker registration note:', err);
      });
    });
  }

  // 6. Auto-dismiss alert messages
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
