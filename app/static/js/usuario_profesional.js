(function () {
    'use strict';

    function initialize(form) {
        const role = form.querySelector('#rol');
        const profile = form.querySelector('#perfil_profesional');
        const profileField = form.querySelector('[data-professional-profile-field]');
        const license = form.querySelector('#cedula_profesional');
        const licenseField = form.querySelector('[data-professional-license-field]');
        const detailFields = form.querySelectorAll('[data-professional-details-field]');
        if (!role || !profile || !profileField) return;

        function synchronize() {
            const isReception = role.value === 'recepcion';
            const isClinical = role.value === 'medico';

            profileField.hidden = isReception;
            profile.disabled = isReception;
            profile.required = isClinical;
            if (isReception) profile.value = '';

            if (license && licenseField) {
                licenseField.hidden = isReception;
                license.disabled = isReception;
                if (isReception) license.value = '';
            }
            detailFields.forEach(function (field) {
                field.hidden = isReception;
                field.querySelectorAll('input').forEach(function (input) {
                    input.disabled = isReception;
                    if (isReception) input.value = '';
                });
            });
        }

        role.addEventListener('change', synchronize);
        synchronize();
    }

    document.querySelectorAll('[data-user-professional-form]').forEach(initialize);
})();
