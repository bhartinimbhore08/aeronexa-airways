// Aeronexa Form & Field Validation Utilities

window.AeronexaValidation = {
  validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  },

  validateIndianPhone(phone) {
    // Supports +91XXXXXXXXXX or 10 digit Indian number
    const re = /^(?:\+91|91)?[6-9]\d{9}$/;
    return re.test(phone.replace(/\s+/g, ''));
  },

  validatePassport(passport) {
    if (!passport) return true; // Optional for domestic, required for intl
    const re = /^[A-PR-WYa-pr-wy][1-9]\ds?\d{4}[1-9]$|^[A-Z0-9]{6,12}$/i;
    return re.test(passport.trim());
  },

  validateDOB(dobString) {
    if (!dobString) return false;
    const dob = new Date(dobString);
    const today = new Date();
    return dob < today;
  }
};
