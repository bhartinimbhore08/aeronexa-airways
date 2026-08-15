// Aeronexa User Dashboard & Loyalty Module

document.addEventListener('DOMContentLoaded', async () => {
  if (window.location.pathname === '/dashboard') {
    loadUserDashboard();
  } else if (window.location.pathname === '/aerorewards') {
    loadAeroRewards();
  }
});

async function loadUserDashboard() {
  const container = document.getElementById('dashboard-content');
  if (!container) return;

  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json();

    if (!res.ok) {
      window.location.href = '/login';
      return;
    }

    renderDashboardUI(data);

  } catch (err) {
    container.innerHTML = `<div class="card" style="color:var(--danger);">Error loading dashboard data.</div>`;
  }
}

function renderDashboardUI(data) {
  const container = document.getElementById('dashboard-content');
  if (!container) return;

  const { user, bookings, rewards } = data;

  let upcomingCount = bookings.filter(b => b.booking_status === 'CONFIRMED').length;
  let completedCount = bookings.filter(b => b.booking_status === 'COMPLETED').length;

  container.innerHTML = `
    <!-- User Profile Header Banner -->
    <div class="card" style="background:linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%); color:var(--white); margin-bottom:2rem; padding:2rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1.5rem;">
        <div>
          <div class="badge badge-gold" style="margin-bottom:0.5rem;">${rewards.tier} Tier Member</div>
          <h2 style="color:var(--white); margin-bottom:0.25rem;">Welcome back, ${user.name}!</h2>
          <p style="color:rgba(255,255,255,0.7); font-size:0.9rem;">${user.email} | ${user.mobile || 'No mobile added'}</p>
        </div>
        <div style="text-align:right; background:rgba(255,255,255,0.1); padding:1rem 1.5rem; border-radius:var(--radius-md); border:1px solid rgba(212,175,55,0.3);">
          <div style="font-size:0.8rem; color:var(--gold); text-transform:uppercase; font-weight:700;">AeroRewards Points</div>
          <div style="font-size:2rem; font-weight:800; color:var(--white); font-family:var(--font-heading);">${rewards.points_balance.toLocaleString()}</div>
        </div>
      </div>
    </div>

    <!-- Quick Stats Grid -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:1.25rem; margin-bottom:2.5rem;">
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem; font-weight:800; color:var(--navy);">${upcomingCount}</div>
        <div style="font-size:0.85rem; color:var(--gray-600); font-weight:600;">Upcoming Trips</div>
      </div>
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem; font-weight:800; color:var(--navy);">${completedCount}</div>
        <div style="font-size:0.85rem; color:var(--gray-600); font-weight:600;">Completed Flights</div>
      </div>
      <div class="card" style="text-align:center;">
        <div style="font-size:2rem; font-weight:800; color:var(--navy);">${bookings.length}</div>
        <div style="font-size:0.85rem; color:var(--gray-600); font-weight:600;">Total Bookings</div>
      </div>
    </div>

    <!-- Bookings History List -->
    <h3 style="margin-bottom:1.25rem; color:var(--navy);">My Flight Reservations</h3>
    ${bookings.length === 0 ? `
      <div class="card" style="text-align:center; padding:3rem;">
        <p>You have no active or past flight bookings yet.</p>
        <a href="/flights" class="btn btn-gold" style="margin-top:1rem;">Book a Flight Now</a>
      </div>
    ` : `
      <div>
        ${bookings.map(b => `
          <div class="card" style="margin-bottom:1.25rem; border-left:4px solid ${b.booking_status === 'CONFIRMED' ? 'var(--success)' : (b.booking_status === 'CANCELLED' ? 'var(--danger)' : 'var(--warning)')};">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; margin-bottom:1rem;">
              <div>
                <span class="badge badge-gold">PNR: ${b.pnr}</span>
                <span style="font-weight:700; color:var(--navy); font-size:1.1rem; margin-left:0.75rem;">${b.origin_city} (${b.origin}) → ${b.dest_city} (${b.destination})</span>
              </div>
              <div>
                <span class="badge ${b.booking_status === 'CONFIRMED' ? 'badge-success' : (b.booking_status === 'CANCELLED' ? 'badge-danger' : 'badge-warning')}">
                  ${b.booking_status}
                </span>
              </div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; font-size:0.9rem; color:var(--gray-600);">
              <div>
                <span>Flight: <strong>${b.flight_number}</strong></span> |
                <span>Departure: <strong>${b.departure_time}</strong></span> |
                <span>Class: <strong style="text-transform:capitalize;">${b.cabin_class}</strong></span>
              </div>
              <div style="font-size:1.25rem; font-weight:800; color:var(--navy);">
                ${window.Aeronexa.formatCurrency(b.total_amount)}
              </div>
            </div>

            <div style="margin-top:1rem; padding-top:1rem; border-top:1px solid var(--gray-100); display:flex; gap:0.75rem; flex-wrap:wrap;">
              <a href="/confirmation?pnr=${b.pnr}" class="btn btn-outline-navy btn-sm">View E-Ticket</a>
              ${b.booking_status === 'CONFIRMED' ? `
                <a href="/checkin?pnr=${b.pnr}" class="btn btn-gold btn-sm">Online Check-in</a>
                <a href="/boarding-pass?pnr=${b.pnr}" class="btn btn-navy btn-sm">Boarding Pass</a>
              ` : ''}
              <a href="/manage-booking?pnr=${b.pnr}" class="btn btn-outline btn-sm">Manage Booking</a>
            </div>
          </div>
        `).join('')}
      </div>
    `}
  `;
}

async function loadAeroRewards() {
  const container = document.getElementById('aerorewards-content');
  if (!container) return;

  try {
    const res = await fetch('/api/aerorewards');
    const data = await res.json();
    
    const balance = data.points_balance || 12450;
    const tier = data.tier || 'Gold';

    let targetPoints = 25000;
    let progressPercent = Math.min(100, Math.round((balance / targetPoints) * 100));

    container.innerHTML = `
      <div class="card" style="background:linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%); color:var(--white); text-align:center; padding:3rem 2rem; margin-bottom:3rem; border:2px solid var(--gold);">
        <span class="badge badge-gold" style="margin-bottom:1rem;">AEROREWARDS LOYALTY CLUB</span>
        <h1 style="color:var(--white); margin-bottom:0.5rem;">${balance.toLocaleString()} Points</h1>
        <h3 style="color:var(--gold); font-weight:600;">${tier} Tier Member</h3>
        
        <div style="max-width:500px; margin:2rem auto 0 auto;">
          <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:rgba(255,255,255,0.8); margin-bottom:0.5rem;">
            <span>Current: ${tier}</span>
            <span>Next: Platinum (${(targetPoints - balance).toLocaleString()} pts needed)</span>
          </div>
          <div style="height:10px; background:rgba(255,255,255,0.2); border-radius:var(--radius-full); overflow:hidden;">
            <div style="width:${progressPercent}%; height:100%; background:linear-gradient(90deg, #E5C158, #D4AF37);"></div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    // default view
  }
}
