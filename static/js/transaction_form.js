// static/js/transaction_form.js

// ============================================
// TRANSACTION FORM - COMPLETE JAVASCRIPT
// ============================================

document.addEventListener("DOMContentLoaded", function() {
    // ===================================================
    // 1. FORM FIELD STYLING INJECTOR
    // ===================================================
    document.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(function(el) {
        if (el.tagName.toLowerCase() === 'select') {
            el.classList.add('form-select');
        } else {
            el.classList.add('form-control');
        }
        if (!el.closest('.input-group')){
            el.classList.add('rounded-3');
        }
    });

    // Ensure quantity field input inherits flat styling inside its group wrapper
    const qtyField = document.getElementById('id_quantity');
    if (qtyField) {
        qtyField.classList.remove('rounded-3');
        qtyField.classList.add('rounded-start-3', 'border-end-0');
    }

    // ===================================================
    // 2. PAYER DROPDOWN WORKFLOW SYNC ENGINE
    // ===================================================
    const hiddenPayerSelect = document.getElementById('id_payer');
    const dropdownLabel = document.getElementById('payerDropdownLabel');

    if (hiddenPayerSelect && dropdownLabel) {
        const selectedOption = hiddenPayerSelect.options[hiddenPayerSelect.selectedIndex];
        if (selectedOption && selectedOption.value) {
            dropdownLabel.textContent = selectedOption.text;
            dropdownLabel.classList.remove('text-muted');
        }

        document.querySelectorAll('.custom-payer-item .option-text-click, .custom-payer-option').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const parentLi = this.closest('[data-value]');
                const val = parentLi ? parentLi.getAttribute('data-value') : '';
                const text = parentLi ? parentLi.getAttribute('data-name') : '---------';

                hiddenPayerSelect.value = val;
                dropdownLabel.textContent = text;
                
                if(val === '') {
                    dropdownLabel.classList.add('text-muted');
                } else {
                    dropdownLabel.classList.remove('text-muted');
                }
            });
        });

        document.querySelectorAll('.no-bubble').forEach(menu => {
            menu.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });
    }

    // ===================================================
    // 3. DIRECT ONE-STEP INTERACTIVE SEARCH ENGINE WITH AUTO-UNIT FETCH
    // ===================================================
    const hiddenItemSelect = document.getElementById('id_item');
    const itemSearchInput = document.getElementById('itemSearchInput');
    const itemDropdownPanel = document.getElementById('itemDropdownPanel');
    const unitAddon = document.getElementById('quantity-unit-addon');

    function updateUnitBadge(unitValue) {
        if (unitAddon) {
            unitAddon.textContent = unitValue ? unitValue : '-';
        }
    }

    if (hiddenItemSelect && itemSearchInput && itemDropdownPanel) {
        
        const initialOption = hiddenItemSelect.options[hiddenItemSelect.selectedIndex];
        if (initialOption && initialOption.value) {
            const matchingRow = document.querySelector(`.custom-item-row[data-value="${initialOption.value}"]`);
            if (matchingRow) {
                itemSearchInput.value = matchingRow.getAttribute('data-display-name');
                updateUnitBadge(matchingRow.getAttribute('data-unit'));
            } else {
                itemSearchInput.value = initialOption.text;
            }
        }

        itemSearchInput.addEventListener('focus', function() {
            itemDropdownPanel.classList.remove('d-none');
            filterItems(this.value);
        });

        itemSearchInput.addEventListener('input', function() {
            filterItems(this.value);
            if (this.value === '') {
                hiddenItemSelect.value = '';
                updateUnitBadge('-');
            }
        });

        function filterItems(searchText) {
            const filterText = searchText.toLowerCase().trim();
            const itemRows = document.querySelectorAll('.custom-item-row');
            let matches = 0;

            itemRows.forEach(row => {
                const itemName = row.getAttribute('data-name');
                if (itemName.includes(filterText)) {
                    row.style.setProperty('display', 'flex', 'important');
                    matches++;
                } else {
                    row.style.setProperty('display', 'none', 'important');
                }
            });

            if (matches === 0 && filterText.length > 0) {
                itemDropdownPanel.classList.add('d-none');
            } else {
                itemDropdownPanel.classList.remove('d-none');
            }
        }

        document.querySelectorAll('.custom-item-row').forEach(row => {
            row.addEventListener('click', function(e) {
                if (e.target.closest('.no-bubble')) return;

                const val = this.getAttribute('data-value');
                const text = this.getAttribute('data-display-name');
                const unit = this.getAttribute('data-unit');

                hiddenItemSelect.value = val;
                itemSearchInput.value = text;
                
                updateUnitBadge(unit);
                itemDropdownPanel.classList.add('d-none');
            });
        });

        document.querySelectorAll('.no-bubble').forEach(menu => {
            menu.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });

        document.addEventListener('click', function(e) {
            if (!e.target.closest('#itemAutocompleteWrapper')) {
                itemDropdownPanel.classList.add('d-none');
                
                const currentSaved = hiddenItemSelect.options[hiddenItemSelect.selectedIndex];
                if (currentSaved && currentSaved.value) {
                    const matchingRow = document.querySelector(`.custom-item-row[data-value="${currentSaved.value}"]`);
                    if (matchingRow) {
                        itemSearchInput.value = matchingRow.getAttribute('data-display-name');
                        updateUnitBadge(matchingRow.getAttribute('data-unit'));
                    } else {
                        itemSearchInput.value = currentSaved.text;
                    }
                } else {
                    itemSearchInput.value = '';
                    updateUnitBadge('-');
                }
            }
        });
    }
});