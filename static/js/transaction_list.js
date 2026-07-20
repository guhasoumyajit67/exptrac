// ============================================
// TRANSACTION LEDGER - COMPLETE JAVASCRIPT
// ============================================

function showRowActions(id, itemName, price) {
    document.getElementById('modalTargetSublabel').textContent = itemName + " (₹" + price + ")";
    
    const editUrlPattern = window.transactionUrls.update || "{% url 'update_transaction' 0 %}";
    let deleteUrlPattern = window.transactionUrls.delete || "{% url 'delete_transaction' 0 %}";
    
    const editUrl = editUrlPattern.replace('0', id);
    let deleteUrl = deleteUrlPattern.replace('0', id);
    
    const currentPath = encodeURIComponent(window.location.pathname);
    deleteUrl = `${deleteUrl}?next=${currentPath}`;
    
    document.getElementById('modalEditBtn').href = editUrl;
    document.getElementById('modalDeleteBtn').href = deleteUrl;
    
    const actionModal = new bootstrap.Modal(document.getElementById('rowActionModal'));
    actionModal.show();
}

window.showRowActions = showRowActions;

// ============================================
// MAIN - DOM READY
// ============================================
document.addEventListener("DOMContentLoaded", function() {
    const tableBody = document.querySelector('tbody');
    const tableWrapper = document.getElementById('ledger-table-wrapper');
    const actionsBar = document.getElementById('bulk-delete-actions');
    const table = document.getElementById("ledgerTable");
    const rows = Array.from(tableBody ? tableBody.querySelectorAll(".ledger-row") : []);
    const noMatchesRow = document.getElementById('excelNoMatchesRow');

    const dateStartInput = document.getElementById('dateFilterStart');
    const dateEndInput = document.getElementById('dateFilterEnd');
    const clearDateBtn = document.getElementById('clearDateRangeBtn');

    let lastFocusedRow = null;
    let unselectedFilters = { category: [], payer: [] };
    let currentSortColumn = -1;
    let isAscending = true;

    // ============================================
    // 1. UPDATE UI STATE FUNCTION
    // ============================================
    function updateUIState() {
        const selectedRows = document.querySelectorAll('.row-selected');
        const checkedCount = selectedRows.length;
        const actionsBar = document.getElementById('bulk-delete-actions');

        if (checkedCount >= 1) {
            actionsBar.classList.add('show-actions');
        } else {
            actionsBar.classList.remove('show-actions');
        }
    }

    // ============================================
    // 2. SEARCH FUNCTIONALITY
    // ============================================
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const searchResultInfo = document.getElementById('searchResultInfo');
    const resultCount = document.getElementById('resultCount');
    let searchTerm = '';
    let activePeriod = 'all';
    let debounceTimer;
    let isApplyingFilter = false;

    function performSearch() {
        const term = searchInput.value.toLowerCase().trim();
        searchTerm = term;
        let visibleCount = 0;

        rows.forEach(row => {
            if (row.style.display === 'none') return;

            const text = row.textContent.toLowerCase();
            const matches = term === '' || text.includes(term);
            
            if (matches) {
                row.style.display = '';
                visibleCount++;
                if (term !== '') {
                    highlightText(row, term);
                } else {
                    removeHighlight(row);
                }
            } else {
                row.style.display = 'none';
            }
        });

        if (term !== '') {
            searchResultInfo.classList.remove('d-none');
            resultCount.textContent = visibleCount;
            clearSearchBtn.style.display = 'block';
        } else {
            searchResultInfo.classList.add('d-none');
            clearSearchBtn.style.display = 'none';
        }

        if (visibleCount === 0 && rows.length > 0) {
            noMatchesRow.classList.remove('d-none');
        } else {
            noMatchesRow.classList.add('d-none');
        }
        
        updateUIState();
    }

    function highlightText(row, term) {
        const cells = row.querySelectorAll('td:not(:first-child)');
        cells.forEach(cell => {
            const text = cell.textContent;
            if (text.toLowerCase().includes(term)) {
                const regex = new RegExp(`(${term})`, 'gi');
                cell.innerHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');
            }
        });
    }

    function removeHighlight(row) {
        const cells = row.querySelectorAll('td:not(:first-child)');
        cells.forEach(cell => {
            cell.innerHTML = cell.textContent;
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                const hiddenSearch = document.getElementById('hiddenSearch');
                if (hiddenSearch) {
                    hiddenSearch.value = this.value.trim();
                }
                submitFilterForm(true); // Reset to page 1
            }, 500);
        });

        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                const hiddenSearch = document.getElementById('hiddenSearch');
                if (hiddenSearch) {
                    hiddenSearch.value = '';
                }
                submitFilterForm(true);
                this.blur();
            }
            if (e.key === 'Enter') {
                e.preventDefault();
                const hiddenSearch = document.getElementById('hiddenSearch');
                if (hiddenSearch) {
                    hiddenSearch.value = this.value.trim();
                }
                submitFilterForm(true);
            }
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            searchInput.value = '';
            const hiddenSearch = document.getElementById('hiddenSearch');
            if (hiddenSearch) {
                hiddenSearch.value = '';
            }
            submitFilterForm(true);
            searchInput.focus();
        });
    }

    // ============================================
    // 3. QUICK FILTER FUNCTIONALITY
    // ============================================
    const quickFilterBtns = document.querySelectorAll('.quick-filter-btn');
    const activeFilterIndicator = document.getElementById('activeFilterIndicator');
    const activeFilterLabel = document.getElementById('activeFilterLabel');

    function applyQuickFilter(period) {
        activePeriod = period;
        
        // Update hidden period input
        const hiddenPeriod = document.getElementById('hiddenPeriod');
        if (hiddenPeriod) {
            hiddenPeriod.value = period;
        }

        quickFilterBtns.forEach(btn => {
            btn.classList.remove('active', 'btn-primary');
            btn.classList.add('btn-outline-secondary');
            if (btn.dataset.period === period) {
                btn.classList.remove('btn-outline-secondary');
                btn.classList.add('btn-primary', 'active');
            }
        });

        if (period !== 'all') {
            const labels = {
                '1w': 'Last 7 Days',
                '1m': 'Last 30 Days',
                '3m': 'Last 90 Days',
                '1y': 'Last 365 Days'
            };
            activeFilterIndicator.classList.remove('d-none');
            activeFilterLabel.textContent = labels[period] || period;
            
            // Clear date inputs when quick filter is applied
            if (dateStartInput) dateStartInput.value = '';
            if (dateEndInput) dateEndInput.value = '';
            
            // Clear hidden date inputs
            const hiddenDateFrom = document.getElementById('hiddenDateFrom');
            const hiddenDateTo = document.getElementById('hiddenDateTo');
            if (hiddenDateFrom) hiddenDateFrom.value = '';
            if (hiddenDateTo) hiddenDateTo.value = '';
        } else {
            activeFilterIndicator.classList.add('d-none');
        }

        // Submit the filter form - reset to page 1
        submitFilterForm(true);
    }

    quickFilterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const period = this.dataset.period;
            applyQuickFilter(period);
        });
    });

    // ============================================
    // 4. FILTER FORM SUBMISSION
    // ============================================
    function submitFilterForm(resetPage = false) {
        if (isApplyingFilter) return;
        isApplyingFilter = true;
        
        // Build URL with query parameters
        const params = new URLSearchParams();
        
        // Get date values
        const dateFrom = dateStartInput ? dateStartInput.value : '';
        const dateTo = dateEndInput ? dateEndInput.value : '';
        const period = document.getElementById('hiddenPeriod')?.value || 'all';
        const search = document.getElementById('hiddenSearch')?.value || '';
        
        if (dateFrom) params.set('date_from', dateFrom);
        if (dateTo) params.set('date_to', dateTo);
        if (period && period !== 'all') params.set('period', period);
        if (search) params.set('search', search);
        
        // Always reset to page 1 when filtering
        params.set('page', '1');
        
        // Navigate to filtered URL
        const url = window.location.pathname + '?' + params.toString();
        window.location.href = url;
    }

    // ============================================
    // 5. EXPORT FUNCTIONALITY
    // ============================================
    window.exportData = function(format) {
        const rows = document.querySelectorAll('#ledgerTable tbody tr:not(.empty-row):not(.d-none)');
        
        if (rows.length === 0) {
            alert('No transactions to export. Please adjust your filters.');
            return;
        }

        const headers = ['Date', 'Category', 'Item', 'Price (₹)', 'Quantity', 'Paid By', 'Comment'];
        const data = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 7) {
                const rowData = {
                    date: cells[1]?.textContent.trim() || '',
                    category: cells[2]?.textContent.trim().replace('●', '').trim() || '',
                    item: cells[3]?.textContent.trim() || '',
                    price: cells[4]?.textContent.trim().replace('₹', '').trim() || '',
                    quantity: cells[5]?.textContent.trim() || '',
                    payer: cells[6]?.textContent.trim() || '',
                    comment: cells[7]?.textContent.trim() || ''
                };
                data.push(rowData);
            }
        });

        switch(format) {
            case 'csv':
                exportCSV(headers, data);
                break;
            case 'excel':
                exportExcel(headers, data);
                break;
            case 'pdf':
                exportPDF(headers, data);
                break;
            case 'print':
                window.print();
                break;
            default:
                alert('Export format not supported');
        }
    };

    function exportCSV(headers, data) {
        let csv = headers.join(',') + '\n';
        data.forEach(row => {
            csv += Object.values(row).join(',') + '\n';
        });

        const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    function exportExcel(headers, data) {
        if (typeof XLSX === 'undefined') {
            alert('Excel export library not loaded. Please refresh the page.');
            return;
        }

        const wsData = [headers];
        data.forEach(row => {
            wsData.push(Object.values(row));
        });

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(wsData);
        XLSX.utils.book_append_sheet(wb, ws, 'Transactions');
        XLSX.writeFile(wb, `transactions_${new Date().toISOString().split('T')[0]}.xlsx`);
    }

    function exportPDF(headers, data) {
        if (typeof html2pdf === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
            script.onload = function() {
                generatePDF(headers, data);
            };
            document.head.appendChild(script);
        } else {
            generatePDF(headers, data);
        }
    }

    function generatePDF(headers, data) {
        const tempDiv = document.createElement('div');
        tempDiv.style.padding = '20px';
        tempDiv.style.fontFamily = 'Arial, sans-serif';
        
        let html = `<h1>Transaction Report</h1>
                    <p>Generated: ${new Date().toLocaleString()}</p>
                    <p>Total: ${data.length} transactions</p>
                    <table style="width:100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background: #0d6efd; color: white;">`;
        
        headers.forEach(h => {
            html += `<th style="padding: 10px; border: 1px solid #ddd; text-align: left;">${h}</th>`;
        });
        
        html += `</tr></thead><tbody>`;
        
        data.forEach(row => {
            html += `<tr>`;
            Object.values(row).forEach(val => {
                html += `<td style="padding: 8px; border: 1px solid #ddd;">${val}</td>`;
            });
            html += `</tr>`;
        });
        
        html += `</tbody></table>`;
        html += `<p style="margin-top: 20px; color: #666; font-size: 12px;">Generated by ExpTrac</p>`;
        tempDiv.innerHTML = html;
        document.body.appendChild(tempDiv);

        html2pdf()
            .set({
                margin: [15, 15],
                filename: `transactions_${new Date().toISOString().split('T')[0]}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
            })
            .from(tempDiv)
            .save()
            .then(() => {
                document.body.removeChild(tempDiv);
            });
    }

    // ============================================
    // 6. EXCEL FILTER ENGINE (Client-side fallback)
    // ============================================
    function populateFilterMenus() {
        const uniqueCategories = new Set();
        const uniquePayers = new Set();

        rows.forEach(row => {
            const catCell = row.querySelector(".excel-cat-cell");
            const payerCell = row.querySelector(".excel-payer-cell");
            
            if (catCell) uniqueCategories.add(catCell.getAttribute("data-filter-val").trim());
            if (payerCell) uniquePayers.add(payerCell.getAttribute("data-filter-val").trim());
        });

        buildMenuOptions("categoryFilterMenu", Array.from(uniqueCategories), "category");
        buildMenuOptions("payerFilterMenu", Array.from(uniquePayers), "payer");
    }

    function buildMenuOptions(menuId, optionList, filterKey) {
        const menuEl = document.getElementById(menuId);
        if (!menuEl) return;
        const container = menuEl.querySelector('.filter-options-container');
        const masterCheckbox = menuEl.querySelector('.master-filter-checkbox');
        if (!container) return;
        
        container.innerHTML = "";
        let isUpdatingMaster = false;

        optionList.sort().forEach(optionText => {
            if (!optionText) return;
            const div = document.createElement("div");
            div.className = "form-check py-1 px-2 filter-option-item rounded-2 m-0 small d-flex align-items-center";
            div.innerHTML = `
                <input class="form-check-input ms-0 me-2 cursor-pointer sub-checkbox" type="checkbox" value="${optionText}" checked id="chk_${filterKey}_${optionText}">
                <label class="form-check-label text-dark cursor-pointer small w-100 ps-1" for="chk_${filterKey}_${optionText}">${optionText}</label>
            `;
            
            div.querySelector("input").addEventListener("change", function() {
                if (this.checked) {
                    unselectedFilters[filterKey] = unselectedFilters[filterKey].filter(v => v !== this.value);
                } else {
                    if (!unselectedFilters[filterKey].includes(this.value)) {
                        unselectedFilters[filterKey].push(this.value);
                    }
                }
                
                if (!isUpdatingMaster && masterCheckbox) {
                    const totalSubs = container.querySelectorAll('.sub-checkbox').length;
                    const checkedSubs = container.querySelectorAll('.sub-checkbox:checked').length;
                    
                    masterCheckbox.checked = (totalSubs === checkedSubs);
                    masterCheckbox.indeterminate = (checkedSubs > 0 && checkedSubs < totalSubs);
                }
                
                // For category/payer filters, we use server-side
                // Just update the UI state
                updateUIState();
            });
            container.appendChild(div);
        });

        if (masterCheckbox) {
            masterCheckbox.addEventListener('change', function() {
                isUpdatingMaster = true;
                const checkboxes = container.querySelectorAll('.sub-checkbox');
                checkboxes.forEach(cb => {
                    if (cb.checked !== this.checked) {
                        cb.checked = this.checked;
                        cb.dispatchEvent(new Event('change'));
                    }
                });
                this.indeterminate = false;
                isUpdatingMaster = false;
            });
        }
    }

    window.toggleExcelFilter = function(event, menuId) {
        event.stopPropagation();
        document.querySelectorAll(".excel-filter-menu").forEach(m => {
            if(m.id !== menuId) m.classList.add("d-none");
        });
        document.getElementById(menuId).classList.toggle("d-none");
    };

    document.addEventListener("click", function(e) {
        if (!e.target.closest(".filterable-header")) {
            document.querySelectorAll(".excel-filter-menu").forEach(m => m.classList.add("d-none"));
        }
    });

    // ============================================
    // 7. DATE RANGE HANDLERS
    // ============================================
    if (dateStartInput) {
        dateStartInput.addEventListener('change', function() {
            const hiddenDateFrom = document.getElementById('hiddenDateFrom');
            if (hiddenDateFrom) {
                hiddenDateFrom.value = this.value;
            }
            // Clear quick filter indicator when date range is manually set
            const hiddenPeriod = document.getElementById('hiddenPeriod');
            if (hiddenPeriod && this.value) {
                hiddenPeriod.value = 'all';
                quickFilterBtns.forEach(btn => {
                    btn.classList.remove('active', 'btn-primary');
                    btn.classList.add('btn-outline-secondary');
                });
                activeFilterIndicator.classList.add('d-none');
            }
            submitFilterForm(true); // Reset to page 1
        });
    }
    
    if (dateEndInput) {
        dateEndInput.addEventListener('change', function() {
            const hiddenDateTo = document.getElementById('hiddenDateTo');
            if (hiddenDateTo) {
                hiddenDateTo.value = this.value;
            }
            submitFilterForm(true); // Reset to page 1
        });
    }
    
    if (clearDateBtn) {
        clearDateBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            if (dateStartInput) dateStartInput.value = "";
            if (dateEndInput) dateEndInput.value = "";
            
            const hiddenDateFrom = document.getElementById('hiddenDateFrom');
            const hiddenDateTo = document.getElementById('hiddenDateTo');
            if (hiddenDateFrom) hiddenDateFrom.value = '';
            if (hiddenDateTo) hiddenDateTo.value = '';
            
            submitFilterForm(true); // Reset to page 1
        });
    }

    // ============================================
    // 8. SELECT ALL FUNCTIONALITY
    // ============================================
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const checkboxes = document.querySelectorAll('.transaction-checkbox');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            checkboxes.forEach(cb => {
                const row = cb.closest('.ledger-row');
                if (row && row.style.display !== 'none') {
                    cb.checked = isChecked;
                    if (isChecked) {
                        row.classList.add('row-selected');
                    } else {
                        row.classList.remove('row-selected');
                    }
                }
            });
            updateUIState();
        });
    }

    // Individual checkbox change
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            const row = this.closest('.ledger-row');
            if (this.checked) {
                row.classList.add('row-selected');
            } else {
                row.classList.remove('row-selected');
            }
            updateUIState();
        });
    });

    // Select All button (icon)
    const selectAllBtn = document.getElementById('select-all-btn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const allCheckboxes = document.querySelectorAll('.transaction-checkbox');
            const allChecked = Array.from(allCheckboxes).every(cb => cb.checked);
            
            allCheckboxes.forEach(cb => {
                const row = cb.closest('.ledger-row');
                if (row && row.style.display !== 'none') {
                    cb.checked = !allChecked;
                    if (cb.checked) {
                        row.classList.add('row-selected');
                    } else {
                        row.classList.remove('row-selected');
                    }
                }
            });
            
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = !allChecked;
            }
            updateUIState();
        });
    }

    // ============================================
    // 9. CLEAR SELECTION
    // ============================================
    const clearSelectionBtn = document.getElementById('clear-selection-btn');
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            checkboxes.forEach(cb => {
                cb.checked = false;
                const row = cb.closest('.ledger-row');
                if (row) row.classList.remove('row-selected');
            });
            
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
            }
            updateUIState();
        });
    }

    // ============================================
    // 10. KEYBOARD SHORTCUTS
    // ============================================
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            document.querySelector('.dropdown-toggle')?.click();
        }
    });

    // ============================================
    // 11. INITIALIZATION
    // ============================================
    populateFilterMenus();

    // ============================================
    // 12. SEARCH HIGHLIGHT STYLES
    // ============================================
    const highlightStyle = document.createElement('style');
    highlightStyle.textContent = `
        .search-highlight {
            background: #ffeb3b !important;
            padding: 0 2px !important;
            border-radius: 2px !important;
            color: #000 !important;
            font-weight: 600 !important;
        }
        .quick-filter-btn.active {
            background: #0d6efd !important;
            color: white !important;
            border-color: #0d6efd !important;
        }
        .quick-filter-btn:hover {
            transform: scale(1.05);
            transition: transform 0.15s ease;
        }
        #searchInput:focus {
            border-color: #0d6efd !important;
            box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15) !important;
            background: white !important;
        }
        @media print {
            .navbar, .btn, .no-print, #bulk-delete-actions, 
            .pagination, footer, .search-section, .filter-section {
                display: none !important;
            }
            body { background: white !important; }
            .card { box-shadow: none !important; border: 1px solid #ddd !important; }
            table { font-size: 10px !important; }
            .badge { background: transparent !important; border: 1px solid #ddd !important; }
        }
    `;
    document.head.appendChild(highlightStyle);

    // ============================================
    // 13. RESTORE FILTER STATES FROM URL
    // ============================================
    function restoreFilterStates() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Restore period
        const period = urlParams.get('period');
        if (period && period !== 'all') {
            activePeriod = period;
            const hiddenPeriod = document.getElementById('hiddenPeriod');
            if (hiddenPeriod) hiddenPeriod.value = period;
            
            quickFilterBtns.forEach(btn => {
                btn.classList.remove('active', 'btn-primary');
                btn.classList.add('btn-outline-secondary');
                if (btn.dataset.period === period) {
                    btn.classList.remove('btn-outline-secondary');
                    btn.classList.add('btn-primary', 'active');
                }
            });
            
            const labels = {
                '1w': 'Last 7 Days',
                '1m': 'Last 30 Days',
                '3m': 'Last 90 Days',
                '1y': 'Last 365 Days'
            };
            activeFilterIndicator.classList.remove('d-none');
            activeFilterLabel.textContent = labels[period] || period;
            
            // Clear date inputs when period is active
            if (dateStartInput) dateStartInput.value = '';
            if (dateEndInput) dateEndInput.value = '';
        } else {
            // Restore date range
            const dateFrom = urlParams.get('date_from');
            const dateTo = urlParams.get('date_to');
            if (dateFrom && dateStartInput) dateStartInput.value = dateFrom;
            if (dateTo && dateEndInput) dateEndInput.value = dateTo;
        }
        
        // Restore search
        const search = urlParams.get('search');
        if (search && searchInput) {
            searchInput.value = search;
            const hiddenSearch = document.getElementById('hiddenSearch');
            if (hiddenSearch) hiddenSearch.value = search;
            
            // Show search results info
            if (searchResultInfo) {
                searchResultInfo.classList.remove('d-none');
                // Get the count from the page
                const countElement = document.querySelector('.pagination');
                if (countElement) {
                    const totalItems = document.querySelector('tbody tr:not(.empty-row)')?.length || 0;
                    resultCount.textContent = totalItems;
                }
            }
            if (clearSearchBtn) clearSearchBtn.style.display = 'block';
        }
    }
    
    restoreFilterStates();
});

// ============================================
// 14. BATCH DELETION LOADER ENGINE
// ============================================
document.addEventListener("DOMContentLoaded", function() {
    const bulkDeleteForm = document.getElementById("bulk-delete-form");
    const processingLoader = document.getElementById("delete-loading-overlay");

    if (bulkDeleteForm && processingLoader) {
        bulkDeleteForm.addEventListener("submit", function (event) {
            const selectedRows = document.querySelectorAll('.row-selected');
            if (selectedRows.length === 0) {
                event.preventDefault();
                alert('Please select at least one row to delete.');
                return;
            }
            
            const userConfirmed = confirm(`Are you sure you want to permanently delete ${selectedRows.length} selected transaction(s)?`);
            if (userConfirmed) {
                // Remove any existing hidden inputs to avoid duplicates
                const existingInputs = document.querySelectorAll('#bulk-delete-form input[name="transaction_ids"]');
                existingInputs.forEach(input => input.remove());
                
                selectedRows.forEach(row => {
                    const id = row.dataset.transactionId;
                    if (id) {
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = 'transaction_ids';
                        input.value = id;
                        document.getElementById('bulk-delete-form').appendChild(input);
                    }
                });
                processingLoader.classList.add('active');
            } else {
                event.preventDefault();
            }
        });
    }
});