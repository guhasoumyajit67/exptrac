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
// DELETE BUTTON CONFIRMATION HANDLER
// ============================================
document.addEventListener('click', function(e) {
    const deleteBtn = e.target.closest('#modalDeleteBtn');
    if (deleteBtn) {
        if (!confirm('Are you sure you want to permanently delete this record?')) {
            e.preventDefault();
            return false;
        }
    }
});

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

    // Make updateUIState globally accessible
    window.updateUIState = updateUIState;

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
        const cells = row.querySelectorAll('td');
        cells.forEach(cell => {
            const text = cell.textContent;
            if (text.toLowerCase().includes(term)) {
                const regex = new RegExp(`(${term})`, 'gi');
                cell.innerHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');
            }
        });
    }

    function removeHighlight(row) {
        const cells = row.querySelectorAll('td');
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
                submitFilterForm(true);
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

        const now = new Date();
        let startDate = null;
        let endDate = null;
        let label = '';

        if (period !== 'all') {
            const labels = {
                '1w': 'Last 7 Days',
                '1m': 'Last 30 Days',
                '3m': 'Last 90 Days',
                '1y': 'Last 365 Days'
            };
            label = labels[period] || period;
            activeFilterIndicator.classList.remove('d-none');
            activeFilterLabel.textContent = label;
            
            const today = new Date();
            if (period === '1w') {
                startDate = new Date(today);
                startDate.setDate(today.getDate() - 7);
            } else if (period === '1m') {
                startDate = new Date(today);
                startDate.setMonth(today.getMonth() - 1);
            } else if (period === '3m') {
                startDate = new Date(today);
                startDate.setMonth(today.getMonth() - 3);
            } else if (period === '1y') {
                startDate = new Date(today);
                startDate.setFullYear(today.getFullYear() - 1);
            }
            endDate = new Date(today);
            
            const formatDate = (date) => {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${year}-${month}-${day}`;
            };
            
            if (dateStartInput) {
                dateStartInput.value = formatDate(startDate);
                const hiddenDateFrom = document.getElementById('hiddenDateFrom');
                if (hiddenDateFrom) hiddenDateFrom.value = formatDate(startDate);
            }
            if (dateEndInput) {
                dateEndInput.value = formatDate(endDate);
                const hiddenDateTo = document.getElementById('hiddenDateTo');
                if (hiddenDateTo) hiddenDateTo.value = formatDate(endDate);
            }
            
        } else {
            activeFilterIndicator.classList.add('d-none');
            if (dateStartInput) dateStartInput.value = '';
            if (dateEndInput) dateEndInput.value = '';
            const hiddenDateFrom = document.getElementById('hiddenDateFrom');
            const hiddenDateTo = document.getElementById('hiddenDateTo');
            if (hiddenDateFrom) hiddenDateFrom.value = '';
            if (hiddenDateTo) hiddenDateTo.value = '';
        }

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
        
        const params = new URLSearchParams();
        
        const dateFrom = dateStartInput ? dateStartInput.value : '';
        const dateTo = dateEndInput ? dateEndInput.value : '';
        const period = document.getElementById('hiddenPeriod')?.value || 'all';
        const search = document.getElementById('hiddenSearch')?.value || '';
        
        if (dateFrom) params.set('date_from', dateFrom);
        if (dateTo) params.set('date_to', dateTo);
        if (period && period !== 'all') params.set('period', period);
        if (search) params.set('search', search);
        
        params.set('page', '1');
        
        const url = window.location.pathname + '?' + params.toString();
        window.location.href = url;
    }

    // ============================================
    // 5. EXPORT FUNCTIONALITY - SERVER SIDE
    // ============================================
    window.exportData = function(format) {
        const loadingOverlay = document.getElementById('delete-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('active');
            loadingOverlay.querySelector('h5').textContent = 'Preparing export...';
            loadingOverlay.querySelector('p').textContent = `Generating ${format.toUpperCase()} file. Please wait...`;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const params = new URLSearchParams();
        
        const period = urlParams.get('period') || document.getElementById('hiddenPeriod')?.value || 'all';
        const search = urlParams.get('search') || document.getElementById('hiddenSearch')?.value || '';
        const dateFrom = urlParams.get('date_from') || document.getElementById('hiddenDateFrom')?.value || '';
        const dateTo = urlParams.get('date_to') || document.getElementById('hiddenDateTo')?.value || '';
        const category = urlParams.get('category') || '';
        const payer = urlParams.get('payer') || '';
        
        if (period && period !== 'all') params.set('period', period);
        if (search) params.set('search', search);
        if (dateFrom) params.set('date_from', dateFrom);
        if (dateTo) params.set('date_to', dateTo);
        if (category) params.set('category', category);
        if (payer) params.set('payer', payer);
        
        params.set('format', format);

        fetch(`/transaction/export/?${params.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Export failed');
            }
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            const extension = format === 'csv' ? 'csv' : format === 'excel' ? 'xlsx' : 'pdf';
            link.download = `transactions_${new Date().toISOString().split('T')[0]}.${extension}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            if (loadingOverlay) {
                loadingOverlay.classList.remove('active');
            }
        })
        .catch(error => {
            console.error('Export error:', error);
            alert('Failed to export data. Please try again.');
            if (loadingOverlay) {
                loadingOverlay.classList.remove('active');
            }
        });
    };

    // ============================================
    // 6. EXCEL FILTER ENGINE
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
    // 7. SORTING
    // ============================================
    document.querySelectorAll(".sortable-header").forEach(header => {
        header.addEventListener("click", function(e) {
            if (e.target.closest('.excel-filter-menu') || e.target.classList.contains('excel-filter-icon')) return;
            
            const colIndex = parseInt(this.getAttribute("data-column"));
            if (currentSortColumn === colIndex) {
                isAscending = !isAscending;
            } else {
                currentSortColumn = colIndex;
                isAscending = true;
            }

            syncSortIcons(this.querySelector("i"), isAscending);
            sortColumn(colIndex, isAscending);
        });
    });

    function syncSortIcons(activeIcon, asc) {
        document.querySelectorAll(".sortable-header i").forEach(icon => {
            icon.className = "bi bi-arrow-down-up text-muted extra-small";
        });
        if (activeIcon) {
            activeIcon.className = asc ? "bi bi-arrow-up text-primary extra-small" : "bi bi-arrow-down text-primary extra-small";
        }
    }

    function sortColumn(index, asc) {
        const sortedRows = rows.sort((a, b) => {
            const cellA = a.children[index];
            const cellB = b.children[index];

            let valA = cellA.getAttribute("data-sort-val") || cellA.innerText.trim();
            let valB = cellB.getAttribute("data-sort-val") || cellB.innerText.trim();

            const numA = parseFloat(valA.replace(/[₹,\s]/g, ''));
            const numB = parseFloat(valB.replace(/[₹,\s]/g, ''));

            if (!isNaN(numA) && !isNaN(numB)) {
                return asc ? numA - numB : numB - numA;
            }
            return asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        });

        sortedRows.forEach(row => tableBody.appendChild(row));
        if(noMatchesRow) tableBody.appendChild(noMatchesRow); 
    }

    // ============================================
    // 8. DATE RANGE HANDLERS
    // ============================================
    if (dateStartInput) {
        dateStartInput.addEventListener('change', function() {
            const hiddenDateFrom = document.getElementById('hiddenDateFrom');
            if (hiddenDateFrom) {
                hiddenDateFrom.value = this.value;
            }
            const hiddenPeriod = document.getElementById('hiddenPeriod');
            if (hiddenPeriod && this.value) {
                hiddenPeriod.value = 'all';
                quickFilterBtns.forEach(btn => {
                    btn.classList.remove('active', 'btn-primary');
                    btn.classList.add('btn-outline-secondary');
                });
                activeFilterIndicator.classList.add('d-none');
            }
            submitFilterForm(true);
        });
    }
    
    if (dateEndInput) {
        dateEndInput.addEventListener('change', function() {
            const hiddenDateTo = document.getElementById('hiddenDateTo');
            if (hiddenDateTo) {
                hiddenDateTo.value = this.value;
            }
            submitFilterForm(true);
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
            
            submitFilterForm(true);
        });
    }

    // ============================================
    // 9. SELECT ALL & CLEAR SELECTION
    // ============================================
    
    // Select All button
    const selectAllBtn = document.getElementById('select-all-btn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const visibleRows = document.querySelectorAll('.ledger-row:not([style*="display: none"])');
            const allSelected = Array.from(visibleRows).every(row => row.classList.contains('row-selected'));
            
            visibleRows.forEach(row => {
                if (allSelected) {
                    row.classList.remove('row-selected');
                } else {
                    row.classList.add('row-selected');
                }
            });
            
            updateUIState();
        });
    }

    // Clear Selection button
    const clearSelectionBtn = document.getElementById('clear-selection-btn');
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            document.querySelectorAll('.row-selected').forEach(row => {
                row.classList.remove('row-selected');
            });
            
            updateUIState();
        });
    }

    // ============================================
    // 10. ROW SELECTION - SINGLE CLICK
    // ============================================
    
    const allRows = document.querySelectorAll('.ledger-row');
    allRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Ignore clicks on buttons, links, or interactive elements inside the row
            if (e.target.closest('button') || e.target.closest('a') || e.target.closest('.no-bubble') || e.target.closest('.dropdown')) {
                return;
            }
            
            // Toggle selection
            this.classList.toggle('row-selected');
            
            // Update bulk actions visibility
            const selectedRows = document.querySelectorAll('.row-selected');
            const actionsBar = document.getElementById('bulk-delete-actions');
            if (selectedRows.length >= 1) {
                actionsBar.classList.add('show-actions');
            } else {
                actionsBar.classList.remove('show-actions');
            }
        });
    });

    // ============================================
    // 11. KEYBOARD SHORTCUTS
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
    // 12. INITIALIZATION
    // ============================================
    populateFilterMenus();

    // ============================================
    // 13. SEARCH HIGHLIGHT STYLES
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
    // 14. RESTORE FILTER STATES FROM URL
    // ============================================
    function restoreFilterStates() {
        const urlParams = new URLSearchParams(window.location.search);
        
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
            
            // Calculate and set date range
            const today = new Date();
            let startDate = null;
            if (period === '1w') {
                startDate = new Date(today);
                startDate.setDate(today.getDate() - 7);
            } else if (period === '1m') {
                startDate = new Date(today);
                startDate.setMonth(today.getMonth() - 1);
            } else if (period === '3m') {
                startDate = new Date(today);
                startDate.setMonth(today.getMonth() - 3);
            } else if (period === '1y') {
                startDate = new Date(today);
                startDate.setFullYear(today.getFullYear() - 1);
            }
            
            if (startDate) {
                const formatDate = (date) => {
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const day = String(date.getDate()).padStart(2, '0');
                    return `${year}-${month}-${day}`;
                };
                if (dateStartInput) {
                    dateStartInput.value = formatDate(startDate);
                }
                if (dateEndInput) {
                    dateEndInput.value = formatDate(today);
                }
            }
            
        } else {
            const dateFrom = urlParams.get('date_from');
            const dateTo = urlParams.get('date_to');
            if (dateFrom && dateStartInput) dateStartInput.value = dateFrom;
            if (dateTo && dateEndInput) dateEndInput.value = dateTo;
        }
        
        const search = urlParams.get('search');
        if (search && searchInput) {
            searchInput.value = search;
            const hiddenSearch = document.getElementById('hiddenSearch');
            if (hiddenSearch) hiddenSearch.value = search;
            
            if (searchResultInfo) {
                searchResultInfo.classList.remove('d-none');
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
// 15. BATCH DELETION LOADER ENGINE
// ============================================
document.addEventListener("DOMContentLoaded", function() {
    const bulkDeleteForm = document.getElementById("bulk-delete-form");
    const processingLoader = document.getElementById("delete-loading-overlay");
    let isSubmitting = false;

    if (bulkDeleteForm && processingLoader) {
        bulkDeleteForm.addEventListener("submit", function (event) {
            if (isSubmitting) {
                event.preventDefault();
                return;
            }
            
            const selectedRows = document.querySelectorAll('.row-selected');
            if (selectedRows.length === 0) {
                event.preventDefault();
                alert('Please select at least one row to delete.');
                return;
            }
            
            const userConfirmed = confirm(`Are you sure you want to permanently delete ${selectedRows.length} selected transaction(s)?`);
            if (userConfirmed) {
                isSubmitting = true;
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