function generateTable(lemmas, containerId) {
    if (!lemmas || lemmas.length === 0) return;

    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Container not found');
        return;
    }

    // Create button
    const button = document.createElement('button');
    button.className = 'collapsible';
    button.textContent = 'More Information';

    // Create content div
    const content = document.createElement('div');
    content.className = 'content';

    // Create table
    const table = document.createElement('table');

    // Create table headers
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const headers = ['ID', 'Label', 'Language', 'Description', 'Link', 'Select'];

    headers.forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');
    lemmas.forEach(lemma => {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${lemma.id}</td>
            <td>${lemma.label}</td>
            <td>${lemma.language}</td>
            <td>${lemma.description}</td>
            <td><a href="https://wikidata.org/wiki/Lexeme:${lemma.id}" target="_blank">${lemma.label}</a></td>
            <td><button class="select-btn">Select</button></td>
        `;

        // Add event listener to the select button
        row.querySelector('.select-btn').addEventListener('click', function() {
            // Remove highlight from any previously selected row
            document.querySelectorAll('tr.selected').forEach(el => el.classList.remove('selected'));
            // Highlight the selected row
            row.classList.add('selected');
        });

        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    // Append elements
    content.appendChild(table);
    container.appendChild(button);
    container.appendChild(content);

    // Collapsible button functionality
    button.addEventListener('click', function() {
        content.style.display = content.style.display === 'block' ? 'none' : 'block';
    });

    // CSS for highlighting the selected row
    const style = document.createElement('style');
    style.textContent = `
        .selected {
            background-color: yellow !important;
        }
    `;
    document.head.appendChild(style);
}
