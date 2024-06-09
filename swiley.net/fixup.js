//optional JS
document.addEventListener('DOMContentLoaded', function() {
    // Array of all heading tags
    const headingTags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
    
    headingTags.forEach(tag => {
        // Select all headings of the current type
        const headings = document.querySelectorAll(tag);
        
        headings.forEach(heading => {
            // Generate a unique id for the heading if it doesn't already have one
            if (!heading.id) {
                heading.id = heading.textContent.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^\w\-]+/g, '');
            }
            
            // Wrap the heading content in an anchor tag
            const link = document.createElement('a');
            link.href = `#${heading.id}`;
            link.innerHTML = heading.innerHTML;
            heading.innerHTML = '';
            heading.appendChild(link);
        });
    });
});
