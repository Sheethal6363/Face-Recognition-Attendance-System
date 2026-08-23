/**
 * VYRON — Multi-Device Camera & Biometric Optical HUD Controller
 * Supports Desktop, Laptop, iOS / Android Smartphones, Tablets & Attendance Kiosks.
 */

class FaceCameraManager {
  constructor(options = {}) {
    this.videoElement = document.getElementById(options.videoId || 'webcamVideo');
    this.canvasElement = document.getElementById(options.canvasId || 'captureCanvas');
    this.statusElement = document.getElementById(options.statusId || 'cameraStatus');
    this.previewImg = document.getElementById(options.previewId || 'capturedPreview');
    this.imageDataInput = document.getElementById(options.inputId || 'imageDataInput');
    this.scanLine = document.getElementById(options.scanLineId || 'hudScanLine');
    this.deviceSelectElement = document.getElementById(options.deviceSelectId || 'cameraDeviceSelect');
    this.torchBtnElement = document.getElementById(options.torchBtnId || 'toggleTorchBtn');
    
    this.stream = null;
    this.isScanning = false;
    this.scanInterval = null;
    this.facingMode = options.facingMode || 'user'; // 'user' (front) or 'environment' (back)
    this.selectedDeviceId = null;
    this.isTorchOn = false;
    this.availableDevices = [];
    
    // Ensure iOS / Mobile WebKit plays inline without kicking to native fullscreen
    if (this.videoElement) {
      this.videoElement.setAttribute('playsinline', 'true');
      this.videoElement.setAttribute('webkit-playsinline', 'true');
      this.videoElement.muted = true;
    }
  }

