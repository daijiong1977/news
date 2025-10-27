/**
 * User Manager - Frontend Client
 * Handles user registration, stats tracking, and sync with server API
 * API: https://news.6ray.com/api/
 */

class UserManager {
    constructor() {
        this.apiBase = 'https://news.6ray.com/api';
        this.userId = null;
        this.userToken = null;
        this.userName = null;
        this.readingStyle = null;
        this.deviceId = null;
        this.stats = {};
        
        this.init();
    }
    
    /**
     * Initialize user manager
     */
    async init() {
        try {
            console.log('📊 Loading user data...');
            // Load user data from localStorage
            this.loadUserData();
            this.loadStats();
            
            console.log('🔑 Ensuring device_id...');
            // Get or generate device_id (for anonymous tracking)
            await this.ensureDeviceId();
            
            console.log('✉️ Checking verification status...');
            // Check if user is verified (from email link)
            this.checkVerificationStatus();
            
            console.log('🎨 Initializing UI...');
            // Initialize UI
            this.initializeUI();
        } catch (error) {
            console.error('❌ Error in init():', error);
        }
    }
    
    /**
     * Ensure device_id exists (generate if needed)
     * This works for both anonymous and registered users
     */
    async ensureDeviceId() {
        this.deviceId = localStorage.getItem('news_device_id');
        
        if (!this.deviceId) {
            try {
                const response = await fetch(`${this.apiBase}/device/generate`);
                const data = await response.json();
                
                if (data.success && data.device_id) {
                    this.deviceId = data.device_id;
                    localStorage.setItem('news_device_id', this.deviceId);
                    console.log('Generated new device_id:', this.deviceId);
                }
            } catch (error) {
                // Fallback: generate locally if API fails
                this.deviceId = `news-local-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                localStorage.setItem('news_device_id', this.deviceId);
                console.warn('Failed to get device_id from API, using local fallback');
            }
        }
    }
    
    /**
     * Load user data from localStorage
     */
    loadUserData() {
        this.userId = localStorage.getItem('news_user_id');
        this.userToken = localStorage.getItem('news_user_token');
        this.userName = localStorage.getItem('news_user_name');
        this.readingStyle = localStorage.getItem('news_reading_style') || 'enjoy';
        this.deviceId = localStorage.getItem('news_device_id');
    }
    
    /**
     * Save user data to localStorage
     */
    saveUserData() {
        if (this.userId) localStorage.setItem('news_user_id', this.userId);
        if (this.userToken) localStorage.setItem('news_user_token', this.userToken);
        if (this.userName) localStorage.setItem('news_user_name', this.userName);
        if (this.readingStyle) localStorage.setItem('news_reading_style', this.readingStyle);
    }
    
    /**
     * Load stats from localStorage
     */
    loadStats() {
        const statsJson = localStorage.getItem('news_stats');
        this.stats = statsJson ? JSON.parse(statsJson) : {};
    }
    
    /**
     * Save stats to localStorage
     */
    saveStats() {
        localStorage.setItem('news_stats', JSON.stringify(this.stats));
    }
    
    /**
     * Check if user arrived from email verification link
     */
    checkVerificationStatus() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('verified') === 'true') {
            this.showMessage('✅ Email verified! You can now receive newsletters.', 'success');
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }
    
    /**
     * Check if user is registered
     */
    isRegistered() {
        return !!(this.userId && this.userToken);
    }
    
    /**
     * Initialize UI elements
     */
    initializeUI() {
        try {
            console.log('📱 Initializing UI...');
            
            // Create registration modal
            this.createRegistrationModal();
            console.log('✅ Modal created');
            
            // Create sync button (if registered)
            if (this.isRegistered()) {
                console.log('👤 User is registered, creating sync button');
                this.createSyncButton();
            } else {
                console.log('👤 User not registered, creating register button');
                this.createRegisterButton();
            }
            
            // Create user info display
            this.updateUserInfo();
            console.log('✅ UI initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing UI:', error);
        }
    }
    
    /**
     * Create registration modal HTML
     */
    createRegistrationModal() {
        try {
            console.log('📋 Creating registration modal...');
            const modalHtml = `
            <div id="user-registration-modal" class="user-modal" style="display: none;">
                <div class="user-modal-content">
                    <span class="user-modal-close">&times;</span>
                    <h2>📧 Subscribe to Newsletter</h2>
                    <p>Get curated articles delivered to your inbox based on your reading preference!</p>
                    
                    <form id="registration-form">
                        <div class="form-group">
                            <label for="user-name">Name:</label>
                            <input type="text" id="user-name" name="name" required placeholder="Your name">
                        </div>
                        
                        <div class="form-group">
                            <label for="user-email">Email:</label>
                            <input type="email" id="user-email" name="email" required placeholder="your@email.com">
                        </div>
                        
                        <div class="form-group">
                            <label for="reading-style">Reading Style:</label>
                            <select id="reading-style" name="reading_style" required>
                                <option value="relax">Relax - Easy reading</option>
                                <option value="enjoy" selected>Enjoy - Balanced</option>
                                <option value="research">Research - Deep dive</option>
                                <option value="chinese">Chinese - 中文翻译</option>
                            </select>
                        </div>
                        
                        <div id="registration-message" class="message"></div>
                        
                        <button type="submit" class="btn-primary">Subscribe</button>
                    </form>
                    
                    <div class="modal-footer">
                        <p><small>Already registered? <a href="#" id="token-recovery-link">Recover your token</a></small></p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add event listeners
        document.querySelector('.user-modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('registration-form').addEventListener('submit', (e) => this.handleRegistration(e));
        document.getElementById('token-recovery-link').addEventListener('click', (e) => {
            e.preventDefault();
            this.showTokenRecovery();
        });
    }
    
    /**
     * Create register button
     */
    createRegisterButton() {
        const button = document.createElement('button');
        button.id = 'register-button';
        button.className = 'user-register-btn';
        button.innerHTML = '📧';
        button.title = 'Subscribe to Newsletter';
        button.addEventListener('click', () => this.openModal());
        
        // Add to body as floating action button
        document.body.appendChild(button);
        console.log('✅ Register button created');
    }
    
    /**
     * Create sync button (for registered users)
     */
    createSyncButton() {
        const button = document.createElement('button');
        button.id = 'sync-button';
        button.className = 'user-sync-btn';
        button.innerHTML = '🔄';
        button.title = 'Sync your activity to cloud';
        button.addEventListener('click', () => this.syncStats());
        
        // Add to body as floating action button
        document.body.appendChild(button);
        console.log('✅ Sync button created');
    }
    
    /**
     * Update user info display
     */
    updateUserInfo() {
        if (this.isRegistered()) {
            const infoHtml = `
                <div class="user-info">
                    <span>👤 ${this.userName}</span>
                    <span class="reading-style-badge">${this.readingStyle}</span>
                </div>
            `;
            
            const header = document.querySelector('header') || document.body;
            const existingInfo = document.querySelector('.user-info');
            if (existingInfo) {
                existingInfo.remove();
            }
            header.insertAdjacentHTML('beforeend', infoHtml);
        }
    }
    
    /**
     * Open registration modal
     */
    openModal() {
        document.getElementById('user-registration-modal').style.display = 'flex';
    }
    
    /**
     * Close registration modal
     */
    closeModal() {
        document.getElementById('user-registration-modal').style.display = 'none';
    }
    
    /**
     * Handle registration form submission
     */
    async handleRegistration(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = {
            name: form.name.value.trim(),
            email: form.email.value.trim(),
            reading_style: form.reading_style.value
        };
        
        // Show loading
        this.showMessage('⏳ Registering...', 'info');
        
        try {
            const response = await fetch(`${this.apiBase}/user/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Save user data
                this.userId = data.user_id;
                this.userToken = data.bootstrap_token;
                this.userName = formData.name;
                this.readingStyle = formData.reading_style;
                this.saveUserData();
                
                // Show success message
                let message = '✅ Registration successful! Check your email to verify.';
                if (data.bootstrap_failed) {
                    message += '<br><small>⚠️ Email service temporarily unavailable. Your account is created but verification email will be sent later.</small>';
                }
                this.showMessage(message, 'success');
                
                // Update UI
                setTimeout(() => {
                    this.closeModal();
                    location.reload(); // Refresh to show sync button
                }, 3000);
            } else {
                this.showMessage(`❌ Error: ${data.error || 'Registration failed'}`, 'error');
            }
        } catch (error) {
            this.showMessage(`❌ Network error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Show token recovery dialog
     */
    showTokenRecovery() {
        const email = prompt('Enter your email address to recover your token:');
        if (!email) return;
        
        this.recoverToken(email);
    }
    
    /**
     * Recover token by email
     */
    async recoverToken(email) {
        try {
            const response = await fetch(`${this.apiBase}/user/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Save recovered data
                this.userId = data.user_id;
                this.userToken = data.bootstrap_token;
                this.userName = data.name;
                this.readingStyle = data.reading_style;
                this.saveUserData();
                
                alert(`✅ Token recovered!\n\nName: ${data.name}\nReading Style: ${data.reading_style}\n\nPage will reload.`);
                location.reload();
            } else {
                alert(`❌ Error: ${data.error || 'Token recovery failed'}`);
            }
        } catch (error) {
            alert(`❌ Network error: ${error.message}`);
        }
    }
    
    /**
     * Sync stats to server
     */
    async syncStats() {
        if (!this.isRegistered()) {
            alert('Please register first to sync your activity.');
            return;
        }
        
        const button = document.getElementById('sync-button');
        const originalText = button.innerHTML;
        button.innerHTML = '⏳ Syncing...';
        button.disabled = true;
        
        try {
            const response = await fetch(`${this.apiBase}/user/sync-stats`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Token': this.userToken
                },
                body: JSON.stringify({
                    stats: this.stats
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                button.innerHTML = '✅ Synced!';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            } else {
                alert(`❌ Sync failed: ${data.error || 'Unknown error'}`);
                button.innerHTML = originalText;
                button.disabled = false;
            }
        } catch (error) {
            alert(`❌ Network error: ${error.message}`);
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    /**
     * Track word completion
     */
    trackWordCompletion(articleId, wordId) {
        const key = `word_${articleId}_${wordId}`;
        this.stats[key] = {
            completed: true,
            timestamp: Date.now()
        };
        this.saveStats();
    }
    
    /**
     * Track quiz completion
     */
    trackQuizCompletion(articleId, score, total) {
        const key = `quiz_${articleId}`;
        this.stats[key] = {
            score: score,
            total: total,
            percentage: Math.round((score / total) * 100),
            timestamp: Date.now()
        };
        this.saveStats();
    }
    
    /**
     * Track article read
     */
    trackArticleRead(articleId) {
        const key = `read_${articleId}`;
        this.stats[key] = {
            read: true,
            timestamp: Date.now()
        };
        this.saveStats();
    }
    
    /**
     * Get user stats summary
     */
    getStatsSummary() {
        const wordsCompleted = Object.keys(this.stats).filter(k => k.startsWith('word_')).length;
        const quizzesCompleted = Object.keys(this.stats).filter(k => k.startsWith('quiz_')).length;
        const articlesRead = Object.keys(this.stats).filter(k => k.startsWith('read_')).length;
        
        return {
            wordsCompleted,
            quizzesCompleted,
            articlesRead
        };
    }
    
    /**
     * Show message in registration modal
     */
    showMessage(message, type) {
        const messageEl = document.getElementById('registration-message');
        if (messageEl) {
            messageEl.innerHTML = message;
            messageEl.className = `message message-${type}`;
            messageEl.style.display = 'block';
        } else {
            // Fallback to alert if not in modal
            if (type === 'error') {
                alert(message.replace(/<[^>]*>/g, '')); // Strip HTML
            }
        }
    }
}

// Initialize user manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🚀 Initializing UserManager...');
        window.userManager = new UserManager();
    });
} else {
    console.log('🚀 Initializing UserManager (DOM already loaded)...');
    window.userManager = new UserManager();
}
