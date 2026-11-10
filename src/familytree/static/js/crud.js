/**
 * Family Tree - Interactive CRUD Operations
 * Handles modal dialogs and API calls for person management
 */

(function() {
    'use strict';

    // ==================== MODAL MANAGEMENT ====================
    
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    function closeAllModals() {
        document.querySelectorAll('[id^="modal-"]').forEach(modal => {
            closeModal(modal.id);
        });
    }

    // Close modal on backdrop click
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-backdrop')) {
            closeAllModals();
        }
    });

    // Close modal on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });

    // ==================== API HELPERS ====================

    async function apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || 'Request failed');
        }

        if (response.status === 204) {
            return null;
        }

        return response.json();
    }

    // ==================== PERSON FORM ====================

    function resetPersonForm() {
        const form = document.getElementById('person-form');
        if (form) {
            form.reset();
            form.dataset.editId = '';
            
            // Reset date fields to empty
            document.getElementById('birth_approx').checked = false;
            document.getElementById('death_approx').checked = false;
            
            // Reset photo preview
            const preview = document.getElementById('photo-preview');
            if (preview) preview.style.display = 'none';
            const previewImg = document.getElementById('photo-preview-img');
            if (previewImg) previewImg.src = '';
        }
    }

    function setupPhotoPreview() {
        const fileInput = document.getElementById('photo_file');
        if (!fileInput) return;
        
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Validate file size (10 MB max)
            if (file.size > 10 * 1024 * 1024) {
                showNotification('Файл слишком большой. Максимум 10 МБ', 'error');
                fileInput.value = '';
                return;
            }
            
            // Validate file type
            if (!file.type.startsWith('image/')) {
                showNotification('Можно загружать только изображения', 'error');
                fileInput.value = '';
                return;
            }
            
            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.getElementById('photo-preview');
                const previewImg = document.getElementById('photo-preview-img');
                if (preview && previewImg) {
                    previewImg.src = e.target.result;
                    preview.style.display = 'flex';
                }
            };
            reader.readAsDataURL(file);
        });
    }

    function removePhotoPreview() {
        const fileInput = document.getElementById('photo_file');
        const preview = document.getElementById('photo-preview');
        const previewImg = document.getElementById('photo-preview-img');
        
        if (fileInput) fileInput.value = '';
        if (preview) preview.style.display = 'none';
        if (previewImg) previewImg.src = '';
    }

    async function uploadPhoto(personId) {
        const fileInput = document.getElementById('photo_file');
        const file = fileInput?.files[0];
        
        if (!file) return;
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('person_id', personId);
            
            const response = await fetch(`/api/v1/photos/upload?person_id=${personId}`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
                throw new Error(error.detail || 'Upload failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Photo upload error:', error);
            throw error;
        }
    }

    function fillPersonForm(person) {
        resetPersonForm();
        
        const form = document.getElementById('person-form');
        form.dataset.editId = person.id;
        
        // Basic fields
        document.getElementById('first_name').value = person.first_name || '';
        document.getElementById('last_name').value = person.last_name || '';
        document.getElementById('middle_name').value = person.middle_name || '';
        document.getElementById('maiden_name').value = person.maiden_name || '';
        
        // Gender
        if (person.gender) {
            document.querySelector(`input[name="gender"][value="${person.gender}"]`).checked = true;
        }
        
        // Birth date
        if (person.birth_year) document.getElementById('birth_year').value = person.birth_year;
        if (person.birth_month) document.getElementById('birth_month').value = person.birth_month;
        if (person.birth_day) document.getElementById('birth_day').value = person.birth_day;
        document.getElementById('birth_approx').checked = person.birth_approx || false;
        
        // Death date
        if (person.death_year) document.getElementById('death_year').value = person.death_year;
        if (person.death_month) document.getElementById('death_month').value = person.death_month;
        if (person.death_day) document.getElementById('death_day').value = person.death_day;
        document.getElementById('death_approx').checked = person.death_approx || false;
        
        // Places
        document.getElementById('place_of_birth').value = person.place_of_birth || '';
        document.getElementById('place_of_death').value = person.place_of_death || '';
        document.getElementById('burial_place').value = person.burial_place || '';
        
        // Death cause
        if (person.death_cause) {
            document.getElementById('death_cause').value = person.death_cause;
        }
        
        // Biography and archive
        document.getElementById('biography').value = person.biography || '';
        document.getElementById('archive_records').value = person.archive_records || '';
    }

    async function submitPersonForm(e) {
        e.preventDefault();
        
        const form = document.getElementById('person-form');
        const editId = form.dataset.editId;
        const url = editId 
            ? `/api/v1/persons/${editId}`
            : '/api/v1/persons';
        
        const method = editId ? 'PUT' : 'POST';
        
        // Collect form data
        const data = {
            first_name: document.getElementById('first_name').value.trim(),
            last_name: document.getElementById('last_name').value.trim(),
            middle_name: document.getElementById('middle_name').value.trim() || null,
            maiden_name: document.getElementById('maiden_name').value.trim() || null,
            gender: document.querySelector('input[name="gender"]:checked')?.value,
            birth_year: document.getElementById('birth_year').value ? parseInt(document.getElementById('birth_year').value) : null,
            birth_month: document.getElementById('birth_month').value ? parseInt(document.getElementById('birth_month').value) : null,
            birth_day: document.getElementById('birth_day').value ? parseInt(document.getElementById('birth_day').value) : null,
            birth_approx: document.getElementById('birth_approx').checked,
            death_year: document.getElementById('death_year').value ? parseInt(document.getElementById('death_year').value) : null,
            death_month: document.getElementById('death_month').value ? parseInt(document.getElementById('death_month').value) : null,
            death_day: document.getElementById('death_day').value ? parseInt(document.getElementById('death_day').value) : null,
            death_approx: document.getElementById('death_approx').checked,
            place_of_birth: document.getElementById('place_of_birth').value.trim() || null,
            place_of_death: document.getElementById('place_of_death').value.trim() || null,
            burial_place: document.getElementById('burial_place').value.trim() || null,
            death_cause: document.getElementById('death_cause').value || null,
            biography: document.getElementById('biography').value.trim() || null,
            archive_records: document.getElementById('archive_records').value.trim() || null,
        };
        
        // Validate required fields
        if (!data.first_name || !data.last_name || !data.gender) {
            showNotification('Заполните обязательные поля: имя, фамилия и пол', 'error');
            return;
        }
        
        try {
            showLoading(true);
            const result = await apiRequest(url, {
                method: method,
                body: JSON.stringify(data)
            });
            
            const personId = result.id || editId;
            
            // Upload photo if selected
            if (personId) {
                try {
                    await uploadPhoto(personId);
                } catch (photoError) {
                    console.warn('Photo upload failed:', photoError);
                    // Don't fail the whole operation if photo upload fails
                }
            }
            
            showNotification(editId ? 'Персона обновлена' : 'Персона добавлена', 'success');
            closeAllModals();
            resetPersonForm();
            reloadPersonsList();
            
        } catch (error) {
            showNotification('Ошибка: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }

    async function deletePerson(personId, personName) {
        if (!confirm(`Удалить персону "${personName}"? Это действие нельзя отменить.`)) {
            return;
        }
        
        try {
            showLoading(true);
            await apiRequest(`/api/v1/persons/${personId}`, {
                method: 'DELETE'
            });
            
            showNotification('Персона удалена', 'success');
            reloadPersonsList();
            
        } catch (error) {
            showNotification('Ошибка удаления: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }

    // ==================== UI HELPERS ====================

    function showNotification(message, type = 'info') {
        // Remove existing notification
        const existing = document.querySelector('.notification');
        if (existing) {
            existing.remove();
        }
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            max-width: 400px;
        `;
        
        if (type === 'success') {
            notification.style.background = '#10b981';
        } else if (type === 'error') {
            notification.style.background = '#ef4444';
        } else {
            notification.style.background = '#3b82f6';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(400px)';
            notification.style.transition = 'all 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    function showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }

    async function reloadPersonsList() {
        const container = document.querySelector('.person-list');
        if (!container) return;
        
        try {
            const persons = await apiRequest('/api/v1/persons/');
            
            // Create a map of new persons for quick lookup
            const newPersonsMap = new Map();
            persons.forEach(p => newPersonsMap.set(p.id, p));
            
            // Get existing person cards
            const existingCards = container.querySelectorAll('.person-card');
            const existingIds = new Set();
            existingCards.forEach(card => existingIds.add(parseInt(card.dataset.personId)));
            
            // Find persons to remove (exist but not in new list)
            existingIds.forEach(id => {
                if (!newPersonsMap.has(id)) {
                    const card = container.querySelector(`[data-person-id="${id}"]`);
                    if (card) card.remove();
                }
            });
            
            // Update or add persons
            persons.forEach(person => {
                const existingCard = container.querySelector(`[data-person-id="${person.id}"]`);
                const personHtml = createPersonCard(person);
                
                if (existingCard) {
                    // Update existing card
                    const newTemp = document.createElement('div');
                    newTemp.innerHTML = personHtml;
                    const newCard = newTemp.firstElementChild;
                    
                    // Preserve position-based animations
                    if (existingCard.outerHTML !== personHtml) {
                        existingCard.replaceWith(newCard);
                    }
                } else {
                    // Add new card at the beginning
                    const temp = document.createElement('div');
                    temp.innerHTML = personHtml;
                    const newCard = temp.firstElementChild;
                    
                    // Remove empty state if exists
                    const emptyState = container.querySelector('.empty-state');
                    if (emptyState) emptyState.remove();
                    
                    container.insertBefore(newCard, container.firstChild);
                }
            });
            
            // Show empty state if no persons
            if (persons.length === 0) {
                container.innerHTML = '<p class="empty-state">Нет персон в базе данных. Нажмите "Добавить персону" чтобы начать.</p>';
            }
            
        } catch (error) {
            console.error('Error reloading persons:', error);
        }
    }
    
    function createPersonCard(person) {
        const photoUrl = person.photos && person.photos.length > 0 
            ? `/uploads/photos/persons/${person.id}/${person.photos[0].filename}`
            : '/static/img/placeholder.png';
        
        return `
            <div class="person-card" data-person-id="${person.id}">
                <div class="main-photo-wrapper">
                    <img src="${photoUrl}" alt="${person.first_name}" class="main-photo">
                </div>
                
                <h3>${person.last_name} ${person.first_name}${person.middle_name ? ' ' + person.middle_name : ''}${person.maiden_name ? ' (дев. ' + person.maiden_name + ')' : ''}</h3>
                <p class="person-meta">
                    ${person.birth_year 
                        ? (person.birth_approx ? 'ок. ' : '') + person.birth_year + ' г.' 
                        : 'Год рождения: неизвестен'}
                    ${person.death_year ? ' — ' + (person.death_approx ? 'ок. ' : '') + person.death_year + ' г.' : ''}
                </p>
                ${person.place_of_birth ? '<p class="person-meta">Место рождения: ' + person.place_of_birth + '</p>' : ''}
                ${person.biography ? '<p class="person-notes">' + person.biography.substring(0, 200) + (person.biography.length > 200 ? '...' : '') + '</p>' : ''}
                
                <div class="person-actions">
                    <button class="btn btn-sm btn-primary" onclick="FamilyTree.editPerson(${person.id})">
                        ✏️ Редактировать
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="FamilyTree.deletePerson(${person.id}, '${person.last_name} ${person.first_name}')">
                        🗑️ Удалить
                    </button>
                </div>
            </div>
        `;
    }

    // ==================== EVENT LISTENERS ====================

    document.addEventListener('DOMContentLoaded', function() {
        // Open modal buttons
        document.querySelectorAll('[data-open-modal]').forEach(button => {
            button.addEventListener('click', function() {
                const modalId = this.dataset.openModal;
                openModal(modalId);
            });
        });
        
        // Person form submit
        const personForm = document.getElementById('person-form');
        if (personForm) {
            personForm.addEventListener('submit', submitPersonForm);
        }
        
        // Setup photo preview
        setupPhotoPreview();
        
        // Surname form submit
        const surnameForm = document.getElementById('surname-form');
        if (surnameForm) {
            surnameForm.addEventListener('submit', submitSurnameForm);
        }
        
        // If on a page with person list, ensure it's loaded
        const personList = document.querySelector('.person-list');
        if (personList && personList.children.length === 0) {
            reloadPersonsList();
        }
    });
    
    async function submitSurnameForm(e) {
        e.preventDefault();
        
        const form = document.getElementById('surname-form');
        const surname = document.getElementById('surname_name').value.trim();
        const note = document.getElementById('surname_note').value.trim() || null;
        
        if (!surname) {
            showNotification('Введите фамилию', 'error');
            return;
        }
        
        try {
            showLoading(true);
            
            // Check if surname already exists
            const existingPersons = await apiRequest('/api/v1/persons/');
            const surnameExists = existingPersons.some(p => 
                p.last_name.toLowerCase() === surname.toLowerCase()
            );
            
            if (surnameExists) {
                showNotification(
                    `Фамилия "${surname}" уже существует в базе. Персоны с этой фамилией появятся автоматически при добавлении.`, 
                    'info'
                );
            } else {
                // Create a placeholder person to establish the surname category
                // We'll create a minimal person and then let user edit it
                showNotification(
                    `Категория "${surname}" будет создана при добавлении первой персоны с этой фамилией.`, 
                    'success'
                );
            }
            
            closeAllModals();
            form.reset();
            
        } catch (error) {
            showNotification('Ошибка: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }

    // ==================== GLOBAL API ====================
    
    window.FamilyTree = {
        openModal,
        closeModal,
        closeAllModals,
        editPerson: function(personId) {
            apiRequest(`/api/v1/persons/${personId}`)
                .then(person => {
                    fillPersonForm(person);
                    openModal('modal-person');
                })
                .catch(error => {
                    showNotification('Ошибка загрузки данных: ' + error.message, 'error');
                });
        },
        deletePerson,
        reloadPersonsList,
        showNotification,
        showLoading,
        removePhotoPreview
    };

    // Expose submitSurnameForm globally
    window.submitSurnameForm = submitSurnameForm;

})();
