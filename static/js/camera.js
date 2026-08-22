/**
 * VYRON — Camera & Biometric Scanner HUD Controller
 */

class FaceCameraManager {
  constructor(options = {}) {
    this.videoElement = document.getElementById(options.videoId || 'webcamVideo');
    this.canvasElement = document.getElementById(options.canvasId || 'captureCanvas');
    this.statusElement = document.getElementById(options.statusId || 'cameraStatus');
    this.previewImg = document.getElementById(options.previewId || 'capturedPreview');
    this.imageDataInput = document.getElementById(options.inputId || 'imageDataInput');
    this.scanLine = document.getElementById(options.scanLineId || 'hudScanLine');
    
    this.stream = null;
    this.isScanning = false;
    this.scanInterval = null;
  }

  async startCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.showStatus('SYSTEM ERROR: Biometric Camera API not supported in this environment.', 'danger');
      return false;
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });

      if (this.videoElement) {
        this.videoElement.srcObject = this.stream;
        await this.videoElement.play();
        this.showStatus('● BIOMETRIC OPTICAL SENSOR ONLINE // READY FOR SCAN', 'info');
        if (this.scanLine) this.scanLine.style.display = 'block';
        return true;
      }
    } catch (err) {
      console.error('Camera error:', err);
      let msg = 'CAMERA SENSOR OFFLINE: Please check camera device connections and system permissions.';
      if (err.name === 'NotAllowedError') {
        msg = 'PERMISSION DENIED: Biometric optical feed access denied by browser security.';
      } else if (err.name === 'NotFoundError') {
        msg = 'SENSOR NOT FOUND: No compatible optical camera hardware detected.';
      }
      this.showStatus(msg, 'danger');
      return false;
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
    ctx.drawImage(this.videoElement, 0, 0, width, height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);

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

    this.scanInterval = setInterval(async () => {
      if (!this.videoElement || this.videoElement.paused || this.videoElement.ended) return;

      const width = this.videoElement.videoWidth;
      const height = this.videoElement.videoHeight;
      if (!width || !height) return;

      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(this.videoElement, 0, 0, width, height);

      const frameBase64 = canvas.toDataURL('image/jpeg', 0.7);

      try {
        const response = await fetch('/api/recognize-frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: frameBase64 })
        });

        if (response.ok) {
          const result = await response.json();
          if (onResultCallback) {
            onResultCallback(result);
          }
        }
      } catch (e) {
        console.warn('Live recognition telemetry error:', e);
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
