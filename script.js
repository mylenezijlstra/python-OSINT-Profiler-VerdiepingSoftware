const searchBtn = document.getElementById('searchBtn');
const firstNameInput = document.getElementById('firstName');
const lastNameInput = document.getElementById('lastName');
const loader = document.getElementById('loader');
const resultsSection = document.getElementById('resultsSection');
const profilesGrid = document.getElementById('profilesGrid');
const deepLinksGrid = document.getElementById('deepLinksGrid');

const API_BASE_URL = 'http://localhost:8000';

searchBtn.addEventListener('click', async () => {
    const first = firstNameInput.value.trim();
    const last = lastNameInput.value.trim();

    if (!first || !last) {
        alert('Please enter both first and last name.');
        return;
    }

    // Reset UI
    resultsSection.style.display = 'none';
    profilesGrid.innerHTML = '';
    deepLinksGrid.innerHTML = '';
    loader.style.display = 'block';
    searchBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/search?first=${encodeURIComponent(first)}&last=${encodeURIComponent(last)}`);
        const data = await response.json();

        displayResults(data);
    } catch (error) {
        console.error('Search failed:', error);
        alert('An error occurred while scanning. Make sure the backend server and its dependencies are running.');
    } finally {
        loader.style.display = 'none';
        searchBtn.disabled = false;
    }
});

function displayResults(data) {
    resultsSection.style.display = 'block';

    // Display Found Profiles
    if (data.profiles && data.profiles.length > 0) {
        data.profiles.forEach(profile => {
            const isFound = profile.status === 'Found';
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <div class="card-header">
                    <span class="platform-name">${profile.platform}</span>
                    <span class="status-badge ${isFound ? 'status-found' : 'status-notfound'}">
                        ${profile.status}
                    </span>
                </div>
                <div class="username-display">@${profile.username}</div>
                ${isFound ? `<a href="${profile.url}" target="_blank" class="visit-btn">View Profile</a>` : ''}
            `;
            profilesGrid.appendChild(card);
        });
    }

    // Display Deep Links
    if (data.deep_links && data.deep_links.length > 0) {
        data.deep_links.forEach(link => {
            const anchor = document.createElement('a');
            anchor.className = 'deep-link';
            anchor.href = link.url;
            anchor.target = '_blank';
            anchor.innerHTML = `
                <span>🔗</span>
                <span>Search on ${link.platform}</span>
            `;
            deepLinksGrid.appendChild(anchor);
        });
    }

    // Smooth scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}
