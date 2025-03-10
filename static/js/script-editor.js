document.addEventListener("DOMContentLoaded", () => {
    // File Explorer Functionality
    const fileItems = document.querySelectorAll(".file-item")
    fileItems.forEach((item) => {
        item.addEventListener("click", function() {
            // Remove active class from all items
            fileItems.forEach((fi) => fi.classList.remove("active"))
                // Add active class to clicked item
            this.classList.add("active")
                // Update editor tab
            updateEditorTab(this.querySelector("span").textContent)
        })
    })

    // Editor Tabs Functionality
    const tabs = document.querySelectorAll(".tab")
    tabs.forEach((tab) => {
        const closeBtn = tab.querySelector("i")
        if (closeBtn) {
            closeBtn.addEventListener("click", (e) => {
                e.stopPropagation()
                if (tab.classList.contains("active") && tabs.length > 1) {
                    // If closing active tab, activate another tab
                    const nextTab = tab.nextElementSibling || tab.previousElementSibling
                    if (nextTab) nextTab.classList.add("active")
                }
                tab.remove()
            })
        }
    })

    // Terminal Simulation
    simulateTerminal()
})

function updateEditorTab(filename) {
    const editorTabs = document.querySelector(".editor-tabs")
    const existingTab = Array.from(editorTabs.querySelectorAll(".tab")).find(
        (tab) => tab.querySelector("span").textContent === filename,
    )

    if (existingTab) {
        // If tab exists, make it active
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"))
        existingTab.classList.add("active")
    } else {
        // Create new tab
        const newTab = document.createElement("div")
        newTab.className = "tab active"
        newTab.innerHTML = `
              <span>${filename}</span>
              <i class="material-icons">close</i>
          `

        // Remove active class from other tabs
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"))

        // Add new tab
        editorTabs.appendChild(newTab)

        // Add close functionality to new tab
        const closeBtn = newTab.querySelector("i")
        closeBtn.addEventListener("click", (e) => {
            e.stopPropagation()
            if (newTab.classList.contains("active") && document.querySelectorAll(".tab").length > 1) {
                const nextTab = newTab.nextElementSibling || newTab.previousElementSibling
                if (nextTab) nextTab.classList.add("active")
            }
            newTab.remove()
        })
    }
}

function simulateTerminal() {
    const terminalContent = document.querySelector(".terminal-content")
    const commands = [
        { command: "npm install", output: "Installing dependencies..." },
        { command: "added 1420 packages in 2m", output: "Done!" },
        { command: "Building project...", output: "Build completed successfully!" },
    ]

    let i = 0
    const interval = setInterval(() => {
        if (i < commands.length) {
            const commandLine = document.createElement("div")
            commandLine.className = "command-line"
            commandLine.innerHTML = `
                  <span class="text-success">$</span>
                  <span class="text-white">${commands[i].command}</span>
              `

            const outputLine = document.createElement("div")
            outputLine.className = "command-output text-secondary"
            outputLine.textContent = commands[i].output

            terminalContent.appendChild(commandLine)
            terminalContent.appendChild(outputLine)

            // Auto scroll to bottom
            terminalContent.scrollTop = terminalContent.scrollHeight

            i++
        } else {
            clearInterval(interval)
        }
    }, 2000)
}