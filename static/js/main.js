/**
 * NexBank Simple Banking System
 * Frontend Interactions & Utility Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Table Search Filter
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.data-table tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(term)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 2. Modal open / close handlers
    document.querySelectorAll('[data-modal-target]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const modalId = trigger.getAttribute('data-modal-target');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
            }
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Close modal on clicking overlay backdrop
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });

    // 3. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// Helper to open modal programmatically
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

// Helper to close modal programmatically
function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

// Function to populate edit branch modal
function openEditBranch(id, name, address, city, phone) {
    const form = document.getElementById('editBranchForm');
    if (form) {
        form.action = `/branches/edit/${id}`;
        document.getElementById('editBranchName').value = name;
        document.getElementById('editBranchAddress').value = address;
        document.getElementById('editBranchCity').value = city;
        document.getElementById('editBranchPhone').value = phone;
        openModal('editBranchModal');
    }
}

// Function to populate edit customer modal
function openEditCustomer(id, fname, lname, email, phone, addr, city, dob, branchId) {
    const form = document.getElementById('editCustomerForm');
    if (form) {
        form.action = `/customers/edit/${id}`;
        document.getElementById('editCustFname').value = fname;
        document.getElementById('editCustLname').value = lname;
        document.getElementById('editCustEmail').value = email;
        document.getElementById('editCustPhone').value = phone;
        document.getElementById('editCustAddr').value = addr;
        document.getElementById('editCustCity').value = city;
        document.getElementById('editCustDob').value = dob;
        document.getElementById('editCustBranch').value = branchId;
        openModal('editCustomerModal');
    }
}

// Function to show transaction receipt modal
function showReceipt(txnId, acctId, custName, type, amount, desc, date) {
    document.getElementById('receiptTxnId').textContent = '#' + txnId;
    document.getElementById('receiptAcct').textContent = 'Acct #' + acctId;
    document.getElementById('receiptCust').textContent = custName;
    document.getElementById('receiptType').textContent = type.toUpperCase();
    document.getElementById('receiptAmount').textContent = '$' + parseFloat(amount).toLocaleString('en-US', {minimumFractionDigits: 2});
    document.getElementById('receiptDesc').textContent = desc || 'N/A';
    document.getElementById('receiptDate').textContent = date;
    openModal('receiptModal');
}
