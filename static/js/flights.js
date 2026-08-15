// Aeronexa Flight Search & Results Module

document.addEventListener('DOMContentLoaded', () => {
  // Flight Search Form Widget Setup
  const searchForm = document.getElementById('search-flights-form');
  const tripTabs = document.querySelectorAll('.trip-tab');
  let tripType = 'round_trip';

  if (tripTabs) {
    tripTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tripTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        tripType = tab.dataset.trip;
        
        const returnGroup = document.getElementById('return-date-group');
        if (returnGroup) {
          if (tripType === 'one_way') {
            returnGroup.style.display = 'none';
          } else {
            returnGroup.style.display = 'flex';
          }
        }
      });
    });
  }

  if (searchForm) {
    searchForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const origin = searchForm.origin.value.trim().toUpperCase();
      const destination = searchForm.destination.value.trim().toUpperCase();
      const departure_date = searchForm.departure_date.value;
      const return_date = searchForm.return_date ? searchForm.return_date.value : '';
      const passengers = parseInt(searchForm.passengers.value) || 1;
      const cabin = searchForm.cabin.value;

      if (!origin || !destination) {
        window.Aeronexa.showToast('Please select both Origin and Destination airports.', 'warning');
        return;
      }

      if (origin === destination) {
        window.Aeronexa.showToast('Origin and Destination airports cannot be the same.', 'error');
        return;
      }

      if (!departure_date) {
        window.Aeronexa.showToast('Please select a departure date.', 'warning');
        return;
      }

      const searchParams = {
        trip_type: tripType,
        origin,
        destination,
        departure_date,
        return_date,
        passengers,
        cabin
      };

      sessionStorage.setItem('aeronexa_search_params', JSON.stringify(searchParams));

      // If on home page, redirect to /flights page
      if (window.location.pathname !== '/flights') {
        window.location.href = '/flights';
      } else {
        loadFlightResults(searchParams);
      }
    });
  }

  // Auto-load results if on /flights page
  if (window.location.pathname === '/flights') {
    const saved = sessionStorage.getItem('aeronexa_search_params');
    const defaultParams = saved ? JSON.parse(saved) : {
      trip_type: 'round_trip',
      origin: 'BOM',
      destination: 'LHR',
      departure_date: '2026-09-12',
      return_date: '2026-09-20',
      passengers: 1,
      cabin: 'economy'
    };

    // Pre-fill search inputs if present
    const sForm = document.getElementById('search-flights-form');
    if (sForm) {
      if (sForm.origin) sForm.origin.value = defaultParams.origin;
      if (sForm.destination) sForm.destination.value = defaultParams.destination;
      if (sForm.departure_date) sForm.departure_date.value = defaultParams.departure_date;
      if (sForm.return_date) sForm.return_date.value = defaultParams.return_date;
      if (sForm.passengers) sForm.passengers.value = defaultParams.passengers;
      if (sForm.cabin) sForm.cabin.value = defaultParams.cabin;
    }

    loadFlightResults(defaultParams);
  }
});

let rawFlightResults = [];

