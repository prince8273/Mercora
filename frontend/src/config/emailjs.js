// EmailJS Configuration
// Replace these values with your actual EmailJS credentials

export const EMAILJS_CONFIG = {
  // Get these from your EmailJS dashboard at https://www.emailjs.com/
  SERVICE_ID: 'service_dgany6p',  // Your Service ID
  PUBLIC_KEY: '2Y59riccErQCaMRYT',     // Your Public Key
  
  // Template IDs - create these templates in EmailJS dashboard
  TEMPLATES: {
    CONTACT: 'template_contact',      // Template for main email (to you) - CREATE THIS ONE
    AUTORESPONSE: 'template_autoresponse'  // Template for confirmation email (to user) - YOU HAVE THIS ONE
  }
};

// Status:
// ✅ EmailJS account created
// ✅ Gmail service added - Service ID: service_dgany6p
// ✅ Public Key obtained: 2Y59riccErQCaMRYT
// ⏳ Create template_contact (main email template)
// ⏳ Update auto-reply template ID to template_autoresponse