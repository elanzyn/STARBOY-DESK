window.dashboardShell = function () {
    return {
        sidebarOpen: false,
        dark: document.documentElement.classList.contains('dark'),
        init() {
            this.dark = document.documentElement.classList.contains('dark');
            document.documentElement.classList.toggle('light', !this.dark);
            this.syncThemeIcon();
        },
        toggleTheme() {
            this.dark = !this.dark;
            document.documentElement.classList.toggle('dark', this.dark);
            document.documentElement.classList.toggle('light', !this.dark);
            localStorage.setItem('theme', this.dark ? 'dark' : 'light');
            this.syncThemeIcon();
        },
        syncThemeIcon() {
            const icon = document.getElementById('dashboard-theme-icon');
            if (!icon) return;
            icon.innerHTML = this.dark
                ? '<svg class="h-5 w-5 text-amber-300" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" stroke-width="1.75" stroke-linejoin="round"/></svg>'
                : '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 3v1m0 16v1M4.2 4.2l.7.7m14.2 14.2.7.7M3 12h1m16 0h1M4.2 19.8l.7-.7m14.2-14.2.7-.7M12 6a6 6 0 1 0 0 12 6 6 0 0 0 0-12Z" stroke-width="1.75" stroke-linecap="round"/></svg>';
        },
    };
};

function buildChart(canvasId, chartData, type, options) {
    const canvas = document.getElementById(canvasId);
    const dataScript = document.getElementById(chartData);

    if (!canvas || !dataScript || typeof Chart === 'undefined') {
        return;
    }

    const parsedData = JSON.parse(dataScript.textContent);
    new Chart(canvas, {
        type,
        data: parsedData,
        options,
    });
}

document.addEventListener('DOMContentLoaded', () => {
    buildChart('ticketsChart', 'tickets-chart-data', 'line', {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(148, 163, 184, 0.08)',
                },
                ticks: {
                    color: 'rgba(226, 232, 240, 0.7)',
                },
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(148, 163, 184, 0.08)',
                },
                ticks: {
                    color: 'rgba(226, 232, 240, 0.7)',
                },
            },
        },
    });

    buildChart('statusChart', 'status-chart-data', 'doughnut', {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    color: 'rgba(226, 232, 240, 0.8)',
                    padding: 18,
                },
            },
        },
    });

    // Ensure selects follow theme by adding data attribute and inline styles where CSS cannot control native rendering
    function applyGlobalSelectStyling(){
        document.querySelectorAll('select').forEach(s => {
            try{
                s.setAttribute('data-custom-select','true');
                s.classList.add('select-sd');
                const isLight = document.documentElement.classList.contains('light');
                const bg = isLight ? 'rgba(255,255,255,0.96)' : 'rgba(15,23,42,0.95)';
                const fg = isLight ? '#0f172a' : '#e6eef8';
                const border = isLight ? '1px solid rgba(15,23,42,0.16)' : '1px solid rgba(255,255,255,0.06)';
                s.style.backgroundColor = bg;
                s.style.color = fg;
                s.style.border = border;
            }catch(e){console.warn('applyGlobalSelectStyling', e)}
            // try style options too (best-effort)
            try{
                const isLight = document.documentElement.classList.contains('light');
                const optBg = isLight ? '#ffffff' : 'rgba(15,23,42,0.95)';
                const optFg = isLight ? '#0f172a' : '#e6eef8';
                Array.from(s.options).forEach(opt => { opt.style.background = optBg; opt.style.color = optFg; });
            }catch(e){}
        });
    }

    document.addEventListener('DOMContentLoaded', function(){
        applyGlobalSelectStyling();
        // Re-apply when dynamic content may change (e.g., after AJAX)
        document.addEventListener('click', function(){ setTimeout(applyGlobalSelectStyling, 50); });
    });
});
