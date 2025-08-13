document.addEventListener('DOMContentLoaded', function () {
    const API_BASE_URL = ''; // Vazio para usar rotas relativas, ex: /api/batches
    let activeCharts = {};
    let activeTimers = {};

    // --- Lógica do Tema Escuro/Claro ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const lightIcon = document.getElementById('theme-toggle-light-icon');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');

    const applyTheme = (isDark) => {
        document.documentElement.classList.toggle('dark', isDark);
        if(lightIcon) lightIcon.classList.toggle('hidden', isDark);
        if(darkIcon) darkIcon.classList.toggle('hidden', !isDark);
    };
    
    const initializeTheme = () => {
        const isDark = localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
        applyTheme(isDark);
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const isDark = !document.documentElement.classList.contains('dark');
            localStorage.setItem('color-theme', isDark ? 'dark' : 'light');
            applyTheme(isDark);
            if (document.getElementById('page-dashboard').classList.contains('active')) {
                const batchFilter = document.getElementById('batch-filter');
                if (batchFilter) applyFilters(batchFilter.value);
            }
        });
    }

    // --- Lógica de Navegação Principal ---
    const navButtons = document.querySelectorAll('.nav-button');
    const pageContents = document.querySelectorAll('.page-content');
    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const pageId = button.dataset.page;
            navButtons.forEach(btn => btn.classList.remove('active'));
            pageContents.forEach(content => content.classList.remove('active'));
            button.classList.add('active');
            const page = document.getElementById(`page-${pageId}`);
            if(page) page.classList.add('active');
            
            if (pageId === 'dashboard') fetchAndRenderDashboard();
            if (pageId === 'batches') {
                const batchPage = document.getElementById('page-batches');
                if(batchPage && !batchPage.innerHTML.trim()) {
                    const template = document.getElementById('batch-page-template');
                    if(template) {
                        batchPage.innerHTML = template.innerHTML;
                        initializeBatchPageListeners();
                    }
                }
                loadBatchesData();
            }
        });
    });
    
    // --- Lógica do Dashboard ---
    async function fetchAndRenderDashboard() {
        try {
            const batchResponse = await fetch(`${API_BASE_URL}/api/batches`);
            const allBatches = await batchResponse.json();
            populateBatchFilter(allBatches);
            const batchFilter = document.getElementById('batch-filter');
            await applyFilters(batchFilter ? batchFilter.value : 'all');
        } catch (error) { console.error("Erro ao carregar dados do dashboard:", error); }
    }
    
    function populateBatchFilter(batches) {
        const batchFilter = document.getElementById('batch-filter');
        if (!batchFilter) return;
        const currentVal = batchFilter.value;
        batchFilter.innerHTML = '<option value="all">Todos os Lotes</option>';
        if (batches) {
            batches.forEach(b => {
                const option = document.createElement('option');
                option.value = b.id;
                option.textContent = `${b.name} (ID: ${b.id})`;
                batchFilter.appendChild(option);
            });
        }
        batchFilter.value = currentVal;
    }
    
    async function applyFilters(batchId = 'all') {
        try {
            const dataUrl = new URL(`${API_BASE_URL}/api/dashboard_data`, window.location.origin);
            if (batchId !== 'all') {
                dataUrl.searchParams.append('batch_id', batchId);
            }
            const dataResponse = await fetch(dataUrl);
            const filteredData = await dataResponse.json();
            renderDashboard(filteredData);
        } catch (error) { console.error("Erro ao aplicar filtros:", error); }
    }

    const batchFilterSelect = document.getElementById('batch-filter');
    if (batchFilterSelect) batchFilterSelect.addEventListener('change', (e) => applyFilters(e.target.value));

    function renderDashboard(data) {
        destroyCharts();
        renderKPIs(data);
        renderSentimentDonut(data);
        renderTopicsBar(data);
        renderDetailsTable(data);
    }

    function destroyCharts() {
        Object.values(activeCharts).forEach(chart => {
            if (chart) chart.destroy();
        });
        activeCharts = {};
    }

    function getChartColors() {
        const isDark = document.documentElement.classList.contains('dark');
        return {
            textColor: isDark ? '#d1d5db' : '#374151',
            gridColor: isDark ? '#374151' : '#e5e7eb',
            sentiment: { 'Positivo': '#22c55e', 'Negativo': '#ef4444', 'Neutro': '#f59e0b' },
            topics: isDark? 'rgba(59, 130, 246, 0.7)' : 'rgba(59, 130, 246, 0.8)',
            donutBorder: isDark ? '#1f2937' : '#ffffff'
        };
    }

    function renderKPIs(data) {
        const kpiContainer = document.getElementById('kpis');
        if(!kpiContainer) return;
        if (!data || data.length === 0) {
            kpiContainer.innerHTML = `<p class="text-gray-500 dark:text-gray-400 col-span-full text-center">Nenhum dado encontrado para os filtros selecionados.</p>`;
            return;
        }
        const totalAnalises = data.length;
        const sentimentCounts = data.reduce((acc, item) => { if(item.sentiment) acc[item.sentiment] = (acc[item.sentiment] || 0) + 1; return acc; }, {});
        const predominantSentiment = Object.keys(sentimentCounts).length ? Object.keys(sentimentCounts).reduce((a, b) => sentimentCounts[a] > sentimentCounts[b] ? a : b) : 'N/A';
        const problemTopics = data.filter(d => d.sentiment === 'Negativo').reduce((acc, item) => { if(item.topic) acc[item.topic] = (acc[item.topic] || 0) + 1; return acc; }, {});
        const topProblem = Object.keys(problemTopics).length ? Object.keys(problemTopics).reduce((a, b) => problemTopics[a] > problemTopics[b] ? a : b) : 'Nenhum';

        kpiContainer.innerHTML = `
            <div class="card text-center"><h3 class="text-gray-500 dark:text-gray-400 text-sm font-medium uppercase">Total de Análises</h3><p class="text-4xl font-bold text-gray-900 dark:text-white mt-2">${totalAnalises}</p></div>
            <div class="card text-center"><h3 class="text-gray-500 dark:text-gray-400 text-sm font-medium uppercase">Sentimento Predominante</h3><p class="text-4xl font-bold text-amber-500 dark:text-amber-400 mt-2">${predominantSentiment}</p></div>
            <div class="card text-center"><h3 class="text-gray-500 dark:text-gray-400 text-sm font-medium uppercase">Principal Desafio</h3><p class="text-4xl font-bold text-red-600 dark:text-red-500 mt-2">${topProblem}</p></div>`;
    }
    
    function renderSentimentDonut(data) {
        const ctx = document.getElementById('sentimentChart')?.getContext('2d');
        if(!ctx || !data) return;
        const colors = getChartColors();
        const sentimentCounts = data.reduce((acc, item) => { if(item.sentiment) acc[item.sentiment] = (acc[item.sentiment] || 0) + 1; return acc; }, {});
        activeCharts.sentiment = new Chart(ctx, {
            type: 'doughnut', data: { labels: Object.keys(sentimentCounts), datasets: [{ data: Object.values(sentimentCounts), backgroundColor: Object.keys(sentimentCounts).map(key => colors.sentiment[key] || '#9ca3af'), borderColor: colors.donutBorder, borderWidth: 4, }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: colors.textColor } } } }
        });
    }

    function renderTopicsBar(data) {
        const ctx = document.getElementById('topicsChart')?.getContext('2d');
        if(!ctx || !data) return;
        const colors = getChartColors();
        const topicCounts = data.reduce((acc, item) => { if(item.topic) acc[item.topic] = (acc[item.topic] || 0) + 1; return acc; }, {});
        activeCharts.topics = new Chart(ctx, {
            type: 'bar', data: { labels: Object.keys(topicCounts), datasets: [{ label: 'Nº de Menções', data: Object.values(topicCounts), backgroundColor: colors.topics, }] },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: colors.textColor }, grid: { color: colors.gridColor } }, y: { ticks: { color: colors.textColor }, grid: { display: false } } }, plugins: { legend: { display: false } } }
        });
    }
    
    function renderDetailsTable(data) {
        const tableBody = document.getElementById('dataTable');
        if (!tableBody) return;
        tableBody.innerHTML = '';
        if (!data || data.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-gray-500">Nenhum dado para exibir.</td></tr>`; return;
        }
        const sentimentColors = { 'Positivo': 'text-green-600 dark:text-green-400', 'Negativo': 'text-red-600 dark:text-red-400', 'Neutro': 'text-amber-600 dark:text-amber-400' };
        data.forEach(item => {
            const row = document.createElement('tr');
            row.className = 'analysis-row hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors';
            row.dataset.id = item.id;
            row.innerHTML = `
                <td class="p-3 text-sm text-gray-700 dark:text-gray-300">${item.batch_name || 'N/A'}</td>
                <td class="p-3 font-medium ${sentimentColors[item.sentiment] || ''}">${item.sentiment || 'N/A'}</td>
                <td class="p-3 text-gray-700 dark:text-gray-300">${item.topic || 'N/A'}</td>
                <td class="p-3 text-gray-500 dark:text-gray-400 text-sm">${item.summary || 'N/A'}</td>`;
            tableBody.appendChild(row);
        });
        tableBody.querySelectorAll('.analysis-row').forEach(row => row.addEventListener('click', () => openAnalysisModal(row.dataset.id)));
    }

    async function loadTranscriptionModels() {
        const modelSelect = document.getElementById('model-id-select');
        if (!modelSelect) return;
        try {
            const response = await fetch(`${API_BASE_URL}/api/get_transcription_models`);
            if (!response.ok) throw new Error('Falha ao buscar modelos.');
            const models = await response.json();
            modelSelect.innerHTML = '';
            if (models.length === 0) {
                modelSelect.innerHTML = '<option value="">Nenhum modelo disponível</option>'; return;
            }
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                modelSelect.appendChild(option);
            });
        } catch (error) {
            console.error("Erro ao carregar modelos de transcrição:", error);
            modelSelect.innerHTML = '<option value="">Erro ao carregar</option>';
        }
    }

    function initializeBatchPageListeners() {
        const uploadForm = document.getElementById('upload-form');
        const fileUploadInput = document.getElementById('file-upload-input');
        
        if (uploadForm) {
            loadTranscriptionModels();

            uploadForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const uploadStatus = document.getElementById('upload-status');
                if (!fileUploadInput || fileUploadInput.files.length === 0) {
                    if (uploadStatus) uploadStatus.innerHTML = `<p class="text-yellow-500">Por favor, selecione um ou mais ficheiros.</p>`; 
                    return;
                }
                
                const formData = new FormData(uploadForm);
                if (uploadStatus) uploadStatus.innerHTML = `<p class="text-blue-500">A enviar ficheiros...</p>`;
                
                try {
                    const response = await fetch(`${API_BASE_URL}/api/upload`, { method: 'POST', body: formData });
                    const result = await response.json();
                    if (response.ok) {
                        if (uploadStatus) uploadStatus.innerHTML = `<p class="text-green-500">${result.message}</p>`;
                        uploadForm.reset();
                        setTimeout(loadBatchesData, 2000); 
                    } else { 
                        throw new Error(result.error || 'Erro desconhecido no servidor.'); 
                    }
                } catch (error) {
                    if (uploadStatus) uploadStatus.innerHTML = `<p class="text-red-500">Erro: ${error.message}</p>`;
                }
            });
        }
    }

    async function loadBatchesData() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/batches`);
            const data = await response.json();
            renderBatchesTable(data);
        } catch (error) { console.error("Erro ao carregar lotes:", error); }
    }

    function renderBatchesTable(data) {
        const tableBody = document.getElementById('batches-table');
        if(!tableBody) return;
        tableBody.innerHTML = '';
        if (!data || data.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="3" class="px-6 py-4 text-center text-gray-500">Nenhum lote encontrado.</td></tr>`; return;
        }
        data.forEach(item => {
            const rowHTML = `
                <tr class="batch-row hover:bg-gray-50 dark:hover:bg-gray-700/50" data-id="${item.id}">
                    <td class="px-6 py-4 font-medium text-gray-900 dark:text-white">${item.name}</td>
                    <td class="px-6 py-4 text-gray-500 dark:text-gray-400">${new Date(item.created_at).toLocaleString('pt-BR')}</td>
                    <td class="px-6 py-4 text-center text-gray-500 dark:text-gray-400">${item.file_count}</td>
                </tr>
                <tr class="files-row bg-gray-100 dark:bg-gray-900" id="files-for-batch-${item.id}">
                    <td colspan="3" class="p-0"><div class="p-4" id="files-table-${item.id}">A carregar ficheiros...</div></td>
                </tr>`;
            tableBody.insertAdjacentHTML('beforeend', rowHTML);
        });
        document.querySelectorAll('.batch-row').forEach(el => el.addEventListener('click', toggleBatchFiles));
    }

    async function toggleBatchFiles(event) {
        const batchId = event.currentTarget.dataset.id;
        const filesRow = document.getElementById(`files-for-batch-${batchId}`);
        if (!filesRow) return;
        const isVisible = filesRow.style.display === 'table-row';
        if (isVisible) {
            filesRow.style.display = 'none';
            if(activeTimers[batchId]) clearInterval(activeTimers[batchId]);
        } else {
            filesRow.style.display = 'table-row';
            await loadAndRenderBatchFiles(batchId);
        }
    }
    
    async function loadAndRenderBatchFiles(batchId) {
        const container = document.getElementById(`files-table-${batchId}`);
        if (!container) return;
        try {
            const response = await fetch(`${API_BASE_URL}/api/batch/${batchId}/details`);
            const files = await response.json();
            renderFilesTable(batchId, files);
            const isProcessing = files.some(f => f.status && !f.status.toLowerCase().includes('concluído') && !f.status.toLowerCase().includes('erro'));
            if (activeTimers[batchId]) clearInterval(activeTimers[batchId]);
            if (isProcessing) {
                activeTimers[batchId] = setInterval(() => loadAndRenderBatchFiles(batchId), 5000);
            }
        } catch (error) {
            container.innerHTML = `<p class="text-red-500">Erro ao carregar ficheiros.</p>`;
        }
    }

    function renderFilesTable(batchId, files) {
        const container = document.getElementById(`files-table-${batchId}`);
        if (!container) return;
        if (!files || files.length === 0) {
            container.innerHTML = `<p class="text-gray-500 p-2">Nenhum ficheiro neste lote.</p>`; return;
        }
        let tableHTML = `<table class="min-w-full">`;
        files.forEach(file => {
            let statusColor = 'text-gray-500 dark:text-gray-400';
            if (file.status === 'Concluído') statusColor = 'text-green-500 dark:text-green-400';
            else if (file.status && file.status.toLowerCase().includes('erro')) statusColor = 'text-red-500 dark:text-red-400';
            else statusColor = 'text-blue-500 dark:text-blue-400';
            
            let actions = '';
            if (file.status === 'Concluído') {
                actions = `<button class="view-transcription-btn text-green-500 hover:text-green-400" data-id="${file.id}">Ver Detalhes</button>`;
            } else if (file.status && file.status.toLowerCase().includes('erro')) {
                actions = `<button class="view-transcription-btn text-red-500 hover:text-red-400" data-id="${file.id}">Ver Erro</button>`;
            }
            tableHTML += `<tr class="border-t border-gray-200 dark:border-gray-700"><td class="p-2">${file.filename}</td><td class="p-2 font-medium ${statusColor}">${file.status}</td><td class="p-2 text-right">${actions}</td></tr>`;
        });
        tableHTML += `</table>`;
        container.innerHTML = tableHTML;
        container.querySelectorAll('.view-transcription-btn').forEach(btn => btn.addEventListener('click', (e) => openAnalysisModal(e.target.dataset.id)));
    }

    const modal = document.getElementById('transcription-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    async function openAnalysisModal(transcriptionId) {
        if (!modal || !transcriptionId) return;
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');
        modalTitle.textContent = "Análise Individual";
        modalContent.innerHTML = '<p>A carregar conteúdo...</p>';
        modal.classList.remove('hidden');
        try {
            const response = await fetch(`${API_BASE_URL}/api/transcription/${transcriptionId}`);
            const data = await response.json();
            const formattedText = data.transcript_text ? data.transcript_text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>') : '<p>Conteúdo não disponível.</p>';
            modalContent.innerHTML = formattedText;
        } catch (error) {
            modalContent.innerHTML = '<p class="text-red-500">Erro ao carregar o conteúdo.</p>';
        }
    }

    function hideModal() { if (modal) modal.classList.add('hidden'); }
    
    if (modalCloseBtn) modalCloseBtn.addEventListener('click', hideModal);
    if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) hideModal(); });
    
    // --- Carga Inicial ---
    initializeTheme();
    fetchAndRenderDashboard();
});