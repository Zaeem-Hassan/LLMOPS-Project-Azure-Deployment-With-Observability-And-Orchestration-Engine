document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('audit-form');
    const urlInput = document.getElementById('video-url');
    const submitBtn = document.getElementById('submit-btn');
    const statusBar = document.getElementById('status-bar');
    const statusText = document.getElementById('status-text');
    const resultsSection = document.getElementById('results');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const videoUrl = urlInput.value.trim();
        if (!videoUrl) return;

        // Show loading state
        submitBtn.classList.add('btn--loading');
        submitBtn.disabled = true;
        showStatus('⏳ Downloading video from YouTube...', false);
        hideResults();

        // Simulate progress stages
        const stages = [
            { text: '📥 Downloading video from YouTube...', delay: 3000 },
            { text: '☁️ Uploading to Azure Video Indexer...', delay: 8000 },
            { text: '🔍 Processing video — extracting transcript & OCR...', delay: 15000 },
            { text: '🧠 Running AI compliance analysis...', delay: 5000 },
        ];

        let currentStage = 0;
        const stageInterval = setInterval(() => {
            currentStage++;
            if (currentStage < stages.length) {
                updateStatus(stages[currentStage].text);
            }
        }, stages[currentStage]?.delay || 10000);

        try {
            const response = await fetch('/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_url: videoUrl })
            });

            clearInterval(stageInterval);

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Audit request failed');
            }

            const data = await response.json();
            hideStatus();
            renderResults(data);

        } catch (error) {
            clearInterval(stageInterval);
            showStatus(`❌ Error: ${error.message}`, true);
        } finally {
            submitBtn.classList.remove('btn--loading');
            submitBtn.disabled = false;
        }
    });

    function showStatus(text, isError) {
        statusBar.classList.add('status-bar--visible');
        statusBar.classList.toggle('status-bar--error', isError);
        const spinner = statusBar.querySelector('.status-bar__spinner');
        if (spinner) spinner.style.display = isError ? 'none' : 'block';
        statusText.innerHTML = text;
    }

    function updateStatus(text) {
        statusText.innerHTML = text;
    }

    function hideStatus() {
        statusBar.classList.remove('status-bar--visible');
    }

    function hideResults() {
        resultsSection.classList.remove('results--visible');
    }

    function renderResults(data) {
        resultsSection.classList.add('results--visible');

        // Status
        const isPassed = data.status && data.status.toUpperCase() === 'PASS';
        const statusVal = document.getElementById('result-status');
        statusVal.className = 'stat-card__value';
        statusVal.classList.add(isPassed ? 'stat-card__value--pass' : 'stat-card__value--fail');
        statusVal.innerHTML = `<span class="status-badge ${isPassed ? 'status-badge--pass' : 'status-badge--fail'}">${isPassed ? '✓ PASS' : '✗ FAIL'}</span>`;

        // Video ID
        document.getElementById('result-video-id').textContent = data.video_id || '—';

        // Violation Count
        const violationCount = data.compliance_results ? data.compliance_results.length : 0;
        const countEl = document.getElementById('result-violations-count');
        countEl.textContent = violationCount;
        countEl.className = 'stat-card__value ' + (violationCount === 0 ? 'stat-card__value--pass' : 'stat-card__value--fail');

        // Violations list
        const violationsContainer = document.getElementById('violations-list');
        violationsContainer.innerHTML = '';

        if (violationCount > 0) {
            document.getElementById('violations-section').style.display = 'block';
            data.compliance_results.forEach(issue => {
                const severity = (issue.severity || 'medium').toLowerCase();
                const el = document.createElement('div');
                el.className = `violation-item violation-item--${severity}`;
                el.innerHTML = `
                    <div class="violation-item__header">
                        <span class="violation-item__category">${escapeHtml(issue.category)}</span>
                        <span class="severity-tag severity-tag--${severity}">${escapeHtml(issue.severity)}</span>
                    </div>
                    <div class="violation-item__description">${escapeHtml(issue.description)}</div>
                `;
                violationsContainer.appendChild(el);
            });
        } else {
            document.getElementById('violations-section').style.display = 'none';
            violationsContainer.innerHTML = `
                <div class="no-violations">
                    <div class="no-violations__icon">✅</div>
                    <div class="no-violations__text">No Violations Detected</div>
                    <div class="no-violations__subtext">This video is compliant with all brand guidelines</div>
                </div>
            `;
            violationsContainer.parentElement.querySelector('.violations__title').style.display = 'none';
        }

        // Report summary
        const reportEl = document.getElementById('report-text');
        reportEl.textContent = data.final_report || 'No report available.';

        // Session ID
        const sessionEl = document.getElementById('session-id');
        if (sessionEl) sessionEl.textContent = data.session_id || '';
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
