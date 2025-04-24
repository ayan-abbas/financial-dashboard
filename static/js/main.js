document.addEventListener('DOMContentLoaded', function() {
    // Load more functionality with AJAX
    const loadMoreBtn = document.querySelector('.load-more-btn');
    
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            const newsContainer = document.getElementById('news-container');
            const loadingText = 'Loading...';
            const originalText = this.textContent;
            
            // Show loading state
            this.textContent = loadingText;
            this.disabled = true;
            
            // Fetch more articles
            fetch(href)
                .then(response => response.text())
                .then(html => {
                    // Create a temporary element to parse the HTML
                    const temp = document.createElement('div');
                    temp.innerHTML = html;
                    
                    // Extract new articles
                    const newArticles = temp.querySelector('#news-container').innerHTML;
                    
                    // Append to existing container
                    newsContainer.innerHTML += newArticles;
                    
                    // Update the button's href to point to the next page
                    const nextPage = parseInt(href.split('page=')[1]) + 1;
                    this.setAttribute('href', href.replace(/page=\d+/, `page=${nextPage}`));
                    
                    // Check if there are more articles
                    const hasMore = temp.querySelector('.load-more-btn');
                    if (!hasMore) {
                        this.remove(); // Remove button if no more articles
                    } else {
                        // Reset button state
                        this.textContent = originalText;
                        this.disabled = false;
                    }
                })
                .catch(error => {
                    console.error('Error loading more articles:', error);
                    this.textContent = 'Error loading articles. Try again.';
                    this.disabled = false;
                });
        });
    }
});
