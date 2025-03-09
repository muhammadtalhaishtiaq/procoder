// Wait for the DOM to be fully loaded
document.addEventListener("DOMContentLoaded", () => {
    // Quick Start Options
    const quickStartButtons = document.querySelectorAll(".quick-start-options .btn")
    quickStartButtons.forEach((button) => {
        button.addEventListener("click", function() {
            const projectType = this.textContent.trim()
            console.log(`Starting new project: ${projectType}`)
                // In a real implementation, this would redirect to a project creation page
            window.location.href = "create-project.html?type=" + encodeURIComponent(projectType)
        })
    })

    // Tech Stack Icons
    const techIcons = document.querySelectorAll(".tech-icon")
    techIcons.forEach((icon, index) => {
        icon.addEventListener("click", () => {
            console.log(`Selected tech stack #${index + 1}`)
                // In a real implementation, this would redirect to a project creation page with the selected stack
            window.location.href = "create-project.html?stack=" + encodeURIComponent(index)
        })
    })

    // Search Box Functionality
    const searchInput = document.querySelector(".search-box input")
    if (searchInput) {
        searchInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                const query = this.value.trim()
                if (query) {
                    console.log(`Searching for: ${query}`)
                        // In a real implementation, this would process the search query
                    processSearchQuery(query)
                }
            }
        })
    }

    // Process search query (simulated AI response)
    function processSearchQuery(query) {
        // Simulate loading state
        searchInput.disabled = true
        const originalPlaceholder = searchInput.placeholder
        searchInput.placeholder = "Processing your request..."

        // Simulate API call delay
        setTimeout(() => {
            // Reset input
            searchInput.disabled = false
            searchInput.placeholder = originalPlaceholder
            searchInput.value = ""

            // Redirect to results page (in a real implementation)
            window.location.href = "search-results.html?q=" + encodeURIComponent(query)
        }, 1500)
    }
})