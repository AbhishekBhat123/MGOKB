$(document).ready(function() {
    let lineItemCounter = 0;
    let manageModal;
    let currentManageType = null;

    $('#icnbFields').hide();
    $('#discountRow').hide();
    $('#no-items-row').show();

    if ($('#manageOptionsModal').length > 0) {
        manageModal = new bootstrap.Modal(document.getElementById('manageOptionsModal'));
    }

    function saveFormState() {
        const formData = {
            docType: $('#docType').val(),
            monthYear: $('#monthYear').val(),
            applyDiscount: $('#discountCheckbox').is(':checked'),
            discountPercentage: parseFloat($('#discountPercentage').val()) || 0,
            advancePayment: $('#advancePaymentCheckbox').is(':checked'),
            reverseCharge: $('#reverseCharge').val(),
            paymentMethod: $('#paymentMethod').val(),
            reference: $('#reference').val() === 'Add New' ? $('#newReference').val().trim() : $('#reference').val(),
            purpose: $('#purpose').val() === 'Add New' ? $('#newPurpose').val().trim() : $('#purpose').val(),
            category: $('#category').val() === 'Add New' ? $('#newCategory').val().trim() : $('#category').val(),
            gstout: $('#gstout').val() === 'Add New' ? $('#newGstout').val().trim() : $('#gstout').val(),
            gstin: $('#gstin').val() === 'Add New' ? $('#newGstin').val().trim() : $('#gstin').val(),
            lineItems: [],
        };

        $('#lineItemsTableBody tr:not(#no-items-row)').each(function() {
            const row = $(this);
            const dataCell = row.find('td.d-none');
            const item = {
                costCategory: row.find('td:eq(0)').text(),
                description: row.find('td:eq(1)').text(),
                sac: row.find('td:eq(2)').text(),
                rateValue: parseFloat(dataCell.data('rate-value')) || parseFloat(row.find('td:eq(3)').text().split(' per ')[0]),
                rateUnit: dataCell.data('rate-unit') || row.find('td:eq(3)').text().split(' per ')[1],
                unitsConsumedValue: parseFloat(dataCell.data('units-value')) || parseFloat(row.find('td:eq(4)').text().split(' ')[0]),
                unitsConsumedUnit: dataCell.data('units-unit') || row.find('td:eq(4)').text().split(' ')[1],
                total: parseFloat(row.find('td:eq(5)').text())
            };
            formData.lineItems.push(item);
        });

        try {
            sessionStorage.setItem('invoiceFormData', JSON.stringify(formData));
        } catch (e) {
            console.error("Could not save form state to sessionStorage:", e);
        }
    }

    function loadFormState() {
        try {
            let formData = null;
            if (typeof preview_data_json !== 'undefined' && preview_data_json) {
                try {
                    formData = JSON.parse(preview_data_json);
                    sessionStorage.removeItem('invoiceFormData');
                } catch (e) {
                    console.error("Could not parse preview_data_json:", e);
                }
            }

            if (!formData) {
                const savedState = sessionStorage.getItem('invoiceFormData');
                if (savedState) {
                    formData = JSON.parse(savedState);
                }
            }

            if (formData) {
                $('#docType').val(formData.docType || '').trigger('change');

                function loadManagedDropdown(selectId, value) {
                    const $select = $(selectId);
                    const $newInput = $select.next('.add-new-input');
                    const fieldName = $select.attr('id');

                    if (value && value !== '') {
                        // Check if the value exists in the dropdown options
                        if ($select.find(`option[value='${escapeHtml(value)}']`).length > 0) {
                            $select.val(value);
                            if ($newInput.length) $newInput.hide().val('');
                        } else { 
                            if ($newInput.length) {
                                $select.val('Add New');
                                $newInput.val(value).show();
                            } else { 
                                $select.append(`<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`);
                                $select.val(value);
                                console.warn(`Added missing option "${value}" to ${fieldName} dropdown`);
                            }
                        }
                        if (value !== 'Manage' && value !== 'Add New') {
                            $select.data('last-valid-selection', value);
                        }
                    } else {
                        $select.val('').trigger('change');
                        if ($newInput.length) $newInput.hide().val('');
                    }
                }

                loadManagedDropdown('#reference', formData.reference);
                loadManagedDropdown('#purpose', formData.purpose);
                loadManagedDropdown('#category', formData.category);
                loadManagedDropdown('#gstout', formData.gstout);
                loadManagedDropdown('#gstin', formData.gstin);
                loadManagedDropdown('#reverseCharge', formData.reverseCharge);
                loadManagedDropdown('#paymentMethod', formData.paymentMethod);

                $('#monthYear').val(formData.monthYear || '');
                $('#discountCheckbox').prop('checked', formData.applyDiscount || false);
                $('#discountPercentage').val(formData.discountPercentage || 0);
                $('#advancePaymentCheckbox').prop('checked', formData.advancePayment || false);

                $('#lineItemsTableBody').empty();
                lineItemCounter = 0;
                if (formData.lineItems && formData.lineItems.length > 0) {
                    $('#no-items-row').hide();
                    formData.lineItems.forEach(function(item) {
                        lineItemCounter++;
                        const newRow = `
                            <tr data-row-id="${lineItemCounter}">
                                <th scope="row">${lineItemCounter}</th>
                                <td>${escapeHtml(item.costCategory)}</td>
                                <td>${escapeHtml(item.description)}</td>
                                <td>${escapeHtml(item.sac)}</td>
                                <td>${escapeHtml(item.rateValue)} per ${escapeHtml(item.rateUnit)}</td>
                                <td>${escapeHtml(item.unitsConsumedValue)} ${escapeHtml(item.unitsConsumedUnit)}</td>
                                <td class="line-item-total">${item.total.toFixed(2)}</td>
                                <td class="text-center">
                                    <i class="bi bi-trash delete-btn" title="Delete Item" style="cursor:pointer; color: red;"></i>
                                </td>
                                <td class="d-none" data-rate-value="${item.rateValue}" data-rate-unit="${item.rateUnit}" data-units-value="${item.unitsConsumedValue}" data-units-unit="${item.unitsConsumedUnit}"></td>
                            </tr>
                        `;
                        $('#lineItemsTableBody').append(newRow);
                    });
                    updateTotals();
                } else {
                    $('#lineItemsTableBody').append('<tr id="no-items-row"><td colspan="8" class="text-center text-muted">No items added yet.</td></tr>');
                    $('#no-items-row').show();
                    updateTotals();
                }

                if (formData.docType && formData.docType !== '') {
                    $('#icnbFields').show();
                }
            }
        } catch (e) {
            console.error("Could not load form state:", e);
            sessionStorage.removeItem('invoiceFormData');
        }
    }

    $('#docType').on('change', function() {
        const selectedType = $(this).val();
        const $icnbFieldsDiv = $('#icnbFields');
        const $detailsHeading = $('#detailsHeading');

        if (selectedType !== '') {
            if (selectedType === 'icnb') {
                $detailsHeading.text('ICNB Details');
            } else if (selectedType === 'quote') {
                $detailsHeading.text('Quotation Details');
            }
            $icnbFieldsDiv.slideDown();
        } else {
            $icnbFieldsDiv.slideUp();
        }
        saveFormState();
    });

    $('#monthYear').on('change', saveFormState);

    $('#invoice-form').on('change', 'select.managed-dropdown', function() {
        const selectedValue = $(this).val();
        const $select = $(this);
        const optionType = $select.data('option-type');
        const $newInput = $select.next('.add-new-input');

        if (selectedValue === 'Add New') {
            if ($newInput.length) {
                $newInput.show().focus();
            }
            $select.data('last-valid-selection', $select.find('option:first-child').val());
        } else {
            if ($newInput.length) {
                $newInput.hide().val('');
            }
            if (selectedValue !== 'Manage') {
                $select.data('last-valid-selection', selectedValue);
            }
        }

        if (selectedValue === 'Manage') {
            if (optionType) {
                openManageModal(optionType, $select.prev('label').text());
                const lastSelection = $select.data('last-valid-selection') || $select.find('option:first-child').val();
                $select.val(lastSelection);
            } else {
                console.error("Manage selected but data-option-type is missing!");
                $select.val($select.find('option:first-child').val());
            }
        }
        saveFormState();
    });

    $('#invoice-form').on('input', '.add-new-input', saveFormState);
    $('#invoice-form').on('input', '#itemRateValue, #itemUnitsConsumedValue', saveFormState);

    $('#addItemBtn').on('click', function() {
        const costCategoryVal = $('#costCategory').val();
        const costCategory = (costCategoryVal === 'Add New') ? $('#newCostCategory').val().trim() : costCategoryVal;
        const descriptionVal = $('#itemDescription').val();
        const description = (descriptionVal === 'Add New') ? $('#newItemDescription').val().trim() : descriptionVal;
        const sacVal = $('#itemSac').val();
        const sac = (sacVal === 'Add New') ? $('#newItemSac').val().trim() : sacVal;
        const rateValue = parseFloat($('#itemRateValue').val()) || 0;
        const rateUnit = $('#itemRateUnit').val();
        const unitsConsumedValue = parseFloat($('#itemUnitsConsumedValue').val()) || 0;
        const unitsConsumedUnit = $('#itemUnitsConsumedUnit').val();

        if (!costCategory || !description || !sac || isNaN(rateValue) || isNaN(unitsConsumedValue)) {
            alert('Please fill in all line item fields with valid values.');
            return;
        }

        if ((costCategoryVal === 'Add New' && !costCategory) ||
            (descriptionVal === 'Add New' && !description) ||
            (sacVal === 'Add New' && !sac)) {
            alert('Please enter a value if "Add New" is selected for an item field.');
            return;
        }

        const total = (rateValue * unitsConsumedValue);
        lineItemCounter++;

        const newRow = `
            <tr data-row-id="${lineItemCounter}">
                <th scope="row">${lineItemCounter}</th>
                <td>${escapeHtml(costCategory)}</td>
                <td>${escapeHtml(description)}</td>
                <td>${escapeHtml(sac)}</td>
                <td>${escapeHtml(rateValue)} per ${escapeHtml(rateUnit)}</td>
                <td>${escapeHtml(unitsConsumedValue)} ${escapeHtml(unitsConsumedUnit)}</td>
                <td class="line-item-total">${total.toFixed(2)}</td>
                <td class="text-center">
                    <i class="bi bi-trash delete-btn" title="Delete Item" style="cursor:pointer; color: red;"></i>
                </td>
                <td class="d-none" data-rate-value="${rateValue}" data-rate-unit="${rateUnit}" data-units-value="${unitsConsumedValue}" data-units-unit="${unitsConsumedUnit}"></td>
            </tr>
        `;

        $('#no-items-row').hide();
        $('#lineItemsTableBody').append(newRow);
        updateTotals();

        $('#costCategory, #itemDescription, #itemSac').val('');
        $('#newCostCategory, #newItemDescription, #newItemSac').hide().val('');
        $('#itemRateValue, #itemUnitsConsumedValue').val('');
        $('#costCategory').focus();

        saveFormState();
    });

    $('#lineItemsTableBody').on('click', '.delete-btn', function() {
        $(this).closest('tr').remove();
        updateSlNumbers();
        updateTotals();
        if ($('#lineItemsTableBody tr:not(#no-items-row)').length === 0) {
            $('#no-items-row').show();
            lineItemCounter = 0;
        }
        saveFormState();
    });

    $('#discountCheckbox').on('change', function() {
        updateTotals();
        saveFormState();
    });

    $('#discountPercentage').on('input', function() {
        if (parseFloat($(this).val()) < 0) $(this).val(0);
        if (parseFloat($(this).val()) > 100) $(this).val(100);
        updateTotals();
        saveFormState();
    });

    $('#invoice-form').on('change', '#advancePaymentCheckbox, #reverseCharge, #paymentMethod', saveFormState);

    $('#invoice-form').on('submit', function(event) {
        event.preventDefault();

        const formData = {
            docType: $('#docType').val(),
            monthYear: $('#monthYear').val(),
            lineItems: [],
            applyDiscount: $('#discountCheckbox').is(':checked'),
            discountPercentage: parseFloat($('#discountPercentage').val()) || 0,
            advancePayment: $('#advancePaymentCheckbox').is(':checked'),
            subTotal: parseFloat($('#subTotalAmount').text()),
            discountAmount: parseFloat($('#discountAmount').text().replace('- ', '')),
            grandTotal: parseFloat($('#grandTotalAmount').text())
        };

        $('.managed-dropdown').each(function() {
            const $select = $(this);
            const fieldId = $select.attr('id');
            const fieldName = $select.attr('name');
            const isItemField = fieldId.startsWith('item');

            if (fieldName && !isItemField) {
                const selectedValue = $select.val();
                const $newInput = $select.next('.add-new-input');
                const newValue = $newInput.length && $newInput.is(':visible') ? $newInput.val().trim() : null;

                formData[fieldName] = selectedValue;
                if (newValue !== null) {
                    const newKey = 'new' + fieldName.charAt(0).toUpperCase() + fieldName.slice(1).replace('Selected', '');
                    formData[newKey] = newValue;
                }
            }
        });

        $('#lineItemsTableBody tr:not(#no-items-row)').each(function() {
            const row = $(this);
            const dataCell = row.find('td.d-none');
            const item = {
                slNo: parseInt(row.find('th').text()),
                costCategory: row.find('td:eq(0)').text(),
                description: row.find('td:eq(1)').text(),
                sac: row.find('td:eq(2)').text(),
                rateValue: parseFloat(dataCell.data('rate-value')),
                rateUnit: dataCell.data('rate-unit'),
                unitsConsumedValue: parseFloat(dataCell.data('units-value')),
                unitsConsumedUnit: dataCell.data('units-unit'),
                total: parseFloat(row.find('td:eq(5)').text())
            };
            formData.lineItems.push(item);
        });

        if (!formData.docType) {
            alert('Please select a Document Type.');
            $('#docType').focus();
            return;
        }

        if (formData.docType === 'icnb' || formData.docType === 'quote') {
            const requiredManagedFields = ['reference', 'purpose', 'category', 'gstout', 'gstin'];
            for (const fieldId of requiredManagedFields) {
                const selectedVal = $(`#${fieldId}`).val();
                const newVal = $(`#new${fieldId.charAt(0).toUpperCase() + fieldId.slice(1)}`).val().trim();
                if (!selectedVal || (selectedVal === 'Add New' && !newVal)) {
                    alert(`Please select or enter a value for "${$(`label[for="${fieldId}"]`).text()}".`);
                    $(`#${fieldId}`).focus();
                    return;
                }
            }

            if (!formData.monthYear) {
                alert('Please select a Billing Month & Year.');
                $('#monthYear').focus();
                return;
            }

            if (formData.lineItems.length === 0) {
                alert('Please add at least one line item.');
                return;
            }
        }

        saveFormState();

        console.log("Sending Form Data:", JSON.stringify(formData, null, 2));
        $.ajax({
            url: '/generate',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                console.log('Server Response:', response);
                if (response.redirect) {
                    window.location.href = response.redirect;
                } else {
                    alert('Document data submitted, but no redirect instruction received.');
                }
            },
            error: function(xhr, status, error) {
                console.error("Error submitting form:", status, error, xhr.responseText);
                alert(`Error submitting data: ${xhr.responseJSON ? (xhr.responseJSON.message || xhr.responseJSON.error || xhr.responseText) : error}`);
            }
        });
    });

    function openManageModal(optionType, label) {
        currentManageType = optionType;
        $('#manageOptionsModalLabel').text(`Manage ${label} Options`);
        $('#manageOptionsList').html('<li>Loading...</li>');
        $('#manageOptionsError').hide();
        $('#manageOptionsMessage').hide();
        manageModal.show();

        $.ajax({
            url: `/get_options/${optionType}`,
            type: 'GET',
            success: function(options) {
                populateManageModalList(options);
            },
            error: function(xhr, status, error) {
                console.error(`Error fetching options for ${optionType}:`, status, error);
                $('#manageOptionsList').html('');
                $('#manageOptionsError').text(`Error loading options: ${xhr.responseJSON ? xhr.responseJSON.description : error}`).show();
            }
        });
    }

    function populateManageModalList(options) {
        const $list = $('#manageOptionsList');
        $list.empty();
        if (options && options.length > 0) {
            options.forEach(function(option) {
                const escapedValue = escapeHtml(String(option.value || option.name || 'N/A'));
                const optionId = option.id;
                const isReservedReverseCharge = (currentManageType === 'reverseCharge' && ['Yes', 'No'].includes(option.value));
                const disabledClass = isReservedReverseCharge ? 'disabled' : '';
                const deleteButtonHtml = optionId && !isReservedReverseCharge ?
                    `<button class="btn btn-sm btn-outline-danger ms-2 delete-option-btn" data-option-id="${optionId}" title="Delete Option"><i class="bi bi-trash"></i></button>` :
                    `<button class="btn btn-sm btn-outline-secondary ms-2 ${disabledClass}" ${disabledClass ? 'disabled' : ''} title="Cannot delete this option"><i class="bi bi-trash"></i></button>`;

                $list.append(`
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span>${escapedValue}</span>
                        ${deleteButtonHtml}
                    </li>
                `);
            });
        } else {
            $list.append('<li class="list-group-item text-muted">No options available.</li>');
        }
    }

    $('#manageOptionsModal').on('click', '.delete-option-btn', function() {
        const $button = $(this);
        const optionId = $button.data('option-id');
        if (!currentManageType || !optionId) {
            console.error("Missing option type or ID for deletion.");
            return;
        }

        if (confirm('Are you sure you want to delete this option? This cannot be undone.')) {
            $button.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
            $('#manageOptionsError').hide();
            $('#manageOptionsMessage').hide();

            $.ajax({
                url: `/delete_option/${currentManageType}/${optionId}`,
                type: 'DELETE',
                success: function(response) {
                    console.log(response);
                    $('#manageOptionsMessage').text(response.message || 'Option deleted.').show();
                    $button.closest('li').fadeOut(300, function() { $(this).remove(); });
                    refreshManagedDropdown(currentManageType, () => {
                        saveFormState();
                    });
                },
                error: function(xhr, status, error) {
                    console.error(`Error deleting option ${optionId} for ${currentManageType}:`, status, error);
                    const errorText = xhr.responseJSON ? (xhr.responseJSON.message || xhr.responseJSON.description) : error;
                    $('#manageOptionsError').text(`Error deleting: ${errorText}`).show();
                    $button.prop('disabled', false).html('<i class="bi bi-trash"></i>');
                }
            });
        }
    });

    function refreshManagedDropdown(optionType, callback) {
        const $select = $(`select.managed-dropdown[data-option-type="${optionType}"]`);
        if ($select.length === 0) {
            console.error(`Dropdown with data-option-type="${optionType}" not found.`);
            if (callback) callback();
            return;
        }

        const currentSelectedValue = $select.val();
        const currentNewValue = $select.next('.add-new-input').val();

        $.ajax({
            url: `/get_options/${optionType}`,
            type: 'GET',
            success: function(options) {
                $select.empty();
                $select.append('<option value="" selected disabled>-- Select --</option>');

                options.forEach(function(option) {
                    const optionValue = option.value !== undefined ? option.value : option.name;
                    const optionText = option.name !== undefined ? option.name : option.value;

                    if (optionValue !== undefined) {
                        $select.append(`<option value="${escapeHtml(String(optionValue))}">${escapeHtml(String(optionText))}</option>`);
                    }
                });

                const hasAddNew = $select.next('.add-new-input').length > 0;
                if (hasAddNew) {
                    $select.append('<option value="Add New" class="add-new-option">Add New</option>');
                }
                $select.append('<option value="Manage" class="manage-option">Manage...</option>');

                if ($select.find(`option[value='${currentSelectedValue}']`).length > 0) {
                    $select.val(currentSelectedValue);
                    if (hasAddNew) $select.next('.add-new-input').hide();
                } else if (currentSelectedValue === 'Add New' && hasAddNew) {
                    $select.val('Add New');
                    $select.next('.add-new-input').val(currentNewValue).show();
                } else {
                    $select.val('').trigger('change');
                }

                if (callback) callback();
            },
            error: function(xhr, status, error) {
                console.error(`Error refreshing options for ${optionType}:`, status, error);
                if (callback) callback();
            }
        });
    }

    $('#manageOptionsModal').on('hidden.bs.modal', function () {
        $('#manageOptionsError').hide().text('');
        $('#manageOptionsMessage').hide().text('');
        currentManageType = null;
    });

    function updateTotals() {
        let subTotal = 0;
        $('#lineItemsTableBody tr:not(#no-items-row)').each(function() {
            subTotal += parseFloat($(this).find('td.line-item-total').text()) || 0;
        });

        $('#subTotalAmount').text(subTotal.toFixed(2));

        let discountAmount = 0;
        let grandTotal = subTotal;

        if ($('#discountCheckbox').is(':checked')) {
            $('#discountRow').show();
            const discountPercent = parseFloat($('#discountPercentage').val()) || 0;
            discountAmount = (subTotal * discountPercent) / 100;
            grandTotal = subTotal - discountAmount;
            $('#discountAmount').text('- ' + discountAmount.toFixed(2));
        } else {
            $('#discountRow').hide();
            $('#discountAmount').text('- 0.00');
        }

        grandTotal = Math.max(0, grandTotal);
        $('#grandTotalAmount').text(grandTotal.toFixed(2));
    }

    function updateSlNumbers() {
        $('#lineItemsTableBody tr:not(#no-items-row)').each(function(index) {
            $(this).find('th:first').text(index + 1);
        });
        lineItemCounter = $('#lineItemsTableBody tr:not(#no-items-row)').length;
    }

    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return unsafe;
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    loadFormState();
});