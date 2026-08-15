// Aeronexa Demo Payment & Dynamic QR Gateway Module

document.addEventListener('DOMContentLoaded', async () => {
  if (window.location.pathname !== '/payment') return;

  const urlParams = new URLSearchParams(window.location.search);
  let pnr = urlParams.get('pnr') || sessionStorage.getItem('aeronexa_pending_pnr');

  if (!pnr) {
    window.location.href = '/manage-booking';
    return;
  }

  const container = document.getElementById('payment-container');
  if (!container) return;

  // Initialize Payment Transaction
  try {
    const res = await fetch('/api/payment/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pnr, payment_method: 'UPI' })
    });

    const data = await res.json();

    if (!res.ok) {
      container.innerHTML = `<div class="card" style="text-align:center; color:var(--danger); padding:2rem;">${data.error || 'Failed to initialize payment.'}</div>`;
      return;
    }

    renderPaymentUI(data);
    startTimer(300); // 5 minute countdown

  } catch (err) {
    container.innerHTML = `<div class="card" style="text-align:center; color:var(--danger); padding:2rem;">Network error initializing payment.</div>`;
  }
});

function renderPaymentUI(payData) {
  const container = document.getElementById('payment-container');
  if (!container) return;

  container.innerHTML = `
    <div class="card" style="max-width:650px; margin:0 auto; text-align:center; border:2px solid var(--gold);">
      <div style="margin-bottom:1.5rem;">
        <span class="badge badge-gold" style="font-size:0.9rem;">DEMO / SANDBOX PAYMENT</span>
        <h2 style="color:var(--navy); margin-top:0.5rem;">Complete Your Flight Reservation</h2>
        <p style="font-size:0.9rem; color:var(--gray-600);">No real bank account or money will be charged.</p>
      </div>

      <div style="background-color:var(--light); padding:1.25rem; border-radius:var(--radius-md); margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center;">
        <div style="text-align:left;">
          <div style="font-size:0.8rem; color:var(--gray-600);">Booking Reference (PNR)</div>
          <div style="font-size:1.5rem; font-weight:800; color:var(--navy); font-family:var(--font-heading);">${payData.pnr}</div>
          <div style="font-size:0.75rem; color:var(--gray-400);">Txn ID: ${payData.transaction_id}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.8rem; color:var(--gray-600);">Amount Payable</div>
          <div style="font-size:1.8rem; font-weight:800; color:var(--navy);">${window.Aeronexa.formatCurrency(payData.amount)}</div>
        </div>
      </div>

      <!-- Dynamic QR Visual Box -->
      <div style="background-color:var(--white); border:2px solid var(--gold); border-radius:var(--radius-md); padding:1.5rem; display:inline-block; margin-bottom:1.5rem; position:relative; box-shadow:var(--shadow-md);">
        <div id="qr-canvas-container" style="display:flex; justify-content:center; margin-bottom:1rem;"></div>
        <div style="font-weight:700; font-size:0.9rem; color:var(--navy); margin-bottom:0.25rem;">Scan using Google Pay, PhonePe, Paytm, BHIM</div>
        <div style="font-size:0.8rem; color:var(--success); font-weight:600;">✓ Official UPI Payment Request Format</div>
        <div style="font-size:0.75rem; color:var(--gray-600); margin-top:0.4rem; background:var(--light); padding:0.4rem 0.8rem; border-radius:4px; font-family:monospace; word-break:break-all;">
          ${payData.qr_payload}
        </div>
      </div>

      <div style="margin-bottom:1.5rem; font-weight:600; color:var(--warning);">
        ⏱ QR expires in: <span id="payment-timer" style="font-family:var(--font-heading); font-size:1.1rem; color:var(--navy);">05:00</span>
      </div>

      <div style="display:flex; gap:1rem; justify-content:center; flex-wrap:wrap;">
        <button id="confirm-payment-btn" class="btn btn-gold btn-lg" style="flex:1; min-width:200px;">
          ✓ I've Completed Payment
        </button>
        <a href="/manage-booking" class="btn btn-outline-navy btn-lg">
          Cancel Payment
        </a>
      </div>

      <div style="margin-top:1.5rem; font-size:0.75rem; color:var(--gray-400); border-top:1px solid var(--gray-100); padding-top:1rem;">
        🔒 Aeronexa Sandbox Security — Simulated transaction for demonstration purposes only.
      </div>
    </div>
  `;

  // Draw Dynamic QR Code SVG Canvas
  drawSVGQRCode('qr-canvas-container', payData.qr_payload);

  const confirmBtn = document.getElementById('confirm-payment-btn');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', async () => {
      confirmBtn.disabled = true;
      confirmBtn.textContent = 'Verifying Transaction...';

      try {
        const res = await fetch('/api/payment/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            transaction_id: payData.transaction_id,
            pnr: payData.pnr
          })
        });

        const data = await res.json();
        if (res.ok) {
          window.Aeronexa.showToast('Payment Verified! Generating your E-Ticket...', 'success');
          setTimeout(() => {
            window.location.href = `/confirmation?pnr=${payData.pnr}`;
          }, 1200);
        } else {
          window.Aeronexa.showToast(data.error || 'Payment verification failed.', 'error');
          confirmBtn.disabled = false;
          confirmBtn.textContent = "✓ I've Completed Payment";
        }
      } catch (err) {
        window.Aeronexa.showToast('Network error during verification.', 'error');
        confirmBtn.disabled = false;
        confirmBtn.textContent = "✓ I've Completed Payment";
      }
    });
  }
}

function drawSVGQRCode(containerId, payload) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (window.AeronexaQR) {
    container.innerHTML = window.AeronexaQR.generateSVG(payload, 4);
  } else {
    container.innerHTML = '<div style="color:var(--danger);">QR Generator loading...</div>';
  }
}

function startTimer(durationSeconds) {
  let timer = durationSeconds;
  const timerElem = document.getElementById('payment-timer');

  const interval = setInterval(() => {
    const minutes = Math.floor(timer / 60);
    const seconds = timer % 60;

    const minStr = String(minutes).padStart(2, '0');
    const secStr = String(seconds).padStart(2, '0');

    if (timerElem) timerElem.textContent = `${minStr}:${secStr}`;

    if (--timer < 0) {
      clearInterval(interval);
      if (timerElem) timerElem.textContent = 'EXPIRED';
      window.Aeronexa.showToast('Payment window expired. Please re-initiate booking.', 'error');
    }
  }, 1000);
}
