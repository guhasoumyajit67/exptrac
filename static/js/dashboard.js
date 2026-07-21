// ============================================
// GLOBAL VARIABLES
// ============================================
let itemTableSortDirections = { 0: true, 1: false, 2: true, 3: true };
let chartInstances = [];

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Toggle between chart and table view
 */
function toggleView(viewId1, viewId2) {
    const el1 = document.getElementById(viewId1);
    const el2 = document.getElementById(viewId2);
    if (el1) el1.classList.toggle('view-hidden');
    if (el2) el2.classList.toggle('view-hidden');
}

/**
 * Sort item table by column
 */
function sortItemTable(columnIndex, isNumeric) {
    const tableBody = document.getElementById("item-table-body");
    if (!tableBody) return;
    const rows = Array.from(tableBody.querySelectorAll("tr"));
    if (rows.length <= 1 && rows[0]?.querySelector("td[colspan]")) return;

    itemTableSortDirections[columnIndex] = !itemTableSortDirections[columnIndex];
    const isAscending = itemTableSortDirections[columnIndex];

    rows.sort((rowA, rowB) => {
        let cellA = rowA.children[columnIndex]?.textContent.trim() || '';
        let cellB = rowB.children[columnIndex]?.textContent.trim() || '';

        if (isNumeric) {
            let valA = parseFloat(cellA.replace(/[^0-9.-]/g, "")) || 0;
            let valB = parseFloat(cellB.replace(/[^0-9.-]/g, "")) || 0;
            return isAscending ? valA - valB : valB - valA;
        } else {
            return isAscending 
                ? cellA.localeCompare(cellB, undefined, { numeric: true, sensitivity: 'base' })
                : cellB.localeCompare(cellA, undefined, { numeric: true, sensitivity: 'base' });
        }
    });

    tableBody.innerHTML = "";
    rows.forEach(row => tableBody.appendChild(row));
}

/**
 * Generate dynamic colors
 */
function generateColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        const hue = (i * 137.508) % 360;
        const saturation = 65 + (i % 20);
        const lightness = 45 + (i % 15);
        colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
    }
    return colors;
}

/**
 * Export chart as image
 */
function exportChartAsImage(chartId, format = 'png') {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `chart_${chartId}.${format}`;
    link.href = canvas.toDataURL(`image/${format}`);
    link.click();
}

/**
 * Export analytics as PDF (Server-side with WeasyPrint)
 */
function exportAnalyticsPDF() {
    // Get the selected month from dropdown
    const select = document.querySelector('select[name="month"]');
    const month = select ? select.value : '';
    
    // Build the URL
    let url = '/analytics/dashboard/export-analytics-pdf/';
    if (month) {
        url += `?month=${month}`;
    }
    
    // Open PDF in new tab (server-side generation)
    window.open(url, '_blank');
}

// Make functions globally accessible
window.toggleView = toggleView;
window.sortItemTable = sortItemTable;
window.exportAnalyticsPDF = exportAnalyticsPDF;
window.exportChartAsImage = exportChartAsImage;

