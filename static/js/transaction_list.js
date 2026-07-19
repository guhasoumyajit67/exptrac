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
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    const clearSelectionBtn = document.getElementById('clear-selection-btn');
    const table = document.getElementById("ledgerTable");
    const rows = Array.from(tableBody.querySelectorAll(".ledger-row"));
    const noMatchesRow = document.getElementById('excelNoMatchesRow');

    const dateStartInput = document.getElementById('dateFilterStart');
    const dateEndInput = document.getElementById('dateFilterEnd');
    const clearDateBtn = document.getElementById('clearDateRangeBtn');

    let lastFocusedRow = null;
    let unselectedFilters = { category: [], payer: [] };
    let currentSortColumn = -1;
    let isAscending = true;

    // ===================================================
    // 1. DYNAMIC EXCEL FILTERING ENGINE (WITH DATE RANGE)
    // ===================================================
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
                
                applyExcelFilters();
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

    function applyExcelFilters() {
        let visibleRows = 0;

        const startDateVal = dateStartInput && dateStartInput.value ? new Date(dateStartInput.value) : null;
        const endDateVal = dateEndInput && dateEndInput.value ? new Date(dateEndInput.value) : null;

        if (startDateVal) startDateVal.setHours(0,0,0,0);
        if (endDateVal) endDateVal.setHours(23,59,59,999);

        rows.forEach(row => {
            const catVal = row.querySelector(".excel-cat-cell")?.getAttribute("data-filter-val")?.trim();
            const payerVal = row.querySelector(".excel-payer-cell")?.getAttribute("data-filter-val")?.trim();

            const dateCell = row.querySelector("[data-sort-val]");
            let rowDate = null;
            if (dateCell) {
                const rawDateStr = dateCell.getAttribute("data-sort-val");
                if (rawDateStr && rawDateStr.length === 8) {
                    const yr = parseInt(rawDateStr.substring(0, 4));
                    const mo = parseInt(rawDateStr.substring(4, 6)) - 1;
                    const dy = parseInt(rawDateStr.substring(6, 8));
                    rowDate = new Date(yr, mo, dy);
                }
            }

            const blockCat = unselectedFilters.category.includes(catVal);
            const blockPayer = unselectedFilters.payer.includes(payerVal);
            
            let blockDate = false;
            if (rowDate) {
                if (startDateVal && rowDate < startDateVal) blockDate = true;
                if (endDateVal && rowDate > endDateVal) blockDate = true;
            }

            if (blockCat || blockPayer || blockDate) {
                row.style.display = "none";
                row.classList.remove('row-selected');
            } else {
                row.style.display = "";
                visibleRows++;
            }
        });

        if (visibleRows === 0 && rows.length > 0) {
            noMatchesRow.classList.remove('d-none');
        } else {
            noMatchesRow.classList.add('d-none');
        }
        updateUIState();
    }

    if (dateStartInput) dateStartInput.addEventListener('change', applyExcelFilters);
    if (dateEndInput) dateEndInput.addEventListener('change', applyExcelFilters);
    if (clearDateBtn) {
        clearDateBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            if (dateStartInput) dateStartInput.value = "";
            if (dateEndInput) dateEndInput.value = "";
            applyExcelFilters();
        });
    }

    // ===================================================
    // 2. EXCEL COLUMN SORT ENGINE & MENU TRIGGERS
    // ===================================================
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

    document.querySelectorAll(".menu-sort-trigger").forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.stopPropagation();
            const colIndex = parseInt(this.getAttribute("data-column"));
            const order = this.getAttribute("data-order");
            
            isAscending = (order === "asc");
            currentSortColumn = colIndex;

            const nativeHeaderIcon = table.querySelector(`.sortable-header[data-column="${colIndex}"] i`);
            syncSortIcons(nativeHeaderIcon, isAscending);
            
            sortColumn(colIndex, isAscending);
            document.querySelectorAll(".excel-filter-menu").forEach(m => m.classList.add("d-none"));
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

    // ===================================================
    // 3. KEYBOARD SHORTCUTS & SELECTIONS OPERATORS
    // ===================================================
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function(e) { e.stopPropagation(); });
    }

    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            resetAllSelections();
        });
    }

    function resetAllSelections() {
        rows.forEach(row => {
            row.classList.remove('row-selected');
        });
        lastFocusedRow = null;
        updateUIState();
    }

    function updateUIState() {
        const selectedRows = document.querySelectorAll('.row-selected');
        const checkedCount = selectedRows.length;

        const deleteBtnText = document.getElementById('delete-btn-text');
        if (deleteBtnText) {
            deleteBtnText.textContent = checkedCount >= 2 ? `${checkedCount}` : "";
        }

        if (checkedCount >= 1) {
            actionsBar.classList.add('show-actions');
        } else {
            actionsBar.classList.remove('show-actions');
        }
    }

    // ===================================================
    // ROW CLICK SELECTION (NEW)
    // ===================================================
    rows.forEach(row => {
        row.setAttribute('tabindex', '0');
        row.addEventListener('click', function(e) {
            // Ignore clicks on buttons, filters, etc.
            if (e.target.tagName === 'BUTTON' || e.target.closest('button') || 
                e.target.closest('.excel-filter-menu') || e.target.classList.contains('excel-filter-icon')) {
                e.stopPropagation();
                return;
            }

            // Toggle selection on row click
            this.classList.toggle('row-selected');
            
            // Update last focused row for shift+click
            if (this.classList.contains('row-selected')) {
                lastFocusedRow = this;
            }
            
            updateUIState();
        });
    });

    // Shift+Click for range selection
    rows.forEach(row => {
        row.addEventListener('click', function(e) {
            if (e.shiftKey && lastFocusedRow) {
                e.preventDefault();
                toggleRange(lastFocusedRow, this);
            }
        });
    });

    function toggleRange(startRow, endRow) {
        const visibleRows = rows.filter(r => r.style.display !== "none");
        const startIndex = visibleRows.indexOf(startRow);
        const endIndex = visibleRows.indexOf(endRow);
        
        if (startIndex === -1 || endIndex === -1) return;
        const low = Math.min(startIndex, endIndex);
        const high = Math.max(startIndex, endIndex);
        
        visibleRows.forEach((row, index) => {
            if (index >= low && index <= high) {
                row.classList.add('row-selected');
            }
        });
        lastFocusedRow = endRow;
        updateUIState();
    }

    // Keyboard shortcuts
    tableBody.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            e.preventDefault();
            resetAllSelections();
            return;
        }

        const activeRow = document.activeElement;
        if (!activeRow || !activeRow.classList.contains('ledger-row')) return;

        const visibleRows = rows.filter(r => r.style.display !== "none");
        const currentIndex = visibleRows.indexOf(activeRow);
        let targetRow = null;

        if (e.key === 'ArrowDown') {
            if (currentIndex < visibleRows.length - 1) targetRow = visibleRows[currentIndex + 1];
        } else if (e.key === 'ArrowUp') {
            if (currentIndex > 0) targetRow = visibleRows[currentIndex - 1];
        } else if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            activeRow.classList.toggle('row-selected');
            if (activeRow.classList.contains('row-selected')) {
                lastFocusedRow = activeRow;
            }
            updateUIState();
            return;
        }

        if (targetRow) {
            e.preventDefault();
            if (e.shiftKey && lastFocusedRow) {
                toggleRange(lastFocusedRow, targetRow);
            } else {
                lastFocusedRow = targetRow;
            }
            targetRow.focus();
            updateUIState();
        }
    });

    populateFilterMenus();

    // ===================================================
    // SELECT ALL BUTTON
    // ===================================================
    setTimeout(function() {
        const selectAllBtn = document.getElementById('select-all-btn');
        if (selectAllBtn) {
            const newBtn = selectAllBtn.cloneNode(true);
            selectAllBtn.parentNode.replaceChild(newBtn, selectAllBtn);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                rows.forEach(function(row) {
                    if (row.style.display !== "none") {
                        row.classList.add('row-selected');
                    }
                });
                updateUIState();
            });
        }
    }, 100);

    // Clear Selection button
    const clearSelectionBtnElement = document.getElementById('clear-selection-btn');
    if (clearSelectionBtnElement) {
        clearSelectionBtnElement.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            resetAllSelections();
        });
    }
});

// ===================================================
// BATCH DELETION LOADER ENGINE INTERCEPTOR
// ===================================================
document.addEventListener("DOMContentLoaded", function() {
    const bulkDeleteForm = document.getElementById("bulk-delete-form");
    const processingLoader = document.getElementById("delete-loading-overlay");

    if (bulkDeleteForm && processingLoader) {
        bulkDeleteForm.addEventListener("submit", function (event) {
            // Get all selected row IDs
            const selectedRows = document.querySelectorAll('.row-selected');
            if (selectedRows.length === 0) {
                event.preventDefault();
                alert('Please select at least one row to delete.');
                return;
            }
            
            const userConfirmed = confirm(`Are you sure you want to permanently delete ${selectedRows.length} selected transaction(s)?`);
            if (userConfirmed) {
                // Add selected IDs to form
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