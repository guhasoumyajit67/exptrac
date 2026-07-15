document.addEventListener("DOMContentLoaded", function() {
    // ===================================================
    // 1. FORM FIELD STYLING INJECTOR
    // ===================================================
    document.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(function(el) {
        el.classList.add('form-control', 'rounded-3');
    });

    // ===================================================
    // 2. COLOR PALETTE WORKFLOW SYNC ENGINE
    // ===================================================
    const colorInput = document.querySelector('input[name="color"]');
    const dots = document.querySelectorAll('.dot-palette-item');

    // Set default color if empty
    if (colorInput && !colorInput.value) {
        colorInput.value = "#0d6efd";
    } else if (colorInput) {
        // Sync active dot with existing color
        dots.forEach(d => {
            if (d.getAttribute('data-color') === colorInput.value) {
                dots.forEach(item => item.classList.remove('active'));
                d.classList.add('active');
            }
        });
    }

    // Add click handlers to color dots
    dots.forEach(function(dot) {
        dot.addEventListener('click', function() {
            // Remove active class from all dots
            dots.forEach(item => item.classList.remove('active'));
            
            // Add active class to clicked dot
            this.classList.add('active');
            
            // Update hidden color input
            if (colorInput) {
                colorInput.value = this.getAttribute('data-color');
            }
        });
    });

    // ===================================================
    // 3. CUSTOM COLOR PICKER (Plus Button)
    // ===================================================
    const customPickerTrigger = document.querySelector('.custom-picker-trigger');
    const hiddenColorInput = document.getElementById('hidden-wheel-input');

    if (customPickerTrigger && hiddenColorInput) {
        // Click on the plus icon triggers the color picker
        customPickerTrigger.addEventListener('click', function(e) {
            e.stopPropagation();
            hiddenColorInput.click();
        });

        // When a color is selected from the picker
        hiddenColorInput.addEventListener('input', function() {
            const selectedColor = this.value;
            
            // Update the hidden color input
            if (colorInput) {
                colorInput.value = selectedColor;
            }
            
            // Update the palette: remove active from all dots
            dots.forEach(item => item.classList.remove('active'));
            
            // Add active class to the custom picker trigger
            customPickerTrigger.classList.add('active');
            
            // Update the background of the custom picker to show selected color
            customPickerTrigger.style.background = selectedColor;
            customPickerTrigger.style.opacity = '1';
        });
    }
});