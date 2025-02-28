$('#generate-form').on('click', function(e) {
    e.preventDefault();
    const prompt = $('#prompt').val();
    console.log('Prompt:', prompt);
    if(prompt === '') {
        alert('Please enter a prompt.');
        return;
    }
    fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ prompt: prompt })
    })
    .then(response => response.json())
    .then(data => {
        window.location.href = '/result';
    })
    .catch(error => {
        alert('Error: ' + error.message);
    })
    .finally(() => {
        // loading.remove();
    });
});
// document.querySelector('#generate-form').addEventListener('submit', async (e) => {
//     e.preventDefault();
//     const prompt = document.querySelector('#prompt').value;
//     console.log('Prompt:', prompt);

//     // Show spinner
//     document.querySelector('#spinner').style.display = 'block';

//     try {
//         const response = await fetch('/generate', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({
//                 prompt: prompt,
//             })
//         });
//         console.log('response: ', response);
//         const data = await response.json();

//         if (data.error) {
//             alert(data.error);
//             return;
//         }

//         // Update DOM
//         document.querySelector('#code-block').innerText = data.code;
//         document.querySelector('#instructions').innerText = data.instructions;

//         // Refresh session list
//         // fetchSessions();
//     } catch (error) {
//         alert('Error generating code.');
//     } finally {
//         // Hide spinner
//         document.querySelector('#spinner').style.display = 'none';
//     }
// });

// function fetchSessions() {
//     fetch('/sessions')
//         .then(response => response.json())
//         .then(sessions => {
//             const sessionList = document.querySelector('#session-list');
//             sessionList.innerHTML = '';
//             sessions.forEach(session => {
//                 const li = document.createElement('li');
//                 li.textContent = `Session ${session.id} - ${session.timestamp}`;
//                 sessionList.appendChild(li);
//             });
//         });
// }