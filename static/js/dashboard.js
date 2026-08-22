/**
 * VYRON — Dashboard Analytics & Chart.js Cyberpunk Visualizer
 */

document.addEventListener('DOMContentLoaded', () => {
  let attendanceChart = null;

  const chartCanvas = document.getElementById('attendanceChart');
  if (chartCanvas && typeof Chart !== 'undefined') {
    const ctx = chartCanvas.getContext('2d');
    
    // Create futuristic gradient for bars
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(0, 245, 255, 0.85)');
    gradient.addColorStop(0.5, 'rgba(139, 92, 255, 0.6)');
    gradient.addColorStop(1, 'rgba(255, 43, 214, 0.2)');

    attendanceChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Identities Verified',
          data: [],
          backgroundColor: gradient,
          borderColor: '#00F5FF',
          borderWidth: 1.5,
          borderRadius: 4,
          hoverBackgroundColor: 'rgba(0, 245, 255, 1)',
          hoverBorderColor: '#FF2BD6',
          hoverBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0B0B1A',
            titleColor: '#00F5FF',
            bodyColor: '#F5F7FF',
            borderColor: 'rgba(0, 245, 255, 0.4)',
            borderWidth: 1,
            titleFont: { family: 'Orbitron, sans-serif', size: 12 },
            bodyFont: { family: 'Rajdhani, sans-serif', size: 13, weight: 'bold' },
            padding: 12,
            cornerRadius: 4,
            displayColors: false,
            callbacks: {
              label: (context) => `VERIFIED ATTENDANCE: ${context.parsed.y} IDENTITIES`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(0, 245, 255, 0.05)', borderColor: 'rgba(0, 245, 255, 0.2)' },
            ticks: { color: '#94A3B8', font: { family: 'Rajdhani, sans-serif', size: 12, weight: 600 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0, 245, 255, 0.05)', borderColor: 'rgba(0, 245, 255, 0.2)' },
            ticks: {
              stepSize: 1,
              color: '#94A3B8',
              font: { family: 'Rajdhani, sans-serif', size: 12, weight: 600 }
            }
          }
        }
      }
    });

    fetchChartData();
  }

  async function fetchChartData() {
    try {
      const res = await fetch('/api/attendance-chart');
      if (!res.ok) return;
      const json = await res.json();
      if (json.success && attendanceChart) {
        attendanceChart.data.labels = json.labels;
        attendanceChart.data.datasets[0].data = json.data;
        attendanceChart.update();
      }
    } catch (e) {
      console.warn('Telemetry fetch error:', e);
    }
  }

  // Periodic polling for Dashboard stats every 6 seconds
  async function pollDashboardStats() {
    try {
      const res = await fetch('/api/dashboard-stats');
      if (!res.ok) return;
      const json = await res.json();
      if (json.success && json.data) {
        const stats = json.data;
        
        // Update metric values
        const totalEl = document.getElementById('statTotalStudents');
        const presentEl = document.getElementById('statPresentToday');
        const absentEl = document.getElementById('statAbsentToday');
        const pctEl = document.getElementById('statAttendancePct');

        if (totalEl) totalEl.textContent = stats.total_students;
        if (presentEl) presentEl.textContent = stats.present_today;
        if (absentEl) absentEl.textContent = stats.absent_today;
        if (pctEl) pctEl.textContent = `${stats.attendance_percentage}%`;

        // Update Recent Attendance Table
        const recentTableBody = document.getElementById('recentAttendanceBody');
        if (recentTableBody && stats.recent_attendance) {
          if (stats.recent_attendance.length === 0) {
            recentTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;"><i class="fas fa-terminal"></i> No biometric telemetry logged for current cycle.</td></tr>`;
          } else {
            recentTableBody.innerHTML = stats.recent_attendance.map(r => `
              <tr>
                <td><strong class="neon-cyan">${r.name}</strong></td>
                <td><code style="color: var(--neon-purple); font-weight: bold;">${r.usn}</code></td>
                <td>${r.date}</td>
                <td>${r.time}</td>
                <td><span class="badge badge-success"><i class="fas fa-circle-check"></i> ${r.status}</span></td>
                <td><strong style="color: var(--neon-cyan);">${r.confidence}%</strong></td>
              </tr>
            `).join('');
          }
        }

        // Update Chart if data changed
        if (attendanceChart && stats.chart_labels && stats.chart_data) {
          attendanceChart.data.labels = stats.chart_labels;
          attendanceChart.data.datasets[0].data = stats.chart_data;
          attendanceChart.update();
        }
      }
    } catch (err) {
      console.warn('Telemetry polling error:', err);
    }
  }

  if (document.getElementById('statTotalStudents')) {
    setInterval(pollDashboardStats, 6000);
  }
});
