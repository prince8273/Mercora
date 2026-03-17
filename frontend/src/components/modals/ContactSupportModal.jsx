import { useState } from 'react';
import emailjs from '@emailjs/browser';
import { EMAILJS_CONFIG } from '../../config/emailjs';

const ContactSupportModal = ({ isOpen, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);
  const [submittedEmail, setSubmittedEmail] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus(null);

    console.log('=== FORM SUBMISSION STARTED ===');
    console.log('Form data:', formData);

    try {
      // Simple test first - just try to send one email
      console.log('Testing EmailJS with simple parameters...');
      
      const testParams = {
        to_name: formData.name,
        to_email: formData.email,
        from_name: formData.name,
        from_email: formData.email,
        subject: formData.subject,
        message: formData.message,
        reply_to: formData.email,
        // Ensure recipient email is set
        user_email: formData.email,
        recipient_email: formData.email
      };

      console.log('Test parameters:', testParams);
      console.log('Service ID:', EMAILJS_CONFIG.SERVICE_ID);
      console.log('Public Key:', EMAILJS_CONFIG.PUBLIC_KEY);
      console.log('Template ID:', EMAILJS_CONFIG.TEMPLATES.AUTORESPONSE);

      // Send auto-response to user first
      console.log('Sending auto-response to user...');
      await emailjs.send(
        EMAILJS_CONFIG.SERVICE_ID,
        EMAILJS_CONFIG.TEMPLATES.AUTORESPONSE,
        testParams,
        EMAILJS_CONFIG.PUBLIC_KEY
      );
      console.log('Auto-response sent successfully');

      // Send main contact form to you
      const mainEmailParams = {
        from_name: formData.name,
        from_email: formData.email,
        subject: formData.subject,
        message: formData.message,
        to_name: 'Harshit Kumar',
        to_email: 'harshitkumar94306@gmail.com',
        reply_to: formData.email,
        // Additional formatting parameters
        current_date: new Date().toLocaleDateString('en-IN', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }),
        website_url: window.location.origin
      };

      console.log('Sending main email to you...', mainEmailParams);
      await emailjs.send(
        EMAILJS_CONFIG.SERVICE_ID,
        EMAILJS_CONFIG.TEMPLATES.CONTACT,
        mainEmailParams,
        EMAILJS_CONFIG.PUBLIC_KEY
      );
      console.log('Main email sent successfully to harshitkumar94306@gmail.com');

      console.log('EmailJS SUCCESS: Both emails sent');
      
      // If we get here, EmailJS is working
      setSubmitStatus('success');
      setSubmittedEmail(formData.email);
      setFormData({ name: '', email: '', subject: '', message: '' });
      
      setTimeout(() => {
        onClose();
        setSubmitStatus(null);
        setSubmittedEmail('');
      }, 5000);
      
    } catch (error) {
      console.error('=== EMAILJS ERROR ===');
      console.error('Error object:', error);
      console.error('Error message:', error.message);
      console.error('Error text:', error.text);
      console.error('Error status:', error.status);
      console.error('Full error:', JSON.stringify(error, null, 2));
      
      // Try FormSubmit as fallback
      console.log('Trying FormSubmit fallback...');
      try {
        const formData_submit = new FormData();
        formData_submit.append('name', formData.name);
        formData_submit.append('email', formData.email);
        formData_submit.append('subject', formData.subject);
        formData_submit.append('message', formData.message);
        formData_submit.append('_subject', `Mercora Contact: ${formData.subject}`);
        formData_submit.append('_captcha', 'false');
        formData_submit.append('_template', 'table');

        const fallbackResponse = await fetch('https://formsubmit.co/c9bb7b4974a13716407d50b0c781b930', {
          method: 'POST',
          body: formData_submit
        });

        if (fallbackResponse.ok) {
          console.log('FormSubmit fallback successful');
          setSubmitStatus('success');
          setSubmittedEmail(formData.email);
          setFormData({ name: '', email: '', subject: '', message: '' });
          
          setTimeout(() => {
            onClose();
            setSubmitStatus(null);
            setSubmittedEmail('');
          }, 5000);
        } else {
          throw new Error(`FormSubmit failed: ${fallbackResponse.status}`);
        }
      } catch (fallbackError) {
        console.error('FormSubmit also failed:', fallbackError);
        setSubmitStatus('error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={onClose}></div>
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-stone-200">
            <h3 className="text-xl font-bold text-stone-900">Contact Support</h3>
            <button
              onClick={onClose}
              className="text-stone-400 hover:text-stone-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {submitStatus === 'success' ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h4 className="text-lg font-semibold text-stone-900 mb-2">Thank You!</h4>
                <p className="text-stone-600">
                  Your message has been sent successfully. We'll get back to you soon.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors"
                    placeholder="Your name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors"
                    placeholder="your@email.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    Subject *
                  </label>
                  <input
                    type="text"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors"
                    placeholder="What can we help you with?"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={4}
                    className="w-full px-3 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors resize-none"
                    placeholder="Please describe your question or issue..."
                  />
                </div>

                {submitStatus === 'error' && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-red-600 text-sm">
                      Failed to send message. Please try again.
                    </p>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-4 py-2 border border-stone-300 text-stone-700 rounded-lg hover:bg-stone-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2 bg-stone-900 text-white rounded-lg hover:bg-stone-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? 'Sending...' : 'Send Message'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactSupportModal;