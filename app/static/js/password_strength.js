document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const strengthBar = document.getElementById('strength-bar');
    const strengthText = document.getElementById('strength-text');

    if (!passwordInput || !strengthBar || !strengthText) return;

    // Password Strength Logic
    passwordInput.addEventListener('input', () => {
        const val = passwordInput.value;
        const result = checkStrength(val);
        
        strengthBar.style.width = result.percent + '%';
        strengthBar.style.backgroundColor = result.color;
        
        strengthText.innerText = `Strength: ${result.label}`;
        strengthText.style.color = result.color;

        // Also trigger match check if confirm input has value
        if (confirmPasswordInput && confirmPasswordInput.value) {
            validateMatch();
        }
    });

    // Password Matching Logic
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', validateMatch);
    }

    function validateMatch() {
        if (!confirmPasswordInput) return;
        
        const pwd = passwordInput.value;
        const cpwd = confirmPasswordInput.value;
        
        let matchText = document.getElementById('match-text');
        if (!matchText) {
            matchText = document.createElement('small');
            matchText.id = 'match-text';
            matchText.style.display = 'block';
            matchText.style.marginTop = '5px';
            matchText.style.fontSize = '0.75rem';
            confirmPasswordInput.parentElement.appendChild(matchText);
        }

        if (!cpwd) {
            matchText.innerText = '';
            confirmPasswordInput.style.borderColor = '#ced4da';
        } else if (pwd === cpwd) {
            matchText.innerText = '✓ Passwords match';
            matchText.style.color = '#10b981'; // Success Green
            confirmPasswordInput.style.borderColor = '#10b981';
        } else {
            matchText.innerText = '✗ Passwords do not match';
            matchText.style.color = '#ef4444'; // Danger Red
            confirmPasswordInput.style.borderColor = '#ef4444';
        }
    }

    function checkStrength(password) {
        let score = 0;
        if (!password) return { percent: 0, label: 'Empty', color: '#cbd5e1' };

        if (password.length >= 8) score += 1;
        if (password.length >= 12) score += 1;
        if (/[a-z]/.test(password)) score += 1;
        if (/[A-Z]/.test(password)) score += 1;
        if (/[0-9]/.test(password)) score += 1;
        if (/[^A-Za-z0-9]/.test(password)) score += 1;

        if (score < 3) return { percent: 25, label: 'Weak', color: '#ef4444' };
        if (score < 4) return { percent: 50, label: 'Fair', color: '#f59e0b' };
        if (score < 5) return { percent: 75, label: 'Good', color: '#3b82f6' };
        return { percent: 100, label: 'Strong', color: '#10b981' };
    }
});
