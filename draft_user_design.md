# Draft User and System Design: News for Kids

**Product Name:** News for Kids. Read-Learn-Think

This document outlines the proposed user roles, permissions, and features for the "News for Kids" platform. The system is designed to provide age-appropriate news content and learning tools, with different levels of access for unregistered visitors, registered members, and administrators.

---

## 1. User Tiers and Permissions

The platform will support three distinct user roles:

### 1.1. Normal User (Unregistered / Guest)

This is the default role for any first-time visitor. The experience is limited to browsing and sampling content to encourage registration.

**Permissions & Features:**
*   **View Portal Page:** Can only access the main portal/homepage.
*   **Content View:** All articles displayed on the portal page are presented at the **medium (mid) difficulty level** by default.
*   **No Customization:** Cannot change language, difficulty level, or access practice pages.
*   **Call to Action:** The interface will prominently feature prompts to register for a free account to unlock more features.

### 1.2. Registered User (Logged In)

Users who have created a free account unlock personalization, learning tools, and delivery options.

**Permissions & Features:**
*   **Full Article Access:** Can access all articles, not just the portal page.
*   **Customized Article View:** When viewing an article, the user can switch between different styles and difficulties:
    *   **Easy:** Simplified summary for younger readers.
    *   **Mid:** Standard, medium-difficulty summary.
    *   **Hard:** Advanced summary with more complex vocabulary.
    *   **CN (Chinese):** A translated version of the article.
*   **Article Practice Page:** Each article will have an associated "practice page" containing:
    *   Vocabulary lists.
    *   Comprehension questions (multiple choice).
    *   Key points and summaries.
*   **Subscription Service:** Users can manage their subscriptions to receive daily or weekly digests:
    *   **Email Delivery:** Articles sent directly to their inbox.
    *   **Send to Kindle:** Integration to deliver articles to a user's Kindle device.
*   **User Profile:** Can manage their email, password, and subscription preferences.

### 1.3. Admin User

This role is for internal staff who manage the platform's content, users, and configuration. It includes all registered user features plus a dedicated admin dashboard.

**Permissions & Features:**
*   **Includes All Registered User Features.**
*   **Admin Dashboard:** A secure, separate interface for managing the platform, broken down into several key areas:

    *   #### Content Management
        *   **Article Oversight:** View, search, and filter all articles in the database.
        *   **Manual AI Trigger:** Select an article and manually trigger the AI analysis/summary generation process.
        *   **Content Moderation:** Edit or delete articles, summaries, and associated images.
        *   **Curation:** Feature or hide specific articles on the main portal page.

    *   #### User Management
        *   **View Users:** List and search all registered users.
        *   **Account Administration:** Reset user passwords or manage user roles (e.g., promote a user to Admin).
        *   **Delete Users:** Remove user accounts.

    *   #### Pipeline & Feed Configuration
        *   **Feed Management:** An interface to manage the `feeds` table directly.
            *   **Add/Edit/Delete Feeds:** Create, update, or remove RSS feeds.
            *   **Enable/Disable:** A toggle switch for each feed's `enable` status, controlling whether it's included in the next mining run.
        *   **Category Management:** An interface for the `categories` table.
            *   **Add/Edit/Delete Categories:** Manage the list of available news categories.
            *   **AI Prompt Association:** For each category, specify which AI prompt template to use (e.g., 'science', 'tech', 'default').
        *   **Mining Schedule & Throttling:**
            *   **Schedule:** A UI to modify the cron job or scheduled task that runs the `daily_pipeline.sh`, effectively changing the mining frequency (e.g., "Run every 4 hours").
            *   **Articles per Source:** A number input to configure `num_per_source` (how many articles to successfully process from each feed per run).
            *   **Max Fetch per Feed:** A number input for `max_fetch_per_feed` (the maximum number of items to check from a feed's RSS before moving on).

    *   #### System & Security Configuration
        *   **API Keys:**
            *   A secure, write-only input field to update the `DEEPSEEK_API_KEY`. The key will be stored in a secure backend location (like a `.env` file) and will never be displayed in the UI.
        *   **Content Filtering Rules:**
            *   **Content Length:** Set the minimum and maximum character counts for an article to be considered for processing.
        *   **System Logs & Maintenance:**
            *   **View Logs:** A log viewer to display output from the pipeline runs (e.g., from `run_mining_apply.nohup.out`).
            *   **Maintenance Tasks:** Buttons to trigger maintenance scripts, such as cleaning up old database backups or temporary files.

---

## 2. System Flow & Architecture Notes

*   **Frontend:** The user interface will need to be dynamic. When a user selects a difficulty level (Easy, Mid, Hard, CN), the frontend will fetch the corresponding summary from the `article_summaries` table for that article ID and difficulty level.
*   **Backend:** The API server will need endpoints to support these roles. For example, `/api/article/{id}` might return different data based on the user's authentication status and role. Admin-specific endpoints (`/api/admin/*`) will require admin-level authentication.
*   **Database:** The existing database schema (`users`, `user_preferences`, `article_summaries`, `feeds`) supports these roles, but may need additional tables or columns for features like Kindle integration settings or admin action logging.
*   **Authentication:** A standard token-based authentication system (e.g., JWT) should be implemented to manage user sessions and secure API endpoints.
