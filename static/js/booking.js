// Aeronexa Multi-Step Booking Wizard Module

document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname !== '/booking') return;

  const savedFlight = sessionStorage.getItem('aeronexa_selected_flight');
  const savedSearchParams = sessionStorage.getItem('aeronexa_search_params');

  if (!savedFlight) {
    window.location.href = '/flights';
    return;
  }

  const flight = JSON.parse(savedFlight);
  const searchParams = savedSearchParams ? JSON.parse(savedSearchParams) : { passengers: 1, cabin: 'economy' };

  let currentStep = 1;
  let fareType = 'Saver';
  let passengersData = [];
  let selectedSeats = {};
  let selectedAddons = [];
  let appliedPromo = null;

  // Initialize Passenger Data template array
  for (let i = 0; i < searchParams.passengers; i++) {
    passengersData.push({
      title: 'Mr.',
      first_name: '',
      middle_name: '',
      last_name: '',
      dob: '1995-06-15',
      gender: 'Male',
      nationality: 'Indian',
      passport_number: '',
      seat_number: '',
      baggage_kg: 0,
      meal_code: 'VEG',
      meal_name: 'Vegetarian Gourmet Meal'
    });
  }

  renderFlightSummaryHeader(flight, searchParams);
  renderPassengerForms(passengersData);
  setupWizardControls(flight, searchParams);

  async function renderSeatMap(flightId) {
    const seatContainer = document.getElementById('seat-map-render');
    if (!seatContainer) return;

    seatContainer.innerHTML = '<div style="text-align:center; padding:2rem;">Loading seat map...</div>';

    try {
      const res = await fetch(`/api/flights/${flightId}/seats`);
      const data = await res.json();
      if (!res.ok) {
        seatContainer.innerHTML = `<div style="color:var(--danger);">Failed to load seats.</div>`;
        return;
      }

      const seats = data.seats;
      let html = '<div class="seat-map-header">FRONT OF AIRCRAFT (COCKPIT)</div>';
      
      // Group seats by row
      const rowMap = {};
      seats.forEach(s => {
        const rowNum = s.seat_number.substring(0, 2);
        if (!rowMap[rowNum]) rowMap[rowNum] = [];
        rowMap[rowNum].push(s);
      });

      html += `<div class="seat-legend">
        <div class="legend-item"><span class="seat-box available"></span> Available</div>
        <div class="legend-item"><span class="seat-box selected"></span> Selected</div>
        <div class="legend-item"><span class="seat-box occupied"></span> Occupied</div>
        <div class="legend-item"><span class="seat-box premium"></span> Premium (+₹500)</div>
      </div>`;

      Object.keys(rowMap).sort().forEach(rNum => {
        html += `<div class="seat-row">`;
        const rowSeats = rowMap[rNum];
        
        rowSeats.forEach((st, idx) => {
          if (idx === 3) {
            html += `<div class="seat-aisle"></div>`; // Aisle gap
          }

          let stateClass = 'available';
          if (st.is_occupied) stateClass = 'occupied';
          if (st.is_premium) stateClass += ' premium';

          // Check if currently selected by any passenger
          const isSelectedByCurrent = Object.values(selectedSeats).includes(st.seat_number);
          if (isSelectedByCurrent) stateClass = 'selected';

          html += `
            <div class="seat-box ${stateClass}" data-seat="${st.seat_number}" data-occupied="${st.is_occupied}" onclick="handleSeatClick('${st.seat_number}', ${st.is_occupied})">
              ${st.seat_number}
            </div>
          `;
        });

        html += `</div>`;

        if (rNum === '06' || rNum === '10') {
          html += `<div style="text-align:center; font-size:0.75rem; font-weight:700; color:var(--gold); margin:0.75rem 0;">══ EMERGENCY EXIT ROW ══</div>`;
        }
      });

      seatContainer.innerHTML = html;

    } catch (err) {
      seatContainer.innerHTML = '<div style="color:var(--danger);">Error loading seats.</div>';
    }
  }

  window.handleSeatClick = function(seatNum, isOccupied) {
    if (isOccupied) {
      window.Aeronexa.showToast(`Seat ${seatNum} is already occupied.`, 'warning');
      return;
    }

    const activePassengerIndex = parseInt(document.getElementById('active-passenger-select') ? document.getElementById('active-passenger-select').value : 0);

    // Assign seat
    selectedSeats[activePassengerIndex] = seatNum;
    passengersData[activePassengerIndex].seat_number = seatNum;

    window.Aeronexa.showToast(`Seat ${seatNum} assigned to Passenger ${activePassengerIndex + 1}.`, 'success');
    renderSeatMap(flight.id);
  };

  function setupWizardControls(flight, searchParams) {
    const nextBtn = document.getElementById('wizard-next-btn');
    const prevBtn = document.getElementById('wizard-prev-btn');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
          currentStep--;
          updateWizardStepUI(currentStep);
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', async () => {
        if (currentStep === 1) {
          // Fare selected
          const fareRadio = document.querySelector('input[name="fare_type"]:checked');
          if (fareRadio) fareType = fareRadio.value;
          currentStep++;
          updateWizardStepUI(currentStep);
        } else if (currentStep === 2) {
          // Validate passenger inputs
          if (!validatePassengerFormInputs()) return;
          currentStep++;
          updateWizardStepUI(currentStep);
          renderSeatMap(flight.id);
        } else if (currentStep === 3) {
          // Seat map
          currentStep++;
          updateWizardStepUI(currentStep);
        } else if (currentStep === 4) {
          // Baggage
          currentStep++;
          updateWizardStepUI(currentStep);
        } else if (currentStep === 5) {
          // Meals
          currentStep++;
          updateWizardStepUI(currentStep);
        } else if (currentStep === 6) {
          // Addons
          currentStep++;
          updateWizardStepUI(currentStep);
          renderSummaryBreakdown(flight, searchParams);
        } else if (currentStep === 7) {
          // Submit final booking payload to backend API
          submitBookingToBackend(flight, searchParams);
        }
      });
    }

    // Fare Card Selectors
    document.querySelectorAll('.fare-card').forEach(fc => {
      fc.addEventListener('click', () => {
        document.querySelectorAll('.fare-card').forEach(c => c.classList.remove('selected'));
        fc.classList.add('selected');
        const radio = fc.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
        fareType = fc.dataset.fare;
      });
    });

    // Promo Code Handler
    const applyPromoBtn = document.getElementById('apply-promo-btn');
    if (applyPromoBtn) {
      applyPromoBtn.addEventListener('click', async () => {
        const codeInput = document.getElementById('promo-code-input');
        if (!codeInput || !codeInput.value) return;

        const code = codeInput.value.trim().toUpperCase();
        try {
          const res = await fetch('/api/validate-promo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, amount: calculateSubtotal(flight, searchParams) })
          });
          const data = await res.json();
          if (res.ok && data.valid) {
            appliedPromo = data;
            window.Aeronexa.showToast(`Promo ${code} applied! Discount: ${window.Aeronexa.formatCurrency(data.discount)}`, 'success');
            renderSummaryBreakdown(flight, searchParams);
          } else {
            window.Aeronexa.showToast(data.error || 'Invalid promo code.', 'error');
          }
        } catch (err) {
          window.Aeronexa.showToast('Failed to validate promo code.', 'error');
        }
      });
    }
  }

  function updateWizardStepUI(step) {
    document.querySelectorAll('.wizard-content-step').forEach(s => s.style.display = 'none');
    const activeStepElem = document.getElementById(`step-content-${step}`);
    if (activeStepElem) activeStepElem.style.display = 'block';

    document.querySelectorAll('.step-item').forEach((si, idx) => {
      si.classList.remove('active', 'completed');
      if (idx + 1 === step) si.classList.add('active');
      if (idx + 1 < step) si.classList.add('completed');
    });

    const prevBtn = document.getElementById('wizard-prev-btn');
    const nextBtn = document.getElementById('wizard-next-btn');

    if (prevBtn) prevBtn.style.display = step === 1 ? 'none' : 'inline-flex';
    if (nextBtn) nextBtn.textContent = step === 7 ? 'Proceed to Payment →' : 'Continue →';
  }

  function validatePassengerFormInputs() {
    let isValid = true;
    passengersData.forEach((p, i) => {
      const titleElem = document.getElementById(`p_title_${i}`);
      const fnElem = document.getElementById(`p_fname_${i}`);
      const lnElem = document.getElementById(`p_lname_${i}`);
      const dobElem = document.getElementById(`p_dob_${i}`);

      if (titleElem) p.title = titleElem.value;
      if (fnElem) p.first_name = fnElem.value.trim();
      if (lnElem) p.last_name = lnElem.value.trim();
      if (dobElem) p.dob = dobElem.value;

      if (!p.first_name || !p.last_name || !p.dob) {
        window.Aeronexa.showToast(`Please complete all required details for Passenger ${i + 1}.`, 'warning');
        isValid = false;
      }
    });
    return isValid;
  }

  function calculateSubtotal(flight, searchParams) {
    let basePrice = flight.price;
    if (fareType === 'Flex') basePrice += 1500;
    if (fareType === 'SuperFlex') basePrice += 3500;

    let total = basePrice * searchParams.passengers;
    return total;
  }

  function renderSummaryBreakdown(flight, searchParams) {
    const summaryBox = document.getElementById('booking-summary-breakdown');
    if (!summaryBox) return;

    let basePrice = flight.price;
    if (fareType === 'Flex') basePrice += 1500;
    if (fareType === 'SuperFlex') basePrice += 3500;

    const baseFareTotal = basePrice * searchParams.passengers;
    const taxes = round(baseFareTotal * 0.12, 2);

    let extras = 0;
    // Calculate baggage/meals/addons extras
    passengersData.forEach(p => {
      if (p.baggage_kg == 15) extras += 800;
      if (p.baggage_kg == 20) extras += 1400;
      if (p.baggage_kg == 30) extras += 2200;
      if (p.meal_code && p.meal_code !== 'NONE') extras += 350;
    });

    let discount = appliedPromo ? appliedPromo.discount : 0;
    let finalTotal = Math.max(0, (baseFareTotal + taxes + extras) - discount);

    summaryBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; margin-bottom:0.75rem;">
        <span>Base Fare (${searchParams.passengers} Passenger${searchParams.passengers > 1 ? 's' : ''})</span>
        <span style="font-weight:700;">${window.Aeronexa.formatCurrency(baseFareTotal)}</span>
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom:0.75rem;">
        <span>Taxes & Aviation Charges (12%)</span>
        <span style="font-weight:700;">${window.Aeronexa.formatCurrency(taxes)}</span>
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom:0.75rem;">
        <span>Seats, Baggage & Add-ons</span>
        <span style="font-weight:700;">${window.Aeronexa.formatCurrency(extras)}</span>
      </div>
      ${discount > 0 ? `
        <div style="display:flex; justify-content:space-between; margin-bottom:0.75rem; color:var(--success);">
          <span>Promo Discount (${appliedPromo.code})</span>
          <span style="font-weight:700;">-${window.Aeronexa.formatCurrency(discount)}</span>
        </div>
      ` : ''}
      <hr style="margin:1rem 0; border:0; border-top:1px solid var(--gray-200);">
      <div style="display:flex; justify-content:space-between; font-size:1.4rem; font-weight:800; color:var(--navy);">
        <span>Total Amount Payable</span>
        <span style="color:var(--navy);">${window.Aeronexa.formatCurrency(finalTotal)}</span>
      </div>
    `;
  }

  async function submitBookingToBackend(flight, searchParams) {
    const nextBtn = document.getElementById('wizard-next-btn');
    if (nextBtn) {
      nextBtn.disabled = true;
      nextBtn.textContent = 'Processing Booking...';
    }

    const payload = {
      flight_id: flight.id,
      cabin_class: searchParams.cabin,
      fare_type: fareType,
      passengers: passengersData,
      promo_code: appliedPromo ? appliedPromo.code : '',
      addons: selectedAddons
    };

    try {
      const res = await fetch('/api/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        sessionStorage.setItem('aeronexa_pending_pnr', data.pnr);
        window.location.href = `/payment?pnr=${data.pnr}`;
      } else {
        window.Aeronexa.showToast(data.error || 'Failed to create booking.', 'error');
        if (nextBtn) {
          nextBtn.disabled = false;
          nextBtn.textContent = 'Proceed to Payment →';
        }
      }
    } catch (err) {
      window.Aeronexa.showToast('Network error processing booking.', 'error');
      if (nextBtn) {
        nextBtn.disabled = false;
        nextBtn.textContent = 'Proceed to Payment →';
      }
    }
  }

  function renderFlightSummaryHeader(flight, searchParams) {
    const header = document.getElementById('booking-flight-header');
    if (!header) return;

    header.innerHTML = `
      <div class="card" style="margin-bottom:2rem; background:linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%); color:var(--white);">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
          <div>
            <span class="badge badge-gold">${flight.flight_number}</span>
            <span style="margin-left:0.5rem; font-weight:600; font-size:1.1rem;">${flight.origin_city} (${flight.origin}) → ${flight.dest_city} (${flight.destination})</span>
          </div>
          <div style="font-size:0.9rem; color:rgba(255,255,255,0.8);">
            <span>Date: <strong>${searchParams.departure_date}</strong></span> |
            <span>Aircraft: <strong>${flight.aircraft_name}</strong></span> |
            <span>Cabin: <strong style="text-transform:capitalize;">${searchParams.cabin}</strong></span>
          </div>
        </div>
      </div>
    `;
  }

  function renderPassengerForms(passengers) {
    const container = document.getElementById('passengers-form-container');
    if (!container) return;

    container.innerHTML = passengers.map((p, i) => `
      <div class="card" style="margin-bottom:1.5rem;">
        <h4 style="margin-bottom:1.25rem; color:var(--navy); display:flex; align-items:center; gap:0.5rem;">
          <span>👤</span> Passenger ${i + 1} (${i === 0 ? 'Primary Traveler' : 'Traveler'})
        </h4>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1rem;">
          <div class="form-group">
            <label class="form-label">Title *</label>
            <select class="form-select" id="p_title_${i}">
              <option value="Mr.">Mr.</option>
              <option value="Ms.">Ms.</option>
              <option value="Mrs.">Mrs.</option>
              <option value="Dr.">Dr.</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">First Name *</label>
            <input type="text" class="form-control" id="p_fname_${i}" placeholder="First name as on ID" required>
          </div>
          <div class="form-group">
            <label class="form-label">Middle Name</label>
            <input type="text" class="form-control" id="p_mname_${i}" placeholder="Middle name (optional)">
          </div>
          <div class="form-group">
            <label class="form-label">Last Name *</label>
            <input type="text" class="form-control" id="p_lname_${i}" placeholder="Last name as on ID" required>
          </div>
          <div class="form-group">
            <label class="form-label">Date of Birth *</label>
            <input type="date" class="form-control" id="p_dob_${i}" value="1995-06-15" required>
          </div>
          <div class="form-group">
            <label class="form-label">Gender *</label>
            <select class="form-select" id="p_gender_${i}">
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Nationality *</label>
            <input type="text" class="form-control" id="p_nat_${i}" value="Indian">
          </div>
          <div class="form-group">
            <label class="form-label">Passport Number (For Intl Flights)</label>
            <input type="text" class="form-control" id="p_pass_${i}" placeholder="e.g. Z9876543">
          </div>
        </div>
      </div>
    `).join('');
  }

  function round(val, dec) {
    return Number(Math.round(val + 'e' + dec) + 'e-' + dec);
  }
});
