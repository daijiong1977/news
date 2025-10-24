# Email Newsletter Design Specification — Two-Feature Model

This specification describes the structure and content of the personalized email newsletter. The goal is to deliver high-value, age-appropriate content in-email while driving users back to the static site for interactive practice pages and archives.

## Goal

- Deliver two featured articles per email (each ~500–700 words, adapted to the user's reading level).
- Provide a curated navigation section with additional articles (six links total).
- Encourage interaction by linking to practice/quiz pages on the static site.

---

## 1. Global Parameters & Personalization

- **Delivery model:** Daily (or scheduled cadence such as twice daily) via an ESP (e.g., Buttondown).
- **Article content:** Full text for the two featured stories (≈500–700 words each).
- **Level targeting:** Show content adapted to the user's selected reading level (easy / mid / hard / cn, or labeled as Grade X).
- **Image source:** Optimized images produced by the backend (web and thumbnail variants). The email references hosted images (no embedded base64).
- **Mobile optimization:** Single-column layout; large type, clear buttons; images use `max-width:100%` and responsive markup.

---

## 2. Email Structure (Top → Bottom)

### A. Header & Branding

- **Logo / Title:** Prominent brand identity (e.g., "NEWS FOR KIDS").
- **Greeting:** Personalized line that includes the user's reading level (for example: "Here is your news for the day, Grade 5 reader!").
- **Links:** Clear unsubscribe link (top + bottom) and a link to user preferences.

### B. Feature 1 — Primary News Story (High priority)

This block contains the most important article (drawn from the primary category such as News).

- **Visual block:** Distinct background or subtle card to separate it from the rest.
- **Title:** Large, bold headline.
- **Level badge:** Small badge showing the reading level (e.g., Grade 5).
- **Image:** Full-width (max 600px) optimized image using the hosted `image_web_url`.
- **Article body:** Full simplified text (500–700 words) adapted to the user's level.
- **Primary CTAs:**
	- `Start the Quiz 🧠` — primary high-contrast button linking to `/practice/{slug}`
	- `Read Full Article 📚` — secondary button linking to `/articles/{slug}`

### C. Feature 2 — Secondary Catalog Story

This follows the same structure as Feature 1 but is visually separated (e.g., white background). It comes from a secondary category (Science, Tech, etc.).

### D. Navigation Menu — Additional Links

List the two next-latest articles from each of three categories (6 links total). This is a compact link list with small thumbnails and short titles.

**Example layout:**

- **More Stories to Explore on the Site**
	- **News**
		- Title 3 — link to `/articles/{slug}`
		- Title 4 — link to `/articles/{slug}`
	- **Science**
		- Title 3 — link to `/articles/{slug}`
		- Title 4 — link to `/articles/{slug}`
	- **Sports**
		- Title 1 — link to `/articles/{slug}`
		- Title 2 — link to `/articles/{slug}`

### E. Footer

- Standard unsubscribe link, privacy policy, and brand logo.
- Minimal contact info and links to preferences / manage subscription.

---

## 3. Design & Styling Guidance

- **Width:** Design for a 600px email content width; use fluid images with `max-width:100%`.
- **Typography:** Legible font sizes (body 16px desktop baseline; scale for mobile).
- **Buttons:** Use accessible contrast and generous tappable areas on mobile.
- **Accessibility:** Include descriptive `alt` text for all images; use semantic headings.

---

## 4. Image Handling (Backend responsibilities)

1. **Download** original image from the source article.
2. **Generate two variants:**
	 - `web` (max width 1200px, JPEG, quality ~80) for article pages and large displays.
	 - `thumb` (e.g., 200px wide) for list views and the navigation menu in email.
3. **Optimize** images (strip metadata, progressive JPEG where useful).
4. **Host** images on your CDN or public site path and use absolute URLs in email and JSON (`image_web_url`, `image_thumb_url`).

---

## 5. Email Template Data Bindings (from Article JSON)

- `{{title}}` — Article headline
- `{{level}}` — Level badge text (easy/mid/hard/cn or Grade)
- `{{image_web_url}}` — full image URL
- `{{image_thumb_url}}` — thumbnail URL
- `{{body}}` — simplified article text
- `{{quiz_url}}` — `/practice/{slug}`
- `{{article_url}}` — `/articles/{slug}`

---

## 6. Example HTML Snippet (simplified)

```html
<table width="100%" cellpadding="0" cellspacing="0" role="presentation">
	<tr>
		<td align="center">
			<table width="600" cellpadding="0" cellspacing="0" role="presentation">
				<tr>
					<td>
						<h1>NEWS FOR KIDS</h1>
						<p>Here is your news for the day, Grade 5 reader!</p>
						<img src="{{image_web_url}}" alt="{{title}}" width="600" style="max-width:100%; height:auto; display:block;">
						<h2>{{title}}</h2>
						<p>{{body}}</p>
						<a href="{{quiz_url}}" style="display:inline-block; padding:12px 18px; background:#ff6f61; color:#fff; text-decoration:none;">Start the Quiz</a>
					</td>
				</tr>
			</table>
		</td>
	</tr>
</table>
```

---

## 7. Deliverability & Best Practices

- **Keep email size small:** Reference hosted images (do not embed). Try to keep the total message body under 200–300 KB.
- **Include unsubscribe header and visible link:** Required for deliverability and compliance.
- **Use a verified sending domain and DKIM/SPF records:** Configure DNS for the ESP (Buttondown will guide you).

---

## 8. Testing Checklist

- Render tests in major clients (Gmail web, Gmail mobile, Apple Mail, Outlook desktop, Outlook web).
- Verify images load from CDN and that `alt` text appears correctly when images are blocked.
- Accessibility check: semantic headings, color contrast, button sizes.

---

## 9. Notes & Next Steps

- Create a small set of template variants (Design A and Design B) and perform A/B testing for engagement.
- Wire up the article JSON → email rendering pipeline and test with a single internal subscriber before sending to real users.
