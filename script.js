document.addEventListener('DOMContentLoaded', () => {
    // 1. A/B Switcher Logic
    const abSwitcher = document.getElementById('ab-switcher');
    const toggleBtn = document.getElementById('ab-toggle-btn');
    const abBtns = document.querySelectorAll('.ab-btn');
    
    // Toggle Switcher collapse
    if(toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            abSwitcher.classList.toggle('collapsed');
        });
    }

    // Handle variant switching
    abBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Remove active class from all
            abBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked
            e.target.classList.add('active');
            
            const variant = e.target.getAttribute('data-variant');
            
            // Hide all variant contents in Hero
            document.querySelectorAll('#hero-headline span[class^="variant-"]').forEach(el => {
                if(!el.classList.contains('highlight')) {
                    el.classList.add('hidden');
                }
            });
            document.querySelectorAll('#hero-cta-container a[class*="variant-"]').forEach(el => {
                el.classList.add('hidden');
            });
            
            // Show selected variant
            document.querySelector(`#hero-headline .variant-${variant}`).classList.remove('hidden');
            document.querySelector(`#hero-cta-container .variant-${variant}`).classList.remove('hidden');
        });
    });

    // 2. Accordion Logic for FAQ
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    
    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const accordionItem = header.parentElement;
            const accordionContent = header.nextElementSibling;
            
            // Close all other active items
            document.querySelectorAll('.accordion-item.active').forEach(item => {
                if(item !== accordionItem) {
                    item.classList.remove('active');
                    item.querySelector('.accordion-content').style.maxHeight = null;
                }
            });

            // Toggle current item
            accordionItem.classList.toggle('active');
            
            if (accordionItem.classList.contains('active')) {
                accordionContent.style.maxHeight = accordionContent.scrollHeight + "px";
            } else {
                accordionContent.style.maxHeight = null;
            }
        });
    });

    // 3. Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            if(this.getAttribute('href') !== '#') {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if(target) {
                    window.scrollTo({
                        top: target.offsetTop - 80, // adjust for header/switcher if any
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
});
