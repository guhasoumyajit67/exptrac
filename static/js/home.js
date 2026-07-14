document.addEventListener("DOMContentLoaded", function () {
    // ============================================
    // 1. GET DATA FROM WINDOW OBJECT
    // ============================================
    const data = window.dashboardData || {};
    
    const categoryLabels = data.categoryLabels || [];
    const categoryAmounts = data.categoryAmounts || [];
    const masterCategoryLabels = data.masterCategoryLabels || [];
    const masterCategoryAmounts = data.masterCategoryAmounts || [];
    const trendLabels = data.trendLabels || [];
    const trendAmounts = data.trendAmounts || [];
    const aggregateMonthlySum = parseFloat(data.totalOutflow || '0');

    // ============================================
    // 2. UPDATE PERCENTAGES IN TABLE
    // ============================================
    if (aggregateMonthlySum > 0) {
        document.querySelectorAll('.table-pct-node').forEach(node => {
            const rowAmount = parseFloat(node.getAttribute('data-amount')) || 0;
            const evaluatedPct = ((rowAmount / aggregateMonthlySum) * 100).toFixed(1);
            node.textContent = `${evaluatedPct}%`;
        });
    }

    // ============================================
    // 3. CREATE LINE CHART (Trend)
    // ============================================
    const ctxLine = document.getElementById('trendLineChart');
    if (ctxLine && trendLabels.length) {
        const chartContext = ctxLine.getContext('2d');
        const gradientFill = chartContext.createLinearGradient(0, 0, 0, 260);
        gradientFill.addColorStop(0, 'rgba(13, 110, 253, 0.25)');
        gradientFill.addColorStop(0.5, 'rgba(13, 110, 253, 0.08)');
        gradientFill.addColorStop(1, 'rgba(255, 255, 255, 0.00)');
        new Chart(chartContext, {
            type: 'line',
            data: {
                labels: trendLabels,
                datasets: [{
                    label: 'Cumulative Total',
                    data: trendAmounts,
                    borderColor: '#0d6efd',
                    backgroundColor: gradientFill,
                    borderWidth: 3,
                    tension: 0.32,
                    fill: true,
                    pointBackgroundColor: '#0d6efd',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 1.5,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        displayColors: false,
                        padding: 10,
                        callbacks: {
                            title: function(context) { return `Date: ${context[0].label}`; },
                            label: function(context) {
                                const rawValue = context.raw || 0;
                                return `Amount: ₹${rawValue.toLocaleString('en-IN')}`;
                            }
                        }
                    }
                },
                scales: {
                    y: { grid: { color: 'rgba(241, 245, 249, 1)' }, ticks: { font: { size: 11 }, callback: function(value) { return '₹' + value; } } },
                    x: { grid: { display: false }, ticks: { font: { size: 11 } } }
                }
            }
        });
    }

    // ============================================
    // 4. TOOLTIP CONFIGURATION
    // ============================================
    const multiLineTooltipConfig = {
        displayColors: false,
        callbacks: {
            title: function(context) { return context[0].label; },
            label: function(context) {
                const rawValue = context.raw || 0;
                const totalSum = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                const percentage = totalSum > 0 ? ((rawValue / totalSum) * 100).toFixed(1) : 0;
                return [`Total Cost: ₹${rawValue.toFixed(0)}`, `Percentage: ${percentage}%`];
            }
        }
    };

    // ============================================
    // 5. CREATE ITEM DOUGHNUT CHART (Left)
    // ============================================
    const ctxDoughnut = document.getElementById('categoryDoughnutChart');
    if (ctxDoughnut) {
        new Chart(ctxDoughnut.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: categoryLabels.length ? categoryLabels : ['No Records'],
                datasets: [{
                    data: categoryAmounts.length ? categoryAmounts : [1],
                    backgroundColor: ['#0d6efd', '#198754', '#ffc107', '#0dcaf0', '#6c757d', '#6610f2'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 }, padding: 15 } },
                    tooltip: multiLineTooltipConfig
                },
                cutout: '72%'
            }
        });
    }

    // ============================================
    // 6. CREATE CATEGORY DOUGHNUT CHART (Right)
    // ============================================
    const ctxMasterDoughnut = document.getElementById('masterCategoryDoughnutChart');
    if (ctxMasterDoughnut) {
        new Chart(ctxMasterDoughnut.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: masterCategoryLabels.length ? masterCategoryLabels : ['No Categories'],
                datasets: [{
                    data: masterCategoryAmounts.length ? masterCategoryAmounts : [1],
                    backgroundColor: ['#198754', '#20c997', '#0d6efd', '#ffc107', '#0dcaf0', '#6610f2'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 }, padding: 15 } },
                    tooltip: multiLineTooltipConfig
                },
                cutout: '72%'
            }
        });
    }
});