async function loadFlightResults(params) {
  const container = document.getElementById('flight-results-container');
  if (!container) return;

  container.innerHTML = `
    <div style="text-align:center; padding:3rem 1rem;">
      <div style="font-size:2rem; margin-bottom:1rem; color:var(--gold);">✈</div>
      <h3>Searching Available Aeronexa Flights...</h3>
      <p>Finding the best fares for ${params.origin} → ${params.destination}</p>
    </div>
  `;

  try {
    const res = await fetch('/api/search-flights', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    const data = await res.json();

    if (!res.ok) {
      container.innerHTML = `<div class="card" style="text-align:center; color:var(--danger); padding:2rem;">${data.error || 'Failed to fetch flights.'}</div>`;
      return;
    }

    rawFlightResults = data.flights;

    if (rawFlightResults.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align:center; padding:3rem;">
          <h3 style="color:var(--navy);">No direct flights found for this route</h3>
          <p style="margin:1rem 0;">Try searching popular Aeronexa routes like <strong>BOM → LHR</strong>, <strong>BOM → DXB</strong>, or <strong>DEL → HND</strong>.</p>
          <a href="/destinations" class="btn btn-gold">Explore All Routes</a>
        </div>
      `;
      return;
    }

    renderFlightCards(rawFlightResults, params);
    setupFiltersAndSorting(params);

  } catch (err) {
    container.innerHTML = `<div class="card" style="text-align:center; color:var(--danger); padding:2rem;">Network error searching flights.</div>`;
  }
}

function renderFlightCards(flights, params) {
  const container = document.getElementById('flight-results-container');
  if (!container) return;

  const countBadge = document.getElementById('results-count');
  if (countBadge) {
    countBadge.textContent = `${flights.length} Flight${flights.length > 1 ? 's' : ''} Found`;
  }

  container.innerHTML = flights.map(fl => `
    <div class="flight-card" data-price="${fl.price}" data-duration="${fl.duration}" data-departure="${fl.departure_time}">
      <div>
        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem;">
          <span class="badge badge-gold">${fl.flight_number}</span>
          <span style="font-weight:600; color:var(--navy); font-size:0.9rem;">${fl.aircraft_name}</span>
          <span class="badge badge-success">${fl.status}</span>
        </div>

        <div class="flight-route">
          <div>
            <div class="route-time">${fl.departure_time}</div>
            <div class="route-city">${fl.origin_city} (${fl.origin})</div>
          </div>
          <div class="route-line">
            <span class="route-duration">${fl.duration}</span>
            <div style="font-size:0.75rem; color:var(--gray-600); margin-top:0.25rem;">
              ${fl.stops === 0 ? 'Non-Stop Direct' : fl.stops + ' Stop'}
            </div>
          </div>
          <div style="text-align:right;">
            <div class="route-time">${fl.arrival_time}</div>
            <div class="route-city">${fl.dest_city} (${fl.destination})</div>
          </div>
        </div>
      </div>

      <div style="font-size:0.85rem; color:var(--gray-600); line-height:1.6;">
        <div>💼 7kg Cabin Baggage</div>
        <div>🧳 23kg Checked Baggage</div>
        <div>🍽 Free Gourmet Meals</div>
        <div>📶 High-Speed Wi-Fi</div>
      </div>

      <div class="flight-price-box">
        <div class="price-unit">Starting from</div>
        <div class="price-amount">${window.Aeronexa.formatCurrency(fl.price)}</div>
        <div style="font-size:0.75rem; color:var(--gray-400); margin-bottom:0.75rem;">per adult passenger</div>
        <button class="btn btn-gold btn-sm" onclick="selectFlightForBooking(${fl.id})">
          Select Flight →
        </button>
      </div>
    </div>
  `).join('');
}

function setupFiltersAndSorting(params) {
  const sortSelect = document.getElementById('sort-flights');
  const priceFilter = document.getElementById('price-filter');
  const priceValue = document.getElementById('price-filter-val');

  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      let sorted = [...rawFlightResults];
      const val = sortSelect.value;

      if (val === 'cheapest') {
        sorted.sort((a, b) => a.price - b.price);
      } else if (val === 'fastest') {
        sorted.sort((a, b) => parseInt(a.duration) - parseInt(b.duration));
      } else if (val === 'earliest') {
        sorted.sort((a, b) => a.departure_time.localeCompare(b.departure_time));
      } else if (val === 'latest') {
        sorted.sort((a, b) => b.departure_time.localeCompare(a.departure_time));
      }

      renderFlightCards(sorted, params);
    });
  }

  if (priceFilter && priceValue) {
    priceFilter.addEventListener('input', () => {
      const maxPrice = parseFloat(priceFilter.value);
      priceValue.textContent = window.Aeronexa.formatCurrency(maxPrice);

      const filtered = rawFlightResults.filter(f => f.price <= maxPrice);
      renderFlightCards(filtered, params);
    });
  }
}

window.selectFlightForBooking = function(flightId) {
  const selectedFlight = rawFlightResults.find(f => f.id === flightId);
  if (selectedFlight) {
    sessionStorage.setItem('aeronexa_selected_flight', JSON.stringify(selectedFlight));
    window.location.href = '/booking';
  }
};