  /**
   * Enumerate connected optical sensors (cameras) across phone/tablet/desktop
   */
  async getAvailableDevices() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
      return [];
    }
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      this.availableDevices = devices.filter(d => d.kind === 'videoinput');
      this.populateDeviceSelector();
      return this.availableDevices;
    } catch (e) {
      console.warn('Device enumeration warning:', e);
      return [];
    }
  }

  /**
   * Populate UI device dropdown if selector element is present
   */
  populateDeviceSelector() {
    if (!this.deviceSelectElement) return;
    this.deviceSelectElement.innerHTML = '';
    
    if (this.availableDevices.length === 0) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Default Optical Sensor';
      this.deviceSelectElement.appendChild(opt);
      return;
    }

    this.availableDevices.forEach((device, idx) => {
      const opt = document.createElement('option');
      opt.value = device.deviceId;
      opt.textContent = device.label || `Camera ${idx + 1} (${device.deviceId.slice(0, 5)}...)`;
      if (this.selectedDeviceId === device.deviceId) {
        opt.selected = true;
      }
      this.deviceSelectElement.appendChild(opt);
    });
  }

  /**
   * Build camera constraint set with deviceId / facingMode fallback
   */
  buildConstraints(width = 1280, height = 720) {
    const videoConstraints = {
      width: { ideal: width },
      height: { ideal: height }
    };

    if (this.selectedDeviceId) {
      videoConstraints.deviceId = { exact: this.selectedDeviceId };
    } else if (this.facingMode) {
      videoConstraints.facingMode = { ideal: this.facingMode };
    }

    return {
      video: videoConstraints,
      audio: false
    };
  }

  /**
   * Initialize optical sensor with multi-resolution fallback
   */
  async startCamera(preferredFacingMode = null) {
    if (preferredFacingMode) {
      this.facingMode = preferredFacingMode;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.showStatus('SYSTEM ERROR: Biometric Optical Camera API not supported in this browser. Please use HTTPS or Chrome/Safari.', 'danger');
      return false;
    }

    // Stop existing stream if active
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }

    // Resolution tiers: HD -> Standard -> Basic fallback for mobile
    const resolutionTiers = [
      { w: 1280, h: 720 },
      { w: 640, h: 480 },
      { w: 320, h: 240 }
    ];

    let lastError = null;

    for (const res of resolutionTiers) {
      try {
        const constraints = this.buildConstraints(res.w, res.h);
        this.stream = await navigator.mediaDevices.getUserMedia(constraints);
        break; // Successfully obtained stream
      } catch (err) {
        lastError = err;
        console.warn(`Camera init at ${res.w}x${res.h} failed, trying fallback:`, err);
      }
    }

    // If still failed with deviceId constraint, try basic unconstrained fallback
    if (!this.stream) {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: this.facingMode },
          audio: false
        });
      } catch (err) {
        lastError = err;
      }
    }

    if (!this.stream) {
      console.error('Camera initialization error:', lastError);
      let msg = 'CAMERA SENSOR OFFLINE: Please check camera device connections and system permissions.';
      if (lastError && lastError.name === 'NotAllowedError') {
        msg = 'PERMISSION DENIED: Biometric optical feed access denied. Please allow camera permissions in your mobile/browser settings.';
      } else if (lastError && lastError.name === 'NotFoundError') {
        msg = 'SENSOR NOT FOUND: No compatible optical camera hardware detected on this device.';
      } else if (lastError && (lastError.name === 'NotReadableError' || lastError.name === 'TrackStartError')) {
        msg = 'SENSOR IN USE: Camera is already being accessed by another application or tab.';
      }
      this.showStatus(msg, 'danger');
      return false;
    }

    try {
      if (this.videoElement) {
        this.videoElement.srcObject = this.stream;
        await this.videoElement.play();
        
        // Refresh device list now that permissions are granted (gives labels on mobile)
        await this.getAvailableDevices();

        const videoTrack = this.stream.getVideoTracks()[0];
        const settings = videoTrack ? videoTrack.getSettings() : {};
        const isFacingUser = settings.facingMode === 'user' || this.facingMode === 'user';
        const sensorLabel = isFacingUser ? 'FRONT SENSOR' : 'REAR SENSOR';

        this.showStatus(`● OPTICAL SENSOR ONLINE // ${sensorLabel} [${settings.width || 640}x${settings.height || 480}]`, 'info');
        if (this.scanLine) this.scanLine.style.display = 'block';

        // Check if torch/flash is supported
        this.checkTorchCapability();
        return true;
      }
    } catch (playErr) {
      console.error('Video play error:', playErr);
      this.showStatus('OPTICAL SENSOR PLAYBACK FAILED: Tap the screen or press Start Scanner.', 'warning');
      return false;
    }
  }

  /**
   * Flip camera facing mode (Front <-> Back) for mobile phones & tablets
   */
  async flipCamera() {
    this.selectedDeviceId = null;
    this.facingMode = (this.facingMode === 'user') ? 'environment' : 'user';
    const scanningWasActive = this.isScanning;
    
    const started = await this.startCamera();
    if (started && scanningWasActive) {
      // scanning interval continues
    }
    return started;
  }

  /**
   * Switch to a specific device by deviceId (external USB webcam, second lens, etc.)
   */
  async selectDevice(deviceId) {
    this.selectedDeviceId = deviceId;
    return await this.startCamera();
  }

  /**
   * Check if device camera supports hardware Torch/Flashlight
   */
  checkTorchCapability() {
    if (!this.torchBtnElement || !this.stream) return;
    const track = this.stream.getVideoTracks()[0];
    if (!track) return;

    const capabilities = track.getCapabilities ? track.getCapabilities() : {};
    if (capabilities.torch) {
      this.torchBtnElement.style.display = 'inline-flex';
    } else {
      this.torchBtnElement.style.display = 'none';
    }
  }

  /**
   * Toggle Torch / Flashlight on supported mobile devices
   */
  async toggleTorch() {
    if (!this.stream) return;
    const track = this.stream.getVideoTracks()[0];
    if (!track || !track.applyConstraints) return;

    try {
      this.isTorchOn = !this.isTorchOn;
      await track.applyConstraints({
        advanced: [{ torch: this.isTorchOn }]
      });
      if (this.torchBtnElement) {
        this.torchBtnElement.classList.toggle('active', this.isTorchOn);
      }
    } catch (e) {
      console.warn('Torch toggle error:', e);
    }
  }

  stopCamera() {
    this.stopScanning();
    if (this.scanLine) this.scanLine.style.display = 'none';
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
  }

  captureSnapshot() {
    if (!this.videoElement || !this.stream) {
      this.showStatus('OPTICAL SENSOR INACTIVE: Initialize camera prior to capture.', 'danger');
      return null;
    }

    const canvas = this.canvasElement || document.createElement('canvas');
    const width = this.videoElement.videoWidth || 640;
    const height = this.videoElement.videoHeight || 480;
    
    canvas.width = width;
    canvas.height = height;
    
    const ctx = canvas.getContext('2d');
    
    // If front camera, un-mirror capture so face orientations match biometric vectors
    ctx.drawImage(this.videoElement, 0, 0, width, height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);

    if (this.previewImg) {
      this.previewImg.src = dataUrl;
      this.previewImg.style.display = 'block';
    }

    if (this.imageDataInput) {
      this.imageDataInput.value = dataUrl;
    }

    this.showStatus('BIOMETRIC FRAME CAPTURED // READY FOR VECTORIZATION', 'success');
    return dataUrl;
  }

  startLiveScanning(onResultCallback, intervalMs = 600) {
    if (this.isScanning) return;
    this.isScanning = true;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    let isProcessing = false;

    this.scanInterval = setInterval(async () => {
      if (!this.videoElement || this.videoElement.paused || this.videoElement.ended || isProcessing) return;

      const width = this.videoElement.videoWidth;
      const height = this.videoElement.videoHeight;
      if (!width || !height) return;

      // Downsample for rapid client transmission & low network latency on mobile Wi-Fi/4G
      const targetW = Math.min(width, 480);
      const targetH = Math.round((targetW / width) * height);

      canvas.width = targetW;
      canvas.height = targetH;
      ctx.drawImage(this.videoElement, 0, 0, targetW, targetH);

      const frameBase64 = canvas.toDataURL('image/jpeg', 0.65);
      isProcessing = true;

      try {
        const response = await fetch('/api/recognize-frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: frameBase64 })
        });

        if (response.ok) {
          const result = await response.json();
          if (onResultCallback) {
            // Include scale factors so bounding boxes map correctly to full video coordinates
            result._scaleX = width / targetW;
            result._scaleY = height / targetH;
            onResultCallback(result);
          }
        }
      } catch (e) {
        console.warn('Live recognition telemetry error:', e);
      } finally {
        isProcessing = false;
      }
    }, intervalMs);
  }

  stopScanning() {
    this.isScanning = false;
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
  }

  showStatus(message, type = 'info') {
    if (!this.statusElement) return;
    this.statusElement.className = `alert alert-${type}`;
    this.statusElement.innerHTML = `<span><i class="fas fa-terminal"></i> ${message}</span>`;
    this.statusElement.style.display = 'flex';
  }
}
