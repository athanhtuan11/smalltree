document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            event.preventDefault();
            // Add form validation logic here
            alert('Form submitted successfully!');
        });
    }

    const galleryImages = document.querySelectorAll('.gallery-image');
    galleryImages.forEach(image => {
        image.addEventListener('click', function() {
            // Add functionality to enlarge the image or show in a modal
            alert('Image clicked: ' + this.src);
        });
    });
});