// ============================================
// MAIN - DOM READY
// ============================================
document.addEventListener("DOMContentLoaded", function() {
    
    // ============================================
    // 1. GET DATA FROM WINDOW OBJECT
    // ============================================
    const data = window.analyticsData || {};
    
    const dailyLabels = data.dailyLabels || [];
    const dailyTotals = data.dailyTotals || [];
    const categoryLabels = data.categoryLabels || [];
    const categoryTotals = data.categoryTotals || [];
    const categoryColors = data.categoryColors || [];
    const payerLabels = data.payerLabels || [];
    const payerTotals = data.payerTotals || [];
    const payerColors = data.payerColors || [];
    const itemDataMatrix = data.itemDataMatrix || [];
    const parsedMedian = Number(data.parsedMedian) || 0;
    const overallSpent = Number(data.overallSpent) || 0;
    const currentMonthLabel = data.currentMonthLabel || '';
    const weeklyLabels = data.weeklyLabels || [];
    const weeklyTotals = data.weeklyTotals || [];

    // ============================================
    // 2. CHECK FOR EMPTY DATA
    // ============================================
    const hasData = dailyLabels && dailyLabels.length > 0 && 
                    dailyTotals && dailyTotals.some(t => t > 0);

    if (!hasData) {
        document.querySelectorAll('.card canvas').forEach(canvas => {
            const container = canvas.parentElement;
            container.style.position = 'relative';
            const msg = document.createElement('div');
            msg.className = 'text-center text-muted py-5';
            msg.innerHTML = `
                <i class="bi bi-inbox fs-1 d-block mb-3 opacity-50"></i>
                <p class="fw-light">No transactions recorded for this period</p>
                <small>Start adding expenses to see analytics</small>
            `;
            container.appendChild(msg);
            canvas.style.display = 'none';
        });
        return;
    }

    // ============================================
    // 3. POPULATE TIMELINE TABLE
    // ============================================
    const tableBody = document.getElementById('timeline-table-body');
    if (tableBody) {
        if (dailyLabels.length > 0) {
            tableBody.innerHTML = "";
            dailyLabels.forEach((label, index) => {
                tableBody.insertAdjacentHTML('beforeend', `<tr>
                    <td class="py-2">${label} ${currentMonthLabel}</td>
                    <td class="text-end fw-bold py-2">₹${dailyTotals[index].toFixed(2)}</td>
                </tr>`);
            });
        } else {
            tableBody.innerHTML = `<tr><td colspan="2" class="text-muted text-center py-3">No records found.</td></tr>`;
        }
    }

    // ============================================
    // 4. POPULATE CATEGORY ALLOCATION TABLE
    // ============================================
    const categoryTableBody = document.getElementById('category-table-body');
    if (categoryTableBody) {
        if (categoryLabels.length > 0) {
            categoryTableBody.innerHTML = "";
            const colors = generateColors(categoryLabels.length);
            categoryLabels.forEach((label, index) => {
                const costVal = categoryTotals[index];
                const colorVal = categoryColors[index] || colors[index % colors.length] || '#6c757d';
                
                const percentageDisplay = overallSpent > 0 
                    ? ((costVal / overallSpent) * 100).toFixed(1) + '%' 
                    : '0.0%';

                const formattedCost = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(costVal);

                const row = `<tr>
                    <td class="py-2">
                        <span class="d-inline-block rounded-circle me-2" style="width: 10px; height: 10px; background-color: ${colorVal};"></span>
                        ${label}
                    </td>
                    <td class="text-end fw-bold py-2">${formattedCost}</td>
                    <td class="text-end text-secondary py-2">${percentageDisplay}</td>
                </tr>`;
                categoryTableBody.insertAdjacentHTML('beforeend', row);
            });
        } else {
            categoryTableBody.innerHTML = `<tr><td colspan="3" class="text-muted text-center py-3">No category records found.</td></tr>`;
        }
    }

    // ============================================
    // 5. POPULATE ITEM TABLE
    // ============================================
    const itemTableBody = document.getElementById('item-table-body');
    if (itemTableBody) {
        if (itemDataMatrix && itemDataMatrix.length > 0) {
            itemTableBody.innerHTML = ""; 
            itemDataMatrix.forEach((obj) => {
                const formattedCost = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(obj.cost);
                const quantityColumnDisplay = (obj.qty && obj.unit) ? `${obj.qty} ${obj.unit}` : '';
                
                itemTableBody.insertAdjacentHTML('beforeend', `<tr>
                    <td class="py-2 fw-medium">${obj.name}</td>
                    <td class="text-end fw-bold text-dark py-2">${formattedCost}</td>
                    <td class="text-end text-secondary py-2">${quantityColumnDisplay}</td>
                    <td class="text-end text-dark py-2">${obj.times || 0}</td>
                </tr>`);
            });
        } else {
            itemTableBody.innerHTML = `<tr><td colspan="4" class="text-muted text-center py-4">No data logged.</td></tr>`;
        }
    }

    // ============================================
    // 6. POPULATE PAYER TABLE
    // ============================================
    const payerTableBody = document.getElementById('payer-table-body');
    if (payerTableBody) {
        if (payerLabels.length > 0) {
            payerTableBody.innerHTML = "";
            payerLabels.forEach((label, index) => {
                const totalPaid = payerTotals[index];
                
                const sharePercentageDisplay = overallSpent > 0 
                    ? ((totalPaid / overallSpent) * 100).toFixed(1) + '%' 
                    : '0.0%';

                const formattedCost = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(totalPaid);

                const row = `<tr>
                    <td class="fw-bold py-2">${label}</td>
                    <td class="text-end fw-bold text-danger py-2">${formattedCost}</td>
                    <td class="text-end text-secondary py-2">${sharePercentageDisplay}</td>
                </tr>`;
                payerTableBody.insertAdjacentHTML('beforeend', row);
            });
        } else {
            payerTableBody.innerHTML = `<tr><td colspan="3" class="text-muted text-center py-3">No payer logs calculated.</td></tr>`;
        }
    }

    // ============================================
    // 7. DAILY BAR CHART
    // ============================================
    const ctxDaily = document.getElementById('dailyBarChart');
    if (ctxDaily) {
        const medianTooltip = document.getElementById('medianTooltip');
        const dailyChartInstance = new Chart(ctxDaily.getContext('2d'), {
            type: 'bar',
            data: {
                labels: dailyLabels,
                datasets: [{
                    label: 'Day Cost (₹)',
                    data: dailyTotals,
                    backgroundColor: '#e0a800',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onHover: (event, activeElements) => {
                    if (!dailyChartInstance.scales || !dailyChartInstance.scales.y) return;
                    const yScale = dailyChartInstance.scales.y;
                    const medianPixelY = yScale.getPixelForValue(parsedMedian);
                    const canvasPosition = Chart.helpers.getRelativePosition(event, dailyChartInstance);

                    if (Math.abs(canvasPosition.y - medianPixelY) < 8) {
                        medianTooltip.classList.remove('d-none');
                        medianTooltip.style.top = (medianPixelY - 32) + 'px';
                        medianTooltip.style.left = (canvasPosition.x + 12) + 'px';
                        medianTooltip.innerHTML = `Median: ₹${parsedMedian.toFixed(0)}`;
                    } else if (activeElements.length === 0) {
                        medianTooltip.classList.add('d-none');
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        backgroundColor: '#1e293b',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: function(context) { 
                                return `Day ${context[0].label}`; 
                            },
                            label: function(context) {
                                const formattedValue = new Intl.NumberFormat('en-IN', { 
                                    style: 'currency', 
                                    currency: 'INR', 
                                    maximumFractionDigits: 0 
                                }).format(context.parsed.y);
                                return `Day Cost: ${formattedValue}`;
                            }
                        }
                    },
                    annotation: {
                        annotations: {
                            medianLine: {
                                type: 'line',
                                yMin: parsedMedian,
                                yMax: parsedMedian,
                                borderColor: '#dc3545',
                                borderWidth: 1.5,
                                borderDash: [5, 5]
                            }
                        }
                    }
                }
            }
        });
        chartInstances.push(dailyChartInstance);
    }

    // ============================================
    // 8. ITEM TREEMAP CHART
    // ============================================
    const ctxTreemap = document.getElementById('itemTreemapChart');
    if (ctxTreemap && itemDataMatrix && itemDataMatrix.length > 0) {
        const poolColors = generateColors(itemDataMatrix.length);
        const treemapInstance = new Chart(ctxTreemap.getContext('2d'), {
            type: 'treemap',
            data: {
                datasets: [{
                    tree: itemDataMatrix,
                    key: 'cost',
                    spacing: 3,
                    borderWidth: 0,
                    borderRadius: 6,
                    backgroundColor: (ctx) => {
                        if (ctx.type !== 'data' || !ctx.raw) return 'transparent';
                        return poolColors[ctx.dataIndex % poolColors.length];
                    },
                    labels: {
                        display: false 
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'nearest',
                    intersect: true
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        position: 'nearest',
                        xAlign: 'center',
                        yAlign: 'bottom',
                        caretSize: 10,
                        caretPadding: 12,
                        callbacks: {
                            title: (items) => items[0] && items[0].raw ? items[0].raw._data.name : '',
                            label: (item) => {
                                if (!item || !item.raw) return '';
                                const obj = item.raw._data;
                                const formattedCost = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(obj.cost);
                                
                                if (obj.qty && obj.unit) {
                                    return [
                                        `Total Cost: ${formattedCost}`,
                                        `Quantity: ${obj.qty} ${obj.unit}`
                                    ];
                                }
                                return `Total Cost: ${formattedCost}`;
                            }
                        }
                    }
                }
            },
            plugins: [{
                id: 'customTreemapLabels',
                afterDatasetsDraw: (chart) => {
                    const { ctx } = chart;
                    const dataset = chart.data.datasets[0];
                    if (!dataset || !dataset.data) return;

                    ctx.save();
                    
                    chart.getDatasetMeta(0).data.forEach((metaRectangle, index) => {
                        const rawItemData = dataset.tree[index];
                        if (!rawItemData) return;

                        const boxX = metaRectangle.x;
                        const boxY = metaRectangle.y;
                        const boxWidth = metaRectangle.width;
                        const boxHeight = metaRectangle.height;

                        if (boxWidth < 65 || boxHeight < 35) return;

                        ctx.fillStyle = '#ffffff';
                        ctx.font = '400 11px system-ui, -apple-system, sans-serif';
                        ctx.textAlign = 'left';
                        ctx.textBaseline = 'top';

                        let displayName = rawItemData.name;
                        if (boxWidth < 120 && displayName.length > 10) {
                            displayName = displayName.substring(0, 9) + '...';
                        } else if (boxWidth < 150 && displayName.length > 14) {
                            displayName = displayName.substring(0, 13) + '...';
                        }

                        ctx.fillText(displayName, boxX + 10, boxY + 10);

                        const currencyStr = '₹' + Number(rawItemData.cost).toLocaleString('en-IN');
                        ctx.fillText(currencyStr, boxX + 10, boxY + 25);

                        if (rawItemData.qty && rawItemData.unit && boxHeight > 45) {
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'bottom';
                            ctx.font = '400 9px system-ui, -apple-system, sans-serif';
                            ctx.fillStyle = '#f1f5f9';

                            const rawQuantityString = `${rawItemData.qty} ${rawItemData.unit}`;
                            ctx.fillText(rawQuantityString, (boxX + boxWidth) - 11, (boxY + boxHeight) - 11);
                        }
                    });

                    ctx.restore();
                }
            }]
        });
        chartInstances.push(treemapInstance);
    }


    
    // ============================================
    // 9. CATEGORY DOUGHNUT CHART
    // ============================================
    const ctxDoughnut = document.getElementById('categoryDoughnutChart');
    if (ctxDoughnut && categoryLabels.length > 0) {
        const colors = categoryColors.length > 0 ? categoryColors : generateColors(categoryLabels.length);
        
        // Check if mobile viewport
        const isMobile = window.innerWidth < 576;
        
        const doughnutInstance = new Chart(ctxDoughnut.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: categoryLabels,
                datasets: [{ data: categoryTotals, backgroundColor: colors, borderWidth: 2, borderColor: '#ffffff' }]
            },
            plugins: [ChartDataLabels],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        display: !isMobile, // Hide legend on mobile
                        position: 'right', 
                        align: 'center',
                        labels: { 
                            boxWidth: 12, 
                            padding: 14, 
                            color: '#4b5563'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: (items) => items[0] ? items[0].label : '',
                            label: (context) => {
                                const rawValue = context.parsed;
                                const datasetData = context.dataset.data;
                                const cumulativeTotal = datasetData.reduce((sum, val) => sum + val, 0);
                                const sharePercentage = cumulativeTotal > 0 ? ((rawValue / cumulativeTotal) * 100).toFixed(1) + '%' : '0.0%';
                                const formattedCost = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0}).format(rawValue);
                                return [
                                    `Total Cost: ${formattedCost}`,
                                    `Percentage: ${sharePercentage}`
                                ];
                            }
                        }
                    },
                    datalabels: {
                        color: '#ffffff',
                        font: {
                            size: 11,
                            weight: '500',
                            family: 'system-ui, -apple-system, sans-serif'
                        },
                        anchor: 'center',
                        align: 'center',
                        formatter: (value, context) => {
                            const datasetData = context.chart.data.datasets[0].data;
                            const cumulativeTotal = datasetData.reduce((sum, val) => sum + val, 0);
                            
                            if (cumulativeTotal === 0) return '';
                            
                            const percentage = (value / cumulativeTotal) * 100;
                            if (percentage < 3.5) return '';
                            
                            return percentage.toFixed(1) + '%';
                        }
                    }
                },
                cutout: '65%'
            }
        });
        chartInstances.push(doughnutInstance);
        
        // Handle resize for legend visibility
        const handleResize = function() {
            const newIsMobile = window.innerWidth < 576;
            const currentOptions = doughnutInstance.options;
            
            // Update legend display based on screen size
            currentOptions.plugins.legend.display = !newIsMobile;
            doughnutInstance.update();
        };
        
        window.addEventListener('resize', handleResize);
        doughnutInstance._resizeHandler = handleResize;
    }



    // ============================================
    // 10. PAYER HORIZONTAL BAR CHART
    // ============================================
    const ctxPayer = document.getElementById('payerBarChart');
    if (ctxPayer && payerLabels.length > 0) {
        const colors = payerColors.map(c => c || '#0d6efd');
        const payerInstance = new Chart(ctxPayer.getContext('2d'), {
            type: 'bar',
            data: {
                labels: payerLabels,
                datasets: [{ 
                    label: 'Total Paid (₹)', 
                    data: payerTotals, 
                    backgroundColor: colors, 
                    borderRadius: 6, 
                    barThickness: 24 
                }]
            },
            plugins: [ChartDataLabels],
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        backgroundColor: '#1e293b',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: function(context) { 
                                return context[0] ? context[0].label : ''; 
                            },
                            label: function(context) {
                                const rawValue = context.parsed.x;
                                const datasetData = context.dataset.data;
                                const cumulativeTotal = datasetData.reduce((sum, val) => sum + val, 0);
                                
                                const sharePercentage = cumulativeTotal > 0 
                                    ? ((rawValue / cumulativeTotal) * 100).toFixed(1) + '%' 
                                    : '0.0%';

                                const formattedValue = new Intl.NumberFormat('en-IN', { 
                                    style: 'currency', 
                                    currency: 'INR', 
                                    maximumFractionDigits: 0 
                                }).format(rawValue);

                                return [
                                    `Total Paid: ${formattedValue}`,
                                    `Percentage: ${sharePercentage}`
                                ];
                            }
                        }
                    },
                    datalabels: {
                        anchor: 'end',
                        align: 'end',
                        offset: 4,
                        color: '#4b5563',
                        font: {
                            size: 11,
                            weight: 'bold',
                            family: 'system-ui, -apple-system, sans-serif'
                        },
                        formatter: (value) => {
                            return new Intl.NumberFormat('en-IN', { 
                                style: 'currency', 
                                currency: 'INR', 
                                maximumFractionDigits: 0 
                            }).format(value);
                        }
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true, 
                        grid: { color: '#f5f5f5' },
                        ticks: { callback: (val) => val.toLocaleString('en-IN') }
                    },
                    y: { 
                        grid: { display: false }, 
                        ticks: { font: { weight: 'bold', size: 12 } } 
                    }
                }
            }
        });
        chartInstances.push(payerInstance);
    }
});

// ============================================
// CLEANUP ON PAGE UNLOAD
// ============================================
window.addEventListener('beforeunload', function() {
    chartInstances.forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    chartInstances = [];
});