// static/js/item_form.js

// ============================================
// ITEM FORM - COMPLETE JAVASCRIPT
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
        el.classList.add('rounded-3');
    });

    // ===================================================
    // 2. CATEGORY DROPDOWN SEARCH ENGINE
    // ===================================================
    const hiddenCategorySelect = document.getElementById('id_category');
    const categorySearchInput = document.getElementById('categorySearchInput');
    const categoryDropdownPanel = document.getElementById('categoryDropdownPanel');

    if (hiddenCategorySelect && categorySearchInput && categoryDropdownPanel) {
        
        // Re-populate active input value if editing or bound initial records exist
        const initialOption = hiddenCategorySelect.options[hiddenCategorySelect.selectedIndex];
        if (initialOption && initialOption.value) {
            categorySearchInput.value = initialOption.text;
        }

        categorySearchInput.addEventListener('focus', function() {
            categoryDropdownPanel.classList.remove('d-none');
            filterCategories(this.value);
        });

        categorySearchInput.addEventListener('input', function() {
            filterCategories(this.value);
            if (this.value === '') {
                hiddenCategorySelect.value = '';
            }
        });

        function filterCategories(searchText) {
            const filterText = searchText.toLowerCase().trim();
            const categoryRows = document.querySelectorAll('.custom-category-row');
            let matches = 0;

            categoryRows.forEach(row => {
                const categoryName = row.getAttribute('data-name').toLowerCase();
                if (categoryName.includes(filterText)) {
                    row.style.setProperty('display', 'flex', 'important');
                    matches++;
                } else {
                    row.style.setProperty('display', 'none', 'important');
                }
            });

            if (matches === 0 && filterText.length > 0) {
                categoryDropdownPanel.classList.add('d-none');
            } else {
                categoryDropdownPanel.classList.remove('d-none');
            }
        }

        // Sync structural parameters on record choice selection clicks
        document.querySelectorAll('.custom-category-row').forEach(row => {
            row.addEventListener('click', function() {
                const val = this.getAttribute('data-value');
                const text = this.getAttribute('data-name');

                hiddenCategorySelect.value = val;
                categorySearchInput.value = text;
                categoryDropdownPanel.classList.add('d-none');
            });
        });

        // Auto-fallback boundary check when clicking away out of frame bounds
        document.addEventListener('click', function(e) {
            if (!e.target.closest('#categoryAutocompleteWrapper')) {
                categoryDropdownPanel.classList.add('d-none');
                
                const currentSaved = hiddenCategorySelect.options[hiddenCategorySelect.selectedIndex];
                categorySearchInput.value = (currentSaved && currentSaved.value) ? currentSaved.text : '';
            }
        });
    }